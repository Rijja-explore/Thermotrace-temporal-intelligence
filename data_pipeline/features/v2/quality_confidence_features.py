"""
ThermoTrace Feature Engineering V2: Data Quality & Confidence Features
======================================================================

Derives objective observation confidence scores, multi-sensor confirmation flags,
and observation quality tiers from sensor counts, detections, and signal strength.
"""

import numpy as np
import pandas as pd

def extract_v2_quality_confidence_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes data confidence score (0-100), multi-satellite confirmation flags,
    and categorical observation quality ratings.
    """
    n_sats = df["unique_satellite_count"].values.astype(np.int32)
    n_dets = df["detection_count"].values.astype(np.int32)
    duration = df["duration_hours"].values.astype(np.float32)
    max_frp = df["max_frp_mw"].values.astype(np.float32)

    # 1. Multi-Satellite Confirmation
    multi_sat = (n_sats > 1)

    # 2. Additive Confidence Points
    # Base: 30 pts for single detection
    # Detections: up to +35 pts
    # Multi-satellite: +20 pts
    # Duration > 0: +10 pts
    # High FRP (> 10 MW): +5 pts
    score = np.full(len(df), 30.0, dtype=np.float32)
    score += np.clip((n_dets - 1) * 7.0, 0.0, 35.0)
    score += np.where(multi_sat, 20.0, 0.0)
    score += np.where(duration > 0.0, 10.0, 0.0)
    score += np.where(max_frp >= 10.0, 5.0, 0.0)
    conf_score = np.clip(score, 0.0, 100.0).astype(np.float32)

    # 3. High and Low Confidence Flags
    high_conf = (conf_score >= 70.0)
    low_conf = (conf_score < 40.0)

    # 4. Observation Quality Tier
    conditions = [
        conf_score >= 70.0,
        (conf_score >= 40.0) & (conf_score < 70.0),
        conf_score < 40.0
    ]
    choices = ["HIGH", "MEDIUM", "LOW"]
    quality_tier = pd.Series(np.select(conditions, choices, default="MEDIUM"), index=df.index, dtype="string")

    return pd.DataFrame({
        "multi_satellite_confirmation": multi_sat,
        "data_confidence_score": conf_score,
        "high_confidence_event": high_conf,
        "low_confidence_event": low_conf,
        "event_observation_quality": quality_tier
    }, index=df.index)
