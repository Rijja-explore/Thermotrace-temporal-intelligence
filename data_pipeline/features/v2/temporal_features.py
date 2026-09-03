"""
ThermoTrace Feature Engineering V2: Temporal Cyclical Features
==============================================================

Extracts continuous sinusoidal cyclical encodings for diurnal, seasonal,
and weekly cycles, enabling machine learning models to respect circular time.
"""

import numpy as np
import pandas as pd

def extract_v2_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives sine and cosine cyclical encodings for hour, month, and day of week.
    Bounded strictly in [-1.0, 1.0].
    """
    hour = df["hour"].values.astype(np.float32)
    month = df["month"].values.astype(np.float32)
    day_of_week = df["day_of_week"].values.astype(np.float32)

    # 24-hour diurnal cycle
    hour_sin = np.sin(2.0 * np.pi * hour / 24.0).astype(np.float32)
    hour_cos = np.cos(2.0 * np.pi * hour / 24.0).astype(np.float32)

    # 12-month annual cycle (0-indexed month)
    month_sin = np.sin(2.0 * np.pi * (month - 1.0) / 12.0).astype(np.float32)
    month_cos = np.cos(2.0 * np.pi * (month - 1.0) / 12.0).astype(np.float32)

    # 7-day weekly cycle
    dow_sin = np.sin(2.0 * np.pi * day_of_week / 7.0).astype(np.float32)
    dow_cos = np.cos(2.0 * np.pi * day_of_week / 7.0).astype(np.float32)

    return pd.DataFrame({
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "month_sin": month_sin,
        "month_cos": month_cos,
        "day_of_week_sin": dow_sin,
        "day_of_week_cos": dow_cos
    }, index=df.index)
