"""
ThermoTrace Feature Engineering V2: Industrial Context Features
===============================================================

Translates OpenStreetMap industrial facility distances and proximity flags into
continuous industrial exposure scores and category-specific context indicators.
"""

import numpy as np
import pandas as pd

def extract_v2_industrial_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives industrial proximity score (0-100), industrial context flag,
    and category-specific context indicators.
    """
    dist_fac = df["distance_to_facility_km"].values.astype(np.float32)

    # 1. Industrial Proximity Score (0.0 to 100.0)
    # 100 at 0km, ~50 at 2km, decaying with 3km scale
    ind_score = np.clip(100.0 * np.exp(-dist_fac / 3.0), 0.0, 100.0).astype(np.float32)

    # 2. General Industrial Context Flag (< 2.0 km)
    ind_flag = (dist_fac <= 2.0)

    # 3. Category Context Indicators
    power_ctx = df["near_power_plant"].values.astype(bool)
    factory_ctx = df["near_factory"].values.astype(bool)
    quarry_ctx = df["near_quarry"].values.astype(bool)
    refinery_ctx = df["near_refinery"].values.astype(bool)
    mining_ctx = df["near_mine"].values.astype(bool)
    storage_ctx = df["near_storage_facility"].values.astype(bool)
    substation_ctx = df["near_substation"].values.astype(bool)

    return pd.DataFrame({
        "industrial_proximity_score": ind_score,
        "industrial_context_flag": ind_flag,
        "power_generation_context": power_ctx,
        "factory_context": factory_ctx,
        "quarry_context": quarry_ctx,
        "refinery_context": refinery_ctx,
        "mining_context": mining_ctx,
        "storage_context": storage_ctx,
        "substation_context": substation_ctx
    }, index=df.index)
