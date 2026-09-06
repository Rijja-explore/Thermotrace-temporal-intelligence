"""
anomaly.py – Transparent anomaly detection engine.

Uses multiple statistical signals rather than a black-box model:
  1. FRP intensity deviation (z-score and robust z-score / MAD)
  2. Detection frequency deviation
  3. Persistence change (active day ratio vs baseline)
  4. Spatial change (spatial extent vs historical)
  5. Duration change (vs typical historical duration)

Each signal produces a component score (0–100).
A weighted composite yields the final anomaly_score.

The approach prioritises explainability over complexity.
Deep learning is deliberately NOT used at this stage.

Anomaly levels:
  normal  – score ≤ 30
  watch   – 30 < score ≤ 55
  abnormal – 55 < score ≤ 80
  severe  – score > 80

All thresholds and weights are read from configuration.
Returns anomaly_reasons so the analyst understands each contribution.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from .config_loader import Config, get_config
from .schemas import AnomalyLevel, AnomalyResult, Baseline, HistoryQuality

logger = logging.getLogger(__name__)


def _robust_zscore(value: float, median: float, mad: float) -> Optional[float]:
    """Compute robust z-score (modified) using median and MAD."""
    if mad == 0:
        return None
    return (value - median) / (1.4826 * mad)  # 1.4826 normalises MAD to std for normal dist


def _component_score_from_zscore(z: float, threshold: float) -> float:
    """
    Convert a z-score to a 0–100 component contribution.
    Score = 0 if z ≤ 0; rises to 100 as z >> threshold.
    """
    if z <= 0:
        return 0.0
    # Sigmoid-like mapping: score = 100 * (1 - exp(-z/threshold))
    score = 100.0 * (1.0 - np.exp(-z / max(threshold, 0.01)))
    return float(np.clip(score, 0.0, 100.0))


def _pct_deviation_score(pct: Optional[float], threshold_pct: float) -> float:
    """
    Convert a percentage deviation to a 0–100 component score.
    Returns 0 if pct is None or negative.
    """
    if pct is None or pct <= 0:
        return 0.0
    score = 100.0 * (1.0 - np.exp(-pct / max(threshold_pct, 0.01)))
    return float(np.clip(score, 0.0, 100.0))


def detect_anomaly(
    current_frp_mean: Optional[float],
    current_frp_max: Optional[float],
    current_detection_frequency: Optional[float],
    current_active_ratio: Optional[float],
    current_spatial_extent: Optional[float],
    current_duration_hours: Optional[float],
    baseline: Baseline,
    deviation: dict,
    config: Optional[Config] = None,
) -> AnomalyResult:
    """
    Compute the anomaly score from multiple signals.

    Parameters
    ----------
    current_frp_mean : float | None
    current_frp_max : float | None
    current_detection_frequency : float | None
    current_active_ratio : float | None
    current_spatial_extent : float | None
    current_duration_hours : float | None
    baseline : Baseline
    deviation : dict
        Pre-computed deviation dictionary from baseline.compute_deviation()
    config : Config, optional

    Returns
    -------
    AnomalyResult
    """
    cfg = config or get_config()

    frp_zscore_thresh: float = cfg.get_threshold("anomaly", "frp_zscore_threshold", default=2.0)
    frp_robust_thresh: float = cfg.get_threshold("anomaly", "frp_robust_zscore_threshold", default=3.0)
    freq_pct_thresh: float = cfg.get_threshold("anomaly", "frequency_deviation_pct_threshold", default=50.0)
    persistence_thresh: float = cfg.get_threshold("anomaly", "persistence_change_threshold", default=0.25)
    spatial_thresh_km: float = cfg.get_threshold("anomaly", "spatial_change_threshold_km", default=2.0)
    duration_thresh_h: float = cfg.get_threshold("anomaly", "duration_change_threshold_hours", default=24.0)

    # Weight each anomaly signal
    w = cfg.weights.get("anomaly", {})
    w_frp: float = w.get("frp_deviation_weight", 0.35)
    w_freq: float = w.get("frequency_deviation_weight", 0.25)
    w_pers: float = w.get("persistence_change_weight", 0.20)
    w_spat: float = w.get("spatial_change_weight", 0.10)
    w_dur: float = w.get("duration_change_weight", 0.10)

    reasons: list[str] = []
    component_scores: dict[str, float] = {}
    data_quality_notes: list[str] = []

    if not baseline.available:
        data_quality_notes.append(
            "Baseline unavailable – anomaly assessment requires historical data (insufficient_history)."
        )
        return AnomalyResult(
            anomaly_score=0.0,
            anomaly_level=AnomalyLevel.UNKNOWN,
            reasons=["Insufficient historical data to assess anomaly."],
            component_scores={},
            data_quality_notes=data_quality_notes,
        )

    if baseline.history_quality == HistoryQuality.INSUFFICIENT:
        data_quality_notes.append(
            "Baseline is based on very limited data – anomaly score has low confidence (requires_verification)."
        )

    # -----------------------------------------------------------------------
    # Signal 1: FRP intensity deviation
    # -----------------------------------------------------------------------
    frp_score = 0.0
    if current_frp_mean is not None and baseline.frp_mean is not None:
        std = baseline.frp_std if baseline.frp_std else 0.0
        if std > 0:
            z = (current_frp_mean - baseline.frp_mean) / std
            frp_score = _component_score_from_zscore(z, frp_zscore_thresh)
            if z > frp_zscore_thresh:
                reasons.append(
                    f"Current FRP mean ({current_frp_mean:.1f} MW) is {z:.1f}σ above baseline "
                    f"mean ({baseline.frp_mean:.1f} MW)."
                )
        else:
            # std == 0: check if current exceeds baseline
            if current_frp_mean > (baseline.frp_mean or 0):
                frp_score = 50.0
                reasons.append(
                    f"Current FRP ({current_frp_mean:.1f} MW) exceeds historical baseline "
                    f"({baseline.frp_mean:.1f} MW); baseline has zero variance."
                )

        # Also check vs upper quantile
        if baseline.frp_upper_quantile is not None and current_frp_mean > baseline.frp_upper_quantile:
            reasons.append(
                f"Current FRP mean exceeds the historical {int(cfg.get_threshold('baseline', 'upper_quantile', default=0.9)*100)}th-percentile "
                f"({baseline.frp_upper_quantile:.1f} MW)."
            )
            frp_score = min(100.0, frp_score + 20.0)

        # Check max FRP vs baseline upper
        if current_frp_max is not None and baseline.frp_upper_quantile is not None:
            if current_frp_max > baseline.frp_upper_quantile * 1.5:
                reasons.append(
                    f"Peak FRP ({current_frp_max:.1f} MW) is substantially above historical upper range "
                    f"({baseline.frp_upper_quantile:.1f} MW)."
                )
                frp_score = min(100.0, frp_score + 15.0)
    elif current_frp_mean is None:
        data_quality_notes.append("Current FRP data unavailable – FRP anomaly signal missing.")
    else:
        data_quality_notes.append("Baseline FRP not available – FRP anomaly signal incomplete.")

    component_scores["frp_deviation"] = round(frp_score, 2)

    # -----------------------------------------------------------------------
    # Signal 2: Detection frequency deviation
    # -----------------------------------------------------------------------
    freq_score = 0.0
    freq_pct = deviation.get("frequency_deviation_percent")
    if freq_pct is not None:
        freq_score = _pct_deviation_score(freq_pct, freq_pct_thresh)
        if freq_pct >= freq_pct_thresh:
            reasons.append(
                f"Detection frequency is {freq_pct:.1f}% above baseline level."
            )
    else:
        data_quality_notes.append("Detection frequency deviation not available.")

    component_scores["frequency_deviation"] = round(freq_score, 2)

    # -----------------------------------------------------------------------
    # Signal 3: Persistence change
    # -----------------------------------------------------------------------
    pers_score = 0.0
    active_deviation = deviation.get("active_day_deviation")
    if active_deviation is not None:
        if active_deviation > persistence_thresh:
            pers_score = min(100.0, (active_deviation / persistence_thresh) * 50.0)
            reasons.append(
                f"Active day ratio increased by {active_deviation:.2f} above baseline "
                f"(threshold: {persistence_thresh:.2f})."
            )
        elif active_deviation < -persistence_thresh:
            # Decrease in persistence is NOT necessarily anomalous; don't penalise
            pass

    component_scores["persistence_change"] = round(pers_score, 2)

    # -----------------------------------------------------------------------
    # Signal 4: Spatial change
    # -----------------------------------------------------------------------
    spat_score = 0.0
    spat_deviation = deviation.get("spatial_deviation")
    if spat_deviation is not None and spat_deviation > 0:
        spat_score = min(100.0, (spat_deviation / spatial_thresh_km) * 50.0)
        if spat_deviation >= spatial_thresh_km:
            reasons.append(
                f"Spatial extent increased by {spat_deviation:.2f} km vs baseline "
                f"(threshold: {spatial_thresh_km:.1f} km)."
            )

    component_scores["spatial_change"] = round(spat_score, 2)

    # -----------------------------------------------------------------------
    # Signal 5: Duration change
    # -----------------------------------------------------------------------
    dur_score = 0.0
    if current_duration_hours is not None and current_duration_hours > duration_thresh_h:
        dur_score = min(100.0, (current_duration_hours / duration_thresh_h) * 40.0)
        reasons.append(
            f"Event duration ({current_duration_hours:.1f} h) exceeds threshold "
            f"({duration_thresh_h:.1f} h)."
        )

    component_scores["duration_change"] = round(dur_score, 2)

    # -----------------------------------------------------------------------
    # Composite anomaly score (weighted sum)
    # -----------------------------------------------------------------------
    total_w = w_frp + w_freq + w_pers + w_spat + w_dur
    if total_w == 0:
        total_w = 1.0  # safety guard

    composite = (
        frp_score * w_frp
        + freq_score * w_freq
        + pers_score * w_pers
        + spat_score * w_spat
        + dur_score * w_dur
    ) / total_w

    anomaly_score = round(float(np.clip(composite, 0.0, 100.0)), 2)

    # Anomaly level from config thresholds
    levels = cfg.get_threshold("anomaly", "levels", default={})
    normal_max = levels.get("normal_max", 30)
    watch_max = levels.get("watch_max", 55)
    abnormal_max = levels.get("abnormal_max", 80)

    if anomaly_score <= normal_max:
        level = AnomalyLevel.NORMAL
    elif anomaly_score <= watch_max:
        level = AnomalyLevel.WATCH
    elif anomaly_score <= abnormal_max:
        level = AnomalyLevel.ABNORMAL
    else:
        level = AnomalyLevel.SEVERE

    if not reasons:
        reasons.append("Current activity is within historical norms.")

    logger.info("Anomaly score=%.1f level=%s", anomaly_score, level.value)

    return AnomalyResult(
        anomaly_score=anomaly_score,
        anomaly_level=level,
        reasons=reasons,
        component_scores=component_scores,
        data_quality_notes=data_quality_notes,
    )
