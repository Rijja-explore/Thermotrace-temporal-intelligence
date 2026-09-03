"""
ThermoTrace Temporal Feature Derivation Engine
==============================================

Extracts astronomical, calendar, and meteorological seasonal features
from M3 thermal event cluster timestamps without altering original values.
"""

import pandas as pd
import numpy as np

def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derives temporal features from event start_time and day/night detection counts."""
    # Parse timestamps vectorized
    dt = pd.to_datetime(df["start_time"])

    year = dt.dt.year.astype(np.int16)
    month = dt.dt.month.astype(np.int8)
    day = dt.dt.day.astype(np.int8)
    day_of_week = dt.dt.dayofweek.astype(np.int8)
    hour = dt.dt.hour.astype(np.int8)
    is_weekend = (day_of_week >= 5)

    # Standard Indian Meteorological Department (IMD) Seasonality:
    # - Winter: Dec - Feb (12, 1, 2)
    # - Pre-Monsoon / Summer: Mar - May (3, 4, 5)
    # - Monsoon / Southwest Monsoon: Jun - Sep (6, 7, 8, 9)
    # - Post-Monsoon / Autumn: Oct - Nov (10, 11)
    season_conditions = [
        month.isin([12, 1, 2]),
        month.isin([3, 4, 5]),
        month.isin([6, 7, 8, 9]),
        month.isin([10, 11])
    ]
    season_choices = ["WINTER", "PRE_MONSOON", "MONSOON", "POST_MONSOON"]
    season = np.select(season_conditions, season_choices, default="UNKNOWN")

    # Day / Night derivation
    # Uses satellite observation flags when available, falling back to UTC/IST solar calculation
    if "day_detection_count" in df.columns and "night_detection_count" in df.columns:
        is_day = df["day_detection_count"] >= df["night_detection_count"]
        is_night = ~is_day
    else:
        # Fallback to local solar hour in India (UTC + 5:30)
        local_hour = (hour + 5.5) % 24
        is_day = (local_hour >= 6.0) & (local_hour < 18.0)
        is_night = ~is_day

    return pd.DataFrame({
        "year": year,
        "month": month,
        "day": day,
        "day_of_week": day_of_week,
        "hour": hour,
        "season": season,
        "is_day": is_day.astype(bool),
        "is_night": is_night.astype(bool),
        "is_weekend": is_weekend.astype(bool)
    }, index=df.index)
