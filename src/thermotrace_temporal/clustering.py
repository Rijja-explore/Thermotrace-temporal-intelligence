"""
clustering.py – Thermal event clustering using DBSCAN.

Converts individual observations into discrete thermal events by clustering
on both spatial distance (Haversine) and temporal proximity.

Design notes:
- DBSCAN is used for transparency and explainability.
- Observations are NOT clustered solely on geographic distance.
  Two observations at the same location but months apart will NOT
  be assigned to the same event.
- All parameters are configurable via config/thresholds.yaml.
- Noise points (cluster_id == -1) are treated as singleton events.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from .config_loader import Config, get_config
from .schemas import Observation, ThermalEvent

logger = logging.getLogger(__name__)

# Earth radius for Haversine
_EARTH_RADIUS_KM = 6371.0


def _haversine_matrix(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Haversine distance matrix (km) for arrays of lat/lon.
    Returns a symmetric (n, n) matrix.
    """
    lat_r = np.radians(lats)
    lon_r = np.radians(lons)
    dlat = lat_r[:, None] - lat_r[None, :]
    dlon = lon_r[:, None] - lon_r[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat_r[:, None]) * np.cos(lat_r[None, :]) * np.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _temporal_distance_matrix(timestamps: np.ndarray) -> np.ndarray:
    """
    Compute pairwise absolute temporal distance matrix in hours.
    timestamps: array of datetime objects
    """
    ts_seconds = np.array(
        [t.timestamp() if hasattr(t, "timestamp") else float(t) for t in timestamps],
        dtype=float,
    )
    diff_seconds = np.abs(ts_seconds[:, None] - ts_seconds[None, :])
    return diff_seconds / 3600.0


def _combined_distance_matrix(
    spatial_km: np.ndarray,
    temporal_hours: np.ndarray,
    spatial_radius_km: float,
    temporal_window_hours: float,
) -> np.ndarray:
    """
    Combine spatial and temporal distances into a single normalised distance.

    Two observations are considered "close" (distance ≤ 1.0) when:
      - spatial distance ≤ spatial_radius_km  AND
      - temporal distance ≤ temporal_window_hours

    We normalise each component to [0, 1] relative to its threshold, then
    take the maximum (Chebyshev-style) so BOTH conditions must be met.
    This avoids the need for a single arbitrary combined metric.
    """
    spatial_norm = spatial_km / max(spatial_radius_km, 1e-9)
    temporal_norm = temporal_hours / max(temporal_window_hours, 1e-9)
    return np.maximum(spatial_norm, temporal_norm)


def cluster_observations(
    observations: list[Observation],
    config: Optional[Config] = None,
) -> list[ThermalEvent]:
    """
    Cluster observations into thermal events using DBSCAN.

    Parameters
    ----------
    observations : list[Observation]
        Validated input observations (may be empty).
    config : Config, optional
        Configuration object. Defaults to the global config.

    Returns
    -------
    list[ThermalEvent]
        One ThermalEvent per discovered cluster.
        Noise points (DBSCAN label -1) are promoted to singleton events.
    """
    cfg = config or get_config()

    spatial_radius_km: float = cfg.get_threshold("clustering", "spatial_radius_km", default=2.0)
    temporal_window_hours: float = cfg.get_threshold("clustering", "temporal_window_hours", default=24.0)
    min_samples: int = cfg.get_threshold("clustering", "min_samples", default=1)

    logger.info("Clustering %d observations (spatial=%.1f km, temporal=%.1f h)",
                len(observations), spatial_radius_km, temporal_window_hours)

    if not observations:
        logger.warning("No observations provided for clustering.")
        return []

    # -----------------------------------------------------------------------
    # Build DataFrame for efficient processing
    # -----------------------------------------------------------------------
    records = []
    for obs in observations:
        records.append({
            "observation_id": obs.observation_id,
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "timestamp": obs.timestamp_utc,
            "frp": obs.frp,
            "confidence": obs.confidence,
            "satellite": obs.satellite or "UNKNOWN",
            "sensor": obs.sensor or "UNKNOWN",
            "facility_id": obs.facility_id,
            "facility_type": obs.facility_type,
            "facility_distance_km": obs.facility_distance_km,
            "landcover_class": obs.landcover_class,
        })
    df = pd.DataFrame(records)

    n = len(df)
    logger.debug("Building %d×%d distance matrices", n, n)

    lats = df["latitude"].values
    lons = df["longitude"].values
    timestamps = df["timestamp"].values

    # Convert numpy datetime64 → Python datetime if needed
    parsed_timestamps = []
    for t in timestamps:
        if isinstance(t, np.datetime64):
            parsed_timestamps.append(pd.Timestamp(t).to_pydatetime().replace(tzinfo=None))
        elif isinstance(t, datetime):
            parsed_timestamps.append(t.replace(tzinfo=None) if t.tzinfo else t)
        else:
            parsed_timestamps.append(pd.Timestamp(t).to_pydatetime().replace(tzinfo=None))

    spatial_km = _haversine_matrix(lats, lons)
    temporal_h = _temporal_distance_matrix(np.array(parsed_timestamps))
    combined = _combined_distance_matrix(spatial_km, temporal_h, spatial_radius_km, temporal_window_hours)

    # -----------------------------------------------------------------------
    # DBSCAN with precomputed combined distance matrix
    # -----------------------------------------------------------------------
    db = DBSCAN(eps=1.0, min_samples=min_samples, metric="precomputed")
    labels = db.fit_predict(combined)

    df["cluster_id"] = labels
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    logger.info("DBSCAN: %d clusters, %d noise points (promoted to singletons)", n_clusters, n_noise)

    # -----------------------------------------------------------------------
    # Build ThermalEvent objects
    # -----------------------------------------------------------------------
    events: list[ThermalEvent] = []

    # Promote noise points to unique cluster IDs
    max_label = labels.max() if len(labels) > 0 else -1
    noise_counter = max_label + 1
    adjusted_labels = labels.copy()
    for i, lbl in enumerate(labels):
        if lbl == -1:
            adjusted_labels[i] = noise_counter
            noise_counter += 1

    df["cluster_id"] = adjusted_labels

    for cluster_id in sorted(df["cluster_id"].unique()):
        mask = df["cluster_id"] == cluster_id
        grp = df[mask]

        obs_ids = grp["observation_id"].tolist()
        centroid_lat = float(grp["latitude"].mean())
        centroid_lon = float(grp["longitude"].mean())

        grp_timestamps = [
            t.replace(tzinfo=None) if hasattr(t, "tzinfo") and t.tzinfo else t
            for t in grp["timestamp"].tolist()
        ]
        start_time = min(grp_timestamps)
        end_time = max(grp_timestamps)
        duration_hours = (end_time - start_time).total_seconds() / 3600.0

        # Spatial extent: max pairwise distance within cluster
        clat = grp["latitude"].values
        clon = grp["longitude"].values
        if len(clat) > 1:
            sp = _haversine_matrix(clat, clon)
            spatial_extent_km = float(sp.max())
        else:
            spatial_extent_km = 0.0

        # FRP statistics
        frp_vals = grp["frp"].dropna().values.astype(float)
        frp_mean = float(np.mean(frp_vals)) if len(frp_vals) > 0 else None
        frp_max = float(np.max(frp_vals)) if len(frp_vals) > 0 else None
        frp_min = float(np.min(frp_vals)) if len(frp_vals) > 0 else None
        frp_std = float(np.std(frp_vals, ddof=1)) if len(frp_vals) > 1 else 0.0

        # Satellites/sensors
        satellites = grp["satellite"].dropna().unique().tolist()
        sensors = grp["sensor"].dropna().unique().tolist()

        # Facility info: use most-frequent non-null value
        facility_id = _mode_or_none(grp["facility_id"])
        facility_type = _mode_or_none(grp["facility_type"])
        facility_distance_km = (
            float(grp["facility_distance_km"].dropna().min())
            if grp["facility_distance_km"].notna().any()
            else None
        )
        landcover_class = _mode_or_none(grp["landcover_class"])

        event = ThermalEvent(
            event_id=f"TT-EVENT-{uuid.uuid4().hex[:8].upper()}",
            cluster_id=int(cluster_id),
            observation_ids=obs_ids,
            centroid_latitude=centroid_lat,
            centroid_longitude=centroid_lon,
            start_time=start_time,
            end_time=end_time,
            observation_count=len(obs_ids),
            duration_hours=duration_hours,
            spatial_extent_km=spatial_extent_km,
            frp_mean=frp_mean,
            frp_max=frp_max,
            frp_min=frp_min,
            frp_std=frp_std,
            satellites=satellites,
            sensors=sensors,
            facility_id=facility_id,
            facility_type=facility_type,
            facility_distance_km=facility_distance_km,
            landcover_class=landcover_class,
        )
        events.append(event)

    logger.info("Created %d thermal events from %d observations", len(events), n)
    return events


def _mode_or_none(series: pd.Series) -> Optional[str]:
    """Return the most frequent non-null value, or None."""
    valid = series.dropna()
    if valid.empty:
        return None
    return str(valid.mode().iloc[0])


def validate_observations(raw: list[dict]) -> tuple[list[Observation], list[dict]]:
    """
    Validate raw observation dicts, returning valid Observation objects and rejected records.

    Parameters
    ----------
    raw : list[dict]
        Raw observation dictionaries from Person 1.

    Returns
    -------
    (valid_observations, rejected_records)
    """
    valid: list[Observation] = []
    rejected: list[dict] = []

    seen_ids: set[str] = set()

    for record in raw:
        obs_id = record.get("observation_id", "MISSING_ID")
        try:
            obs = Observation.model_validate(record)
            if obs.observation_id in seen_ids:
                logger.warning("Duplicate observation_id=%s – skipping", obs.observation_id)
                rejected.append({"record": record, "reason": "duplicate observation_id"})
                continue
            seen_ids.add(obs.observation_id)
            valid.append(obs)
        except Exception as exc:
            logger.warning("Rejected observation %s: %s", obs_id, exc)
            rejected.append({"record": record, "reason": str(exc)})

    logger.info(
        "Validation: %d valid, %d rejected out of %d total",
        len(valid), len(rejected), len(raw),
    )
    return valid, rejected
