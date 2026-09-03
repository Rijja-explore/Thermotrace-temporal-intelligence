"""
ThermoTrace Feature Engineering V2: Conservation & Protected Area Features
==========================================================================

Quantifies ecological conservation sensitivity and protected area proximity
classes derived from UNEP-WCMC WDPA spatial containment and distance queries.
"""

import numpy as np
import pandas as pd

def extract_v2_conservation_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives conservation sensitivity score (0-100), alert flags,
    and proximity classifications.
    """
    inside = df["inside_protected_area"].values.astype(bool)
    dist_pa = df["distance_to_protected_area_km"].values.astype(np.float32)

    # 1. Conservation Sensitivity Score (0.0 to 100.0)
    # 100.0 inside; decaying exponentially with e-folding scale of 3.0 km
    decay_score = 100.0 * np.exp(-dist_pa / 3.0)
    cons_score = np.where(inside, 100.0, np.clip(decay_score, 0.0, 100.0)).astype(np.float32)

    # 2. Protected Area Alert Flag
    alert_flag = inside | (dist_pa <= 1.0)

    # 3. Proximity Classification
    conditions = [
        inside,
        (~inside) & (dist_pa <= 1.0),
        (~inside) & (dist_pa > 1.0) & (dist_pa <= 5.0),
        dist_pa > 5.0
    ]
    choices = ["INSIDE", "IMMEDIATE_BUFFER_1KM", "PROXIMATE_5KM", "DISTANT"]
    proximity_class = pd.Series(np.select(conditions, choices, default="DISTANT"), index=df.index, dtype="string")

    return pd.DataFrame({
        "conservation_sensitivity_score": cons_score,
        "protected_area_alert_flag": alert_flag,
        "protected_area_proximity_class": proximity_class
    }, index=df.index)
