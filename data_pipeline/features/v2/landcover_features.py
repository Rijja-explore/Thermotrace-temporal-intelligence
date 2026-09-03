"""
ThermoTrace Feature Engineering V2: Land-Cover & Environmental Sensitivity Features
==================================================================================

Computes domain-specific environmental vulnerability scores and natural vegetation fractions
derived from ESA WorldCover 10m land cover composition metrics.
"""

import numpy as np
import pandas as pd

def extract_v2_landcover_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives exposure scores for forest, cropland, built-up, and grassland,
    natural vegetation fraction, and overall environmental sensitivity score (0-100).
    """
    f_forest = df["forest_fraction_1km"].values.astype(np.float32)
    f_crop = df["cropland_fraction_1km"].values.astype(np.float32)
    f_built = df["builtup_fraction_1km"].values.astype(np.float32)
    f_grass = df["grassland_fraction_1km"].values.astype(np.float32)

    # 1. Individual Landcover Exposure Scores [0.0 - 100.0]
    forest_exp = (f_forest * 100.0).astype(np.float32)
    crop_exp = (f_crop * 100.0).astype(np.float32)
    built_exp = (f_built * 100.0).astype(np.float32)
    grass_exp = (f_grass * 100.0).astype(np.float32)

    # 2. Natural Land Fraction (Forest + Grassland)
    natural_frac = np.clip(f_forest + f_grass, 0.0, 1.0).astype(np.float32)

    # 3. Environmental Sensitivity Score (0.0 to 100.0)
    # Reflects flammable biomass and ecological sensitivity
    env_sensitivity = np.clip(
        0.70 * forest_exp + 0.20 * grass_exp + 0.10 * crop_exp,
        0.0, 100.0
    ).astype(np.float32)

    return pd.DataFrame({
        "forest_exposure_score": forest_exp,
        "cropland_exposure_score": crop_exp,
        "builtup_exposure_score": built_exp,
        "grassland_exposure_score": grass_exp,
        "natural_land_fraction": natural_frac,
        "environmental_sensitivity_score": env_sensitivity
    }, index=df.index)
