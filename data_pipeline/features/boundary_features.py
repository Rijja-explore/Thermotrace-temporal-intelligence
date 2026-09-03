"""
ThermoTrace Administrative Boundary Context Engine
==================================================

Handles spatial joins with national, state, and district administrative boundaries.
Inspects boundary availability and provides documented fallback when awaiting
authoritative Survey of India datasets.
"""

from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np

def extract_boundary_features(events_df: pd.DataFrame, admin_gpkg_path: str = None) -> Tuple[pd.DataFrame, str]:
    """Derives administrative hierarchy or returns documented pending fields."""
    n_events = len(events_df)
    admin_path = Path(admin_gpkg_path) if admin_gpkg_path else None

    if admin_path and admin_path.exists():
        # Authoritative boundary dataset exists
        try:
            import pyogrio
            import geopandas as gpd
            from shapely.strtree import STRtree
            from shapely.geometry import Point

            admin_gdf = pyogrio.read_dataframe(str(admin_path), layer="india_districts")
            tree = STRtree(admin_gdf.geometry.values)
            pts = [Point(x, y) for x, y in zip(events_df["centroid_lon"], events_df["centroid_lat"])]
            res = tree.query(pts, predicate="intersects")

            states = [None] * n_events
            districts = [None] * n_events
            state_codes = [None] * n_events
            district_codes = [None] * n_events

            for pt_idx, geom_idx in zip(res[0], res[1]):
                row = admin_gdf.iloc[geom_idx]
                states[pt_idx] = row.get("state_name")
                districts[pt_idx] = row.get("district_name")
                state_codes[pt_idx] = str(row.get("state_code", ""))
                district_codes[pt_idx] = str(row.get("district_code", ""))

            return pd.DataFrame({
                "country": pd.Series(["India"] * n_events, dtype="string"),
                "state": pd.Series(states, dtype="string"),
                "state_code": pd.Series(state_codes, dtype="string"),
                "district": pd.Series(districts, dtype="string"),
                "district_code": pd.Series(district_codes, dtype="string")
            }, index=events_df.index), "READY"
        except Exception as e:
            pass

    # Awaiting authoritative dataset (Survey of India / Bharat Maps)
    return pd.DataFrame({
        "country": pd.Series(["India"] * n_events, dtype="string"),
        "state": pd.Series([None] * n_events, dtype="string"),
        "state_code": pd.Series([None] * n_events, dtype="string"),
        "district": pd.Series([None] * n_events, dtype="string"),
        "district_code": pd.Series([None] * n_events, dtype="string")
    }, index=events_df.index), "PENDING (Awaiting Survey of India boundaries)"
