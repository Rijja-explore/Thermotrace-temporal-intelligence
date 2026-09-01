"""
facility_fingerprint.py – Builds a facility thermal fingerprint from historical observations.

The fingerprint answers: "What normally happens at this facility?"

It summarises historical detection patterns using robust statistics so that
a single outlier event does not distort the normal behaviour profile.

History quality labels:
  good        – sufficient observations and history span
  moderate    – some history but limited
  poor        – very limited history
  insufficient – not enough data to build a meaningful fingerprint
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from .config_loader import Config, get_config
from .schemas import FacilityFingerprint, HistoryQuality, Observation

logger = logging.getLogger(__name__)


def build_facility_fingerprint(
    facility_id: str,
    observations: list[Observation],
    facility_type: Optional[str] = None,
    config: Optional[Config] = None,
) -> FacilityFingerprint:
    """
    Build a thermal fingerprint for a facility from its historical observations.

    Parameters
    ----------
    facility_id : str
    observations : list[Observation]
        All historical observations for this facility (should NOT include
        current-period observations – see baseline.py for leakage prevention).
    facility_type : str, optional
    config : Config, optional

    Returns
    -------
    FacilityFingerprint
    """
    cfg = config or get_config()
    good_min_obs = cfg.get_threshold("history_quality", "good_min_observations", default=30)
    good_min_days = cfg.get_threshold("history_quality", "good_min_days", default=14)
    mod_min_obs = cfg.get_threshold("history_quality", "moderate_min_observations", default=10)
    mod_min_days = cfg.get_threshold("history_quality", "moderate_min_days", default=5)

    logger.info("Building fingerprint for facility=%s (%d observations)", facility_id, len(observations))

    fingerprint = FacilityFingerprint(
        facility_id=facility_id,
        facility_type=facility_type,
        observation_count=0,
        active_days=0,
        history_quality=HistoryQuality.INSUFFICIENT,
    )

    if not observations:
        logger.warning("No observations for facility=%s – returning insufficient fingerprint", facility_id)
        return fingerprint

    records = [
        {
            "timestamp": obs.timestamp_utc,
            "frp": obs.frp,
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "sensor": obs.sensor or "UNKNOWN",
        }
        for obs in observations
    ]
    df = pd.DataFrame(records)
    ts_converted = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    if hasattr(ts_converted, "dt") and hasattr(ts_converted.dt, "tz_localize"):
        df["timestamp"] = ts_converted.dt.tz_localize(None)
    elif isinstance(ts_converted, pd.Timestamp):
        df["timestamp"] = ts_converted.tz_localize(None)
    else:
        df["timestamp"] = ts_converted

    observation_count = len(df)
    if hasattr(df["timestamp"], "dt") and hasattr(df["timestamp"].dt, "date"):
        active_days = int(df["timestamp"].dt.date.nunique())
    else:
        active_days = len(set(t.date() if hasattr(t, "date") else str(t)[:10] for t in df["timestamp"] if pd.notna(t)))
    min_ts = df["timestamp"].min()
    max_ts = df["timestamp"].max()
    baseline_start = min_ts.to_pydatetime() if hasattr(min_ts, "to_pydatetime") else min_ts
    baseline_end = max_ts.to_pydatetime() if hasattr(max_ts, "to_pydatetime") else max_ts
    total_days = max((baseline_end - baseline_start).days, 1) if hasattr(baseline_end - baseline_start, "days") else 1

    # Determine quality
    if observation_count >= good_min_obs and active_days >= good_min_days:
        quality = HistoryQuality.GOOD
    elif observation_count >= mod_min_obs and active_days >= mod_min_days:
        quality = HistoryQuality.MODERATE
    elif observation_count >= 3:
        quality = HistoryQuality.POOR
    else:
        quality = HistoryQuality.INSUFFICIENT

    # FRP statistics (robust)
    frp_vals = df["frp"].dropna().values.astype(float)
    frp_mean = float(np.mean(frp_vals)) if len(frp_vals) > 0 else None
    frp_median = float(np.median(frp_vals)) if len(frp_vals) > 0 else None
    frp_std = float(np.std(frp_vals, ddof=1)) if len(frp_vals) > 1 else None
    frp_p90 = float(np.percentile(frp_vals, 90)) if len(frp_vals) > 0 else None
    frp_p95 = float(np.percentile(frp_vals, 95)) if len(frp_vals) > 0 else None

    # Detection frequency (detections per monitored day)
    normal_detection_frequency = round(observation_count / total_days, 4) if total_days > 0 else None

    # Spatial extent
    lats = df["latitude"].values.astype(float)
    lons = df["longitude"].values.astype(float)
    normal_spatial_extent: Optional[float] = None
    if len(lats) > 1:
        from .clustering import _haversine_matrix
        sp = _haversine_matrix(lats, lons)
        normal_spatial_extent = round(float(sp.max()), 4)

    # Hour distribution
    if hasattr(df["timestamp"], "dt") and hasattr(df["timestamp"].dt, "hour"):
        hour_series = df["timestamp"].dt.hour
    else:
        hour_series = pd.Series([
            t.hour if hasattr(t, "hour") else 0
            for t in df["timestamp"]
        ], index=df.index)

    hour_counts = hour_series.value_counts().sort_index()
    total_obs_for_hour = max(len(df), 1)
    normal_active_hours = {
        int(h): round(cnt / total_obs_for_hour, 4)
        for h, cnt in hour_counts.items()
    }

    fingerprint = FacilityFingerprint(
        facility_id=facility_id,
        facility_type=facility_type,
        observation_count=observation_count,
        active_days=active_days,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        normal_detection_frequency=normal_detection_frequency,
        normal_frp_mean=round(frp_mean, 4) if frp_mean is not None else None,
        normal_frp_median=round(frp_median, 4) if frp_median is not None else None,
        normal_frp_std=round(frp_std, 4) if frp_std is not None else None,
        normal_frp_p90=round(frp_p90, 4) if frp_p90 is not None else None,
        normal_frp_p95=round(frp_p95, 4) if frp_p95 is not None else None,
        normal_active_hours=normal_active_hours,
        normal_spatial_extent=normal_spatial_extent,
        history_quality=quality,
    )

    logger.info(
        "Fingerprint for %s: quality=%s, obs=%d, active_days=%d, frp_mean=%.2f",
        facility_id, quality.value, observation_count, active_days,
        frp_mean if frp_mean is not None else float("nan"),
    )
    return fingerprint
