"""
baseline.py – Baseline calculation engine.

IMPORTANT: The baseline MUST be calculated ONLY from historical data
that pre-dates the current analysis period. No current-period data
may be included. This prevents data leakage and baseline contamination.

The baseline represents:
"What was normal activity at this facility before the current period?"

Returns:
  - baseline statistics (mean, median, std, quantiles)
  - history quality assessment
  - explicit notes when data is insufficient
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from .config_loader import Config, get_config
from .schemas import Baseline, HistoryQuality, Observation

logger = logging.getLogger(__name__)


def compute_baseline(
    historical_observations: list[Observation],
    current_period_start: datetime,
    facility_id: Optional[str] = None,
    config: Optional[Config] = None,
) -> Baseline:
    """
    Compute baseline statistics from historical observations.

    Only observations BEFORE current_period_start are used.
    This enforces a hard cut-off and prevents data leakage.

    Parameters
    ----------
    historical_observations : list[Observation]
        All observations for the facility (may include current-period ones;
        this function will filter them out).
    current_period_start : datetime
        Observations from this datetime onward are excluded from baseline.
    facility_id : str, optional
    config : Config, optional

    Returns
    -------
    Baseline
    """
    cfg = config or get_config()
    min_obs = cfg.get_threshold("baseline", "min_observations_for_baseline", default=5)
    min_days = cfg.get_threshold("baseline", "min_days_for_good_baseline", default=14)
    upper_q = cfg.get_threshold("baseline", "upper_quantile", default=0.90)
    lower_q = cfg.get_threshold("baseline", "lower_quantile", default=0.10)

    # Normalise cutoff to timezone-naive
    cutoff = current_period_start.replace(tzinfo=None) if current_period_start.tzinfo else current_period_start

    logger.info(
        "Computing baseline for facility=%s, cutoff=%s, total_obs=%d",
        facility_id, cutoff.isoformat(), len(historical_observations),
    )

    def _to_naive_dt(val: Any) -> datetime:
        if isinstance(val, datetime):
            return val.replace(tzinfo=None) if val.tzinfo else val
        if hasattr(val, "to_pydatetime"):
            dt = val.to_pydatetime()
            return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt
        try:
            dt = pd.to_datetime(val)
            if hasattr(dt, "to_pydatetime"):
                pydt = dt.to_pydatetime()
                return pydt.replace(tzinfo=None) if getattr(pydt, "tzinfo", None) else pydt
        except Exception:
            pass
        return datetime.min

    # Filter: only historical (pre-cutoff) observations
    pre_obs = [
        obs for obs in historical_observations
        if _to_naive_dt(obs.timestamp_utc) < cutoff
    ]

    notes: list[str] = []

    if not pre_obs:
        notes.append(
            "No historical observations before current period – baseline unavailable (insufficient_history)."
        )
        logger.warning("No pre-period observations for baseline (facility=%s)", facility_id)
        return Baseline(
            available=False,
            facility_id=facility_id,
            history_count=0,
            history_quality=HistoryQuality.INSUFFICIENT,
            notes=notes,
        )

    if len(pre_obs) < min_obs:
        notes.append(
            f"Only {len(pre_obs)} historical observations found; minimum recommended is {min_obs}. "
            "Statistics are unreliable (insufficient_history)."
        )

    records = [
        {
            "timestamp": obs.timestamp_utc,
            "frp": obs.frp,
            "latitude": obs.latitude,
            "longitude": obs.longitude,
        }
        for obs in pre_obs
    ]
    df = pd.DataFrame(records)
    ts_converted = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    if hasattr(ts_converted, "dt") and hasattr(ts_converted.dt, "tz_localize"):
        df["timestamp"] = ts_converted.dt.tz_localize(None)
    elif isinstance(ts_converted, pd.Timestamp):
        df["timestamp"] = ts_converted.tz_localize(None)
    else:
        df["timestamp"] = ts_converted

    history_count = len(df)
    min_ts = df["timestamp"].min()
    max_ts = df["timestamp"].max()
    baseline_start = min_ts.to_pydatetime() if hasattr(min_ts, "to_pydatetime") else min_ts
    baseline_end = max_ts.to_pydatetime() if hasattr(max_ts, "to_pydatetime") else max_ts
    total_days = max((baseline_end - baseline_start).days, 1) if hasattr(baseline_end - baseline_start, "days") else 1
    if hasattr(df["timestamp"], "dt") and hasattr(df["timestamp"].dt, "date"):
        active_days = int(df["timestamp"].dt.date.nunique())
    else:
        active_days = len(set(t.date() if hasattr(t, "date") else str(t)[:10] for t in df["timestamp"] if pd.notna(t)))

    # Quality
    if history_count >= cfg.get_threshold("history_quality", "good_min_observations", default=30) \
            and active_days >= min_days:
        quality = HistoryQuality.GOOD
    elif history_count >= cfg.get_threshold("history_quality", "moderate_min_observations", default=10) \
            and active_days >= cfg.get_threshold("history_quality", "moderate_min_days", default=5):
        quality = HistoryQuality.MODERATE
    elif history_count >= min_obs:
        quality = HistoryQuality.POOR
    else:
        quality = HistoryQuality.INSUFFICIENT
        notes.append("Insufficient data for reliable baseline – treat results as indicative only.")

    # FRP statistics
    frp_vals = df["frp"].dropna().values.astype(float)

    def safe_stat(fn, *args):
        try:
            result = fn(*args)
            return None if (np.isnan(result) or np.isinf(result)) else float(result)
        except Exception:
            return None

    frp_mean = safe_stat(np.mean, frp_vals) if len(frp_vals) > 0 else None
    frp_median = safe_stat(np.median, frp_vals) if len(frp_vals) > 0 else None
    frp_std = safe_stat(np.std, frp_vals, 1) if len(frp_vals) > 1 else 0.0
    frp_upper_q = safe_stat(np.percentile, frp_vals, upper_q * 100) if len(frp_vals) > 0 else None
    frp_lower_q = safe_stat(np.percentile, frp_vals, lower_q * 100) if len(frp_vals) > 0 else None

    # Detection frequency
    detection_frequency = round(history_count / total_days, 4) if total_days > 0 else None

    # Active days ratio
    active_days_ratio = round(active_days / total_days, 4) if total_days > 0 else None

    # Spatial extent
    lats = df["latitude"].values.astype(float)
    lons = df["longitude"].values.astype(float)
    spatial_extent_mean: Optional[float] = None
    if len(lats) > 1:
        from .clustering import _haversine_matrix
        sp = _haversine_matrix(lats, lons)
        spatial_extent_mean = round(float(sp.max()), 4)

    if len(frp_vals) == 0:
        notes.append("All historical FRP values are missing – FRP baseline is unavailable.")

    return Baseline(
        available=True,
        facility_id=facility_id,
        baseline_period_start=baseline_start,
        baseline_period_end=baseline_end,
        frp_mean=round(frp_mean, 4) if frp_mean is not None else None,
        frp_median=round(frp_median, 4) if frp_median is not None else None,
        frp_std=round(frp_std, 4) if frp_std is not None else None,
        frp_upper_quantile=round(frp_upper_q, 4) if frp_upper_q is not None else None,
        frp_lower_quantile=round(frp_lower_q, 4) if frp_lower_q is not None else None,
        detection_frequency=detection_frequency,
        active_days_ratio=active_days_ratio,
        spatial_extent_mean=spatial_extent_mean,
        history_count=history_count,
        history_quality=quality,
        notes=notes,
    )


def compute_deviation(
    current_frp_mean: Optional[float],
    current_detection_frequency: Optional[float],
    current_active_ratio: Optional[float],
    current_spatial_extent: Optional[float],
    baseline: Baseline,
) -> dict:
    """
    Compare current activity statistics against the baseline.

    Returns a plain dict (compatible with Deviation schema) with:
    - frp_deviation, frp_deviation_percent
    - frequency_deviation, frequency_deviation_percent
    - active_day_deviation
    - spatial_deviation
    - notes

    All divisions are safe. No NaN/Inf values are returned.
    """
    notes: list[str] = []

    def safe_pct(current, base_value):
        """((current - base) / base) * 100, safe for base == 0."""
        if current is None or base_value is None:
            return None
        if base_value == 0:
            notes.append(
                f"Baseline value is zero; percentage deviation is not calculable "
                f"(reporting absolute deviation only)."
            )
            return None
        pct = ((current - base_value) / abs(base_value)) * 100.0
        if np.isnan(pct) or np.isinf(pct):
            return None
        return round(float(pct), 2)

    def safe_diff(a, b):
        if a is None or b is None:
            return None
        result = a - b
        if np.isnan(result) or np.isinf(result):
            return None
        return round(float(result), 4)

    if not baseline.available:
        notes.append("Baseline unavailable – deviation cannot be computed (insufficient_history).")
        return {
            "frp_deviation": None,
            "frp_deviation_percent": None,
            "frequency_deviation": None,
            "frequency_deviation_percent": None,
            "active_day_deviation": None,
            "spatial_deviation": None,
            "notes": notes,
        }

    return {
        "frp_deviation": safe_diff(current_frp_mean, baseline.frp_mean),
        "frp_deviation_percent": safe_pct(current_frp_mean, baseline.frp_mean),
        "frequency_deviation": safe_diff(current_detection_frequency, baseline.detection_frequency),
        "frequency_deviation_percent": safe_pct(current_detection_frequency, baseline.detection_frequency),
        "active_day_deviation": safe_diff(current_active_ratio, baseline.active_days_ratio),
        "spatial_deviation": safe_diff(current_spatial_extent, baseline.spatial_extent_mean),
        "notes": notes,
    }
