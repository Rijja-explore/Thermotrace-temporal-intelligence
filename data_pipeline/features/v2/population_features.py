"""
ThermoTrace Feature Engineering V2: Population Exposure Features
================================================================

Transforms continuous 100m population counts and densities into interpretable
exposure scores, density classes, and high-exposure alert flags.
"""

import numpy as np
import pandas as pd

def extract_v2_population_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives population exposure score (0-100), density classifications,
    pressure indicators, and high-exposure threshold flags.
    """
    pop_at = df["population_at_event"].values.astype(np.float32)
    pop_1k = df["population_1km"].values.astype(np.float32)
    pop_5k = df["population_5km"].values.astype(np.float32)
    dens_1k = df["population_density_1km"].values.astype(np.float32)
    dens_5k = df["population_density_5km"].values.astype(np.float32)

    # 1. Population Exposure Score (0.0 to 100.0)
    # Log-linear scaling combining immediate 1km density and regional 5km population
    # 500 persons/km2 corresponds to dense Indian agricultural/semi-urban plains
    score_1k = np.clip(dens_1k / 10.0, 0.0, 70.0)
    score_5k = np.clip(pop_5k / 1000.0, 0.0, 30.0)
    exposure_score = np.clip(score_1k + score_5k, 0.0, 100.0).astype(np.float32)

    # 2. High Exposure Flag (dens_1k >= 500 persons/km2 or pop_5k >= 50,000)
    high_exposure_flag = (dens_1k >= 500.0) | (pop_5k >= 50000.0)

    # 3. Density Classification
    conditions = [
        dens_1k < 1.0,
        (dens_1k >= 1.0) & (dens_1k < 50.0),
        (dens_1k >= 50.0) & (dens_1k < 300.0),
        (dens_1k >= 300.0) & (dens_1k < 1000.0),
        dens_1k >= 1000.0
    ]
    choices = ["UNINHABITED", "SPARSE_RURAL", "MODERATE_RURAL", "SEMI_URBAN", "URBAN_DENSE"]
    density_class = pd.Series(np.select(conditions, choices, default="UNINHABITED"), index=df.index, dtype="string")

    # 4. Population Pressure Indicator [0.0 - 1.0]
    pressure = np.clip(np.log1p(pop_1k) / 10.0, 0.0, 1.0).astype(np.float32)

    return pd.DataFrame({
        "population_exposure_score": exposure_score,
        "high_population_exposure_flag": high_exposure_flag,
        "population_density_class": density_class,
        "population_pressure_indicator": pressure
    }, index=df.index)
