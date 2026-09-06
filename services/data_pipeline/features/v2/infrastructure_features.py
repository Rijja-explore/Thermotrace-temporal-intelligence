"""
ThermoTrace Feature Engineering V2: Infrastructure Proximity Features
=====================================================================

Derives network proximity scores for roads, railways, transmission lines,
and pipelines, and establishes transport corridor proximity flags.
"""

import numpy as np
import pandas as pd

def extract_v2_infrastructure_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes infrastructure corridor proximity scores (0-100),
    transport corridor flags, and composite infrastructure context scores.
    """
    d_road = df["distance_to_major_road_km"].values.astype(np.float32)
    d_rail = df["distance_to_railway_km"].values.astype(np.float32)
    d_power = df["distance_to_power_line_km"].values.astype(np.float32)
    d_pipe = df["distance_to_pipeline_km"].values.astype(np.float32)

    # 1. Proximity Scores (0.0 to 100.0)
    # Exponential decay with characteristic distances (2km for roads/rail/power, 5km for pipelines)
    road_score = np.clip(100.0 * np.exp(-d_road / 2.0), 0.0, 100.0).astype(np.float32)
    rail_score = np.clip(100.0 * np.exp(-d_rail / 2.0), 0.0, 100.0).astype(np.float32)
    power_score = np.clip(100.0 * np.exp(-d_power / 2.0), 0.0, 100.0).astype(np.float32)
    pipe_score = np.clip(100.0 * np.exp(-d_pipe / 5.0), 0.0, 100.0).astype(np.float32)

    # 2. Transport Corridor Flag (< 1.0 km from road or rail)
    corridor_flag = (d_road <= 1.0) | (d_rail <= 1.0)

    # 3. Composite Infrastructure Context Score
    infra_score = np.maximum.reduce([road_score, rail_score, power_score, pipe_score]).astype(np.float32)

    return pd.DataFrame({
        "road_proximity_score": road_score,
        "railway_proximity_score": rail_score,
        "power_infrastructure_proximity": power_score,
        "pipeline_proximity_score": pipe_score,
        "transport_corridor_flag": corridor_flag,
        "infrastructure_context_score": infra_score
    }, index=df.index)
