"""
temporal_features.py – Temporal feature extraction for thermal events/facilities.

Computes features across 7-day, 30-day, and 90-day windows:
- Detection counts and active days
- Persistence ratio (active_days / monitored_days)
- FRP statistics (mean, median, max, min, std, p90, p95)
- Spatial stability
- Day/night and hour-of-day distributions
- Days since last detection
- Detection frequency (detections per day)

All division-by-zero cases are handled safely.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from .config_loader import Config, get_config
from .schemas import Observation, SpatialStability, TemporalFeatures, TemporalWindow

logger = logging.getLogger(__name__)

_EARTH_RADIUS_KM = 6371.0

# Daytime: 06:00–18:00 UTC (approximate; no sun-angle correction)
_DAY_START_HOUR = 6
_DAY_END_HOUR = 18


def _haversine_point(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance (km) between two points."""
    rl = np.radians([lat1, lon1, lat2, lon2])
    dlat = rl[2] - rl[0]
    dlon = rl[3] - rl[1]
    a = np.sin(dlat / 2) ** 2 + np.cos(rl[0]) * np.cos(rl[2]) * np.sin(dlon / 2) ** 2
    return float(2 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1))))


def compute_spatial_stability(
    lats: np.ndarray,
    lons: np.ndarray,
    config: Optional[Config] = None,
) -> SpatialStability:
    """
    Compute spatial stability metrics for a set of detection points.

    Returns centroid, mean/max distance from centroid, and a normalised
    stability score (0–100; higher = more stable).
    """
    cfg = config or get_config()
    very_stable = cfg.get_threshold("spatial_stability", "very_stable_km", default=0.5)
    stable = cfg.get_threshold("spatial_stability", "stable_km", default=1.5)
    unstable = cfg.get_threshold("spatial_stability", "unstable_km", default=5.0)

    if len(lats) == 0:
        return SpatialStability(
            centroid_lat=0.0,
            centroid_lon=0.0,
            mean_distance_km=0.0,
            max_distance_km=0.0,
            radius_km=0.0,
            stability_score=0.0,
        )

    centroid_lat = float(np.mean(lats))
    centroid_lon = float(np.mean(lons))

    distances = np.array(
        [_haversine_point(centroid_lat, centroid_lon, lat, lon)
         for lat, lon in zip(lats, lons)]
    )
    mean_dist = float(np.mean(distances))
    max_dist = float(np.max(distances))

    # Normalised stability score: 100 if very stable, 0 if very spread
    if mean_dist <= very_stable:
        score = 100.0
    elif mean_dist <= stable:
        score = 100.0 - 40.0 * (mean_dist - very_stable) / (stable - very_stable)
    elif mean_dist <= unstable:
        score = 60.0 - 55.0 * (mean_dist - stable) / (unstable - stable)
    else:
        score = max(0.0, 5.0 - 5.0 * (mean_dist - unstable) / unstable)

    return SpatialStability(
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
        mean_distance_km=round(mean_dist, 4),
        max_distance_km=round(max_dist, 4),
        radius_km=round(max_dist, 4),
        stability_score=round(min(100.0, max(0.0, score)), 2),
    )


def _compute_window(
    df: pd.DataFrame,
    analysis_end: datetime,
    window_days: int,
    label: str,
) -> TemporalWindow:
    """
    Compute temporal features for a single look-back window.

    Parameters
    ----------
    df : pd.DataFrame
        Full observation DataFrame with columns:
        [timestamp, frp, latitude, longitude, satellite, sensor]
    analysis_end : datetime
        The end of the analysis period (inclusive).
    window_days : int
        Number of days to look back.
    label : str
        Human-readable label ("7d", "30d", "90d").
    """
    window_start = analysis_end - timedelta(days=window_days)
    mask = (df["timestamp"] >= window_start) & (df["timestamp"] <= analysis_end)
    sub = df[mask].copy()

    monitored_days = window_days

    tw = TemporalWindow(
        window_days=window_days,
        window_label=label,
        start=window_start,
        end=analysis_end,
        monitored_days=monitored_days,
    )

    if sub.empty:
        tw.days_since_last_detection = float(
            (analysis_end - df["timestamp"].max()).days
        ) if not df.empty else None
        return tw

    # Detection counts
    tw.detection_count = len(sub)
    if hasattr(sub["timestamp"], "dt") and hasattr(sub["timestamp"].dt, "date"):
        active_day_set = sub["timestamp"].dt.date.nunique()
    else:
        active_day_set = len(set(t.date() if hasattr(t, "date") else str(t)[:10] for t in sub["timestamp"] if pd.notna(t)))
    tw.active_days = int(active_day_set)

    # Persistence ratio
    if monitored_days > 0:
        tw.persistence_ratio = round(tw.active_days / monitored_days, 4)
    else:
        tw.persistence_ratio = None

    # Duration: span of detections
    if len(sub) > 1:
        span = (sub["timestamp"].max() - sub["timestamp"].min()).total_seconds() / 3600.0
        tw.duration_hours_total = round(span, 2)
    else:
        tw.duration_hours_total = 0.0

    # FRP statistics
    frp_vals = sub["frp"].dropna().values.astype(float)
    if len(frp_vals) > 0:
        tw.frp_mean = round(float(np.mean(frp_vals)), 4)
        tw.frp_median = round(float(np.median(frp_vals)), 4)
        tw.frp_max = round(float(np.max(frp_vals)), 4)
        tw.frp_min = round(float(np.min(frp_vals)), 4)
        tw.frp_std = round(float(np.std(frp_vals, ddof=1)) if len(frp_vals) > 1 else 0.0, 4)
        tw.frp_p90 = round(float(np.percentile(frp_vals, 90)), 4)
        tw.frp_p95 = round(float(np.percentile(frp_vals, 95)), 4)

    # Spatial
    lats = sub["latitude"].values.astype(float)
    lons = sub["longitude"].values.astype(float)
    if len(lats) > 1:
        from .clustering import _haversine_matrix
        spatial_km = _haversine_matrix(lats, lons)
        tw.spatial_extent_km = round(float(spatial_km.max()), 4)
    else:
        tw.spatial_extent_km = 0.0

    stability = compute_spatial_stability(lats, lons)
    tw.spatial_stability_score = stability.stability_score

    # Detection frequency
    if monitored_days > 0:
        tw.detection_frequency = round(tw.detection_count / monitored_days, 4)
    else:
        tw.detection_frequency = None

    # Days since last detection
    last_dt = sub["timestamp"].max()
    tw.days_since_last_detection = round(
        (analysis_end - last_dt).total_seconds() / 86400.0, 2
    )

    # Day/night distribution (UTC hour)
    if hasattr(sub["timestamp"], "dt") and hasattr(sub["timestamp"].dt, "hour"):
        hours = sub["timestamp"].dt.hour
    else:
        hours = pd.Series([
            t.hour if hasattr(t, "hour") else 0
            for t in sub["timestamp"]
        ], index=sub.index)
    tw.day_count = int(((hours >= _DAY_START_HOUR) & (hours < _DAY_END_HOUR)).sum())
    tw.night_count = int(tw.detection_count - tw.day_count)

    # Hour-of-day distribution
    hour_dist: dict[int, int] = {}
    for h, cnt in hours.value_counts().items():
        hour_dist[int(h)] = int(cnt)
    tw.hour_distribution = hour_dist

    # Weekday/weekend
    if hasattr(sub["timestamp"], "dt") and hasattr(sub["timestamp"].dt, "dayofweek"):
        dow = sub["timestamp"].dt.dayofweek  # 0=Monday, 6=Sunday
    else:
        dow = pd.Series([
            t.weekday() if hasattr(t, "weekday") else 0
            for t in sub["timestamp"]
        ], index=sub.index)
    tw.weekday_count = int((dow < 5).sum())
    tw.weekend_count = int((dow >= 5).sum())

    # Sensor distribution
    if "sensor" in sub.columns:
        sensor_dist: dict[str, int] = {}
        for s, cnt in sub["sensor"].value_counts().items():
            sensor_dist[str(s)] = int(cnt)
        tw.sensor_distribution = sensor_dist

    return tw


def extract_temporal_features(
    observations: list[Observation],
    analysis_end: Optional[datetime] = None,
    event_id: Optional[str] = None,
    facility_id: Optional[str] = None,
    config: Optional[Config] = None,
) -> TemporalFeatures:
    """
    Compute temporal features for a list of observations.

    Parameters
    ----------
    observations : list[Observation]
        All relevant observations (may span any period).
    analysis_end : datetime, optional
        The reference end date for look-back windows.
        Defaults to the latest timestamp in observations.
    event_id : str, optional
        Associated event ID.
    facility_id : str, optional
        Associated facility ID.
    config : Config, optional

    Returns
    -------
    TemporalFeatures
        Features for 7d, 30d, and 90d windows.
    """
    cfg = config or get_config()
    window_cfg = cfg.get_threshold("temporal_features", "windows", default={})
    w7 = window_cfg.get("short", 7)
    w30 = window_cfg.get("medium", 30)
    w90 = window_cfg.get("long", 90)

    if not observations:
        logger.warning("No observations for temporal feature extraction.")
        from datetime import timezone
        empty_end = analysis_end or datetime.now(timezone.utc).replace(tzinfo=None)
        return TemporalFeatures(
            event_id=event_id,
            facility_id=facility_id,
            analysis_end=empty_end,
            window_7d=TemporalWindow(window_days=w7, window_label="7d", start=empty_end - timedelta(days=w7), end=empty_end, monitored_days=w7),
            window_30d=TemporalWindow(window_days=w30, window_label="30d", start=empty_end - timedelta(days=w30), end=empty_end, monitored_days=w30),
            window_90d=TemporalWindow(window_days=w90, window_label="90d", start=empty_end - timedelta(days=w90), end=empty_end, monitored_days=w90),
        )

    records = []
    for obs in observations:
        records.append({
            "timestamp": obs.timestamp_utc,
            "frp": obs.frp,
            "confidence": obs.confidence,
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "satellite": obs.satellite,
            "sensor": obs.sensor or "UNKNOWN",
        })
    df = pd.DataFrame(records)
    ts_converted = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    if hasattr(ts_converted, "dt") and hasattr(ts_converted.dt, "tz_localize"):
        df["timestamp"] = ts_converted.dt.tz_localize(None)
    elif isinstance(ts_converted, pd.Timestamp):
        df["timestamp"] = ts_converted.tz_localize(None)
    else:
        df["timestamp"] = ts_converted

    end_dt = analysis_end or df["timestamp"].max().to_pydatetime()
    if isinstance(end_dt, pd.Timestamp):
        end_dt = end_dt.to_pydatetime()
    end_dt = end_dt.replace(tzinfo=None)

    logger.debug(
        "Extracting temporal features: %d obs, end=%s, windows=%d/%d/%d d",
        len(df), end_dt, w7, w30, w90,
    )

    tw7 = _compute_window(df, end_dt, w7, "7d")
    tw30 = _compute_window(df, end_dt, w30, "30d")
    tw90 = _compute_window(df, end_dt, w90, "90d")

    return TemporalFeatures(
        event_id=event_id,
        facility_id=facility_id,
        analysis_end=end_dt,
        window_7d=tw7,
        window_30d=tw30,
        window_90d=tw90,
    )
