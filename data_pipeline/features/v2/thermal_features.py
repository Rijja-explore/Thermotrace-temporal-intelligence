"""
ThermoTrace Feature Engineering V2: Thermal Behaviour Features
==============================================================

Extracts derived radiative energy, spatial concentration, and persistence metrics
from M3 thermal event cluster attributes.
"""

import numpy as np
import pandas as pd

def extract_v2_thermal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes derived thermal behaviour features with strict division-by-zero guards.
    Preserves original MW measurements and applies safe log1p transformations.
    """
    max_frp = df["max_frp_mw"].values.astype(np.float32)
    mean_frp = df["mean_frp_mw"].values.astype(np.float32)
    sum_frp = df["sum_frp_mw"].values.astype(np.float32)
    duration = df["duration_hours"].values.astype(np.float32)
    extent = df["spatial_extent_km"].values.astype(np.float32)
    det_count = df["detection_count"].values.astype(np.float32)

    # 1. Log Transformations (safe log1p)
    log_max = np.log1p(np.maximum(max_frp, 0.0)).astype(np.float32)
    log_mean = np.log1p(np.maximum(mean_frp, 0.0)).astype(np.float32)
    log_sum = np.log1p(np.maximum(sum_frp, 0.0)).astype(np.float32)

    # 2. Radiative Concentration & Variability
    intensity = (sum_frp / (extent + 0.1)).astype(np.float32)
    variability = np.clip((max_frp - mean_frp) / (mean_frp + 1e-3), 0.0, 100.0).astype(np.float32)
    frp_per_det = (sum_frp / np.maximum(det_count, 1.0)).astype(np.float32)
    frp_per_hour = (sum_frp / (duration + 0.1)).astype(np.float32)
    det_density = (det_count / (extent + 0.1)).astype(np.float32)

    # 3. Persistence and Concentration Indicators [0.0 - 1.0]
    persistence = np.clip(duration / 0.5, 0.0, 1.0).astype(np.float32)
    concentration = np.clip(max_frp / (sum_frp + 1e-3), 0.0, 1.0).astype(np.float32)

    return pd.DataFrame({
        "log_max_frp": log_max,
        "log_mean_frp": log_mean,
        "log_sum_frp": log_sum,
        "thermal_intensity": intensity,
        "thermal_frp_variability": variability,
        "thermal_frp_per_detection": frp_per_det,
        "thermal_frp_per_hour": frp_per_hour,
        "thermal_detection_density": det_density,
        "thermal_persistence_indicator": persistence,
        "thermal_concentration_indicator": concentration
    }, index=df.index)
