"""
ThermoTrace Feature Engineering V2: Spatial Thermal Density Features
====================================================================

Computes multi-scale spatial event density and local clustering metrics
across 1km, 5km, and 10km fixed geographic grid resolutions.
"""

import numpy as np
import pandas as pd

PI_KM2_1KM = np.pi * (1.0 ** 2)
PI_KM2_5KM = np.pi * (5.0 ** 2)
PI_KM2_10KM = np.pi * (10.0 ** 2)

def extract_v2_spatial_density_features(df: pd.DataFrame, rec_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Computes static spatial clustering counts and historical 7d/30d local activity.
    Uses discrete fixed grid binning (~0.01 deg, ~0.05 deg, ~0.10 deg).
    """
    lats = df["centroid_lat"].values.astype(np.float64)
    lons = df["centroid_lon"].values.astype(np.float64)

    # 1. Grid cell keys
    # 0.01 deg ~ 1.1 km
    c1 = (np.floor(lats / 0.01).astype(np.int64) << 32) | (np.floor(lons / 0.01).astype(np.int64) & 0xFFFFFFFF)
    # 0.05 deg ~ 5.5 km
    c5 = (np.floor(lats / 0.05).astype(np.int64) << 32) | (np.floor(lons / 0.05).astype(np.int64) & 0xFFFFFFFF)
    # 0.10 deg ~ 11 km
    c10 = (np.floor(lats / 0.10).astype(np.int64) << 32) | (np.floor(lons / 0.10).astype(np.int64) & 0xFFFFFFFF)

    s1 = pd.Series(c1)
    s5 = pd.Series(c5)
    s10 = pd.Series(c10)

    events_1km = s1.map(s1.value_counts()).values.astype(np.int32)
    events_5km = s5.map(s5.value_counts()).values.astype(np.int32)
    events_10km = s10.map(s10.value_counts()).values.astype(np.int32)

    density_1km = (events_1km / PI_KM2_1KM).astype(np.float32)
    density_5km = (events_5km / PI_KM2_5KM).astype(np.float32)
    density_10km = (events_10km / PI_KM2_10KM).astype(np.float32)

    # Recent historical local density
    if rec_df is not None and "events_previous_7d" in rec_df.columns:
        ev_loc_7d = rec_df["events_previous_7d"].values.astype(np.int32)
        ev_loc_30d = rec_df["events_previous_30d"].values.astype(np.int32)
    else:
        ev_loc_7d = np.zeros(len(df), dtype=np.int32)
        ev_loc_30d = np.zeros(len(df), dtype=np.int32)

    return pd.DataFrame({
        "events_local_1km": events_1km,
        "events_local_5km": events_5km,
        "events_local_10km": events_10km,
        "thermal_density_1km": density_1km,
        "thermal_density_5km": density_5km,
        "thermal_density_10km": density_10km,
        "events_local_7d": ev_loc_7d,
        "events_local_30d": ev_loc_30d
    }, index=df.index)
