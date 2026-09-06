"""
ThermoTrace Protected Area Feature Extraction Engine
=====================================================

Performs spatial containment and geodesic proximity analysis between
thermal event clusters and the canonical India Protected Area (WDPA) network.

Features Extracted:
- inside_protected_area: Boolean containment flag
- protected_area_id: WDPA Site ID
- protected_area_name: Official English name
- protected_area_designation: National Park, Wildlife Sanctuary, Ramsar, etc.
- distance_to_protected_area_km: Distance to closest protected area boundary
- protected_area_within_1km: Binary proximity flag
- protected_area_within_5km: Binary proximity flag
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pyogrio
from shapely.geometry import Point, MultiPolygon, Polygon
from shapely.strtree import STRtree
from .spatial_features import haversine_distance_matrix_km, SphericalSpatialIndex

def extract_protected_area_features(events_df: pd.DataFrame, pa_gpkg_path: str) -> pd.DataFrame:
    """Computes spatial containment and proximity to India protected areas."""
    p = Path(pa_gpkg_path)
    if not p.exists():
        raise FileNotFoundError(f"Protected areas GeoPackage not found at: {p}")

    n_events = len(events_df)
    ev_lons = events_df["centroid_lon"].values
    ev_lats = events_df["centroid_lat"].values

    # Load canonical polygon boundaries
    polys_df = pyogrio.read_dataframe(str(p), layer="protected_areas_polygons")
    
    # 1. Point-in-polygon containment using STRtree
    geoms = polys_df.geometry.values
    tree = STRtree(geoms)

    # Vectorized Point creation
    pts = [Point(x, y) for x, y in zip(ev_lons, ev_lats)]
    
    inside_flags = np.zeros(n_events, dtype=bool)
    pa_ids = np.array([None] * n_events, dtype=object)
    pa_names = np.array([None] * n_events, dtype=object)
    pa_desigs = np.array([None] * n_events, dtype=object)

    # Query candidate intersections
    res = tree.query(pts, predicate="intersects")
    pt_indices, poly_indices = res[0], res[1]

    for pt_idx, poly_idx in zip(pt_indices, poly_indices):
        inside_flags[pt_idx] = True
        pa_ids[pt_idx] = str(polys_df.iloc[poly_idx]["SITE_ID"])
        pa_names[pt_idx] = str(polys_df.iloc[poly_idx]["NAME_ENG"])
        pa_desigs[pt_idx] = str(polys_df.iloc[poly_idx]["DESIG_ENG"])

    # 2. Distance to nearest protected area
    # Use representative centroids from combined layer for fast global spherical distance
    comb_df = pyogrio.read_dataframe(str(p), layer="protected_areas_combined")
    pa_lats = comb_df["rep_lat"].values
    pa_lons = comb_df["rep_lon"].values

    spatial_idx = SphericalSpatialIndex(pa_lats, pa_lons)
    dists_km, nearest_indices = spatial_idx.query_nearest(ev_lats, ev_lons)

    # For points inside protected area, distance to boundary is 0.0
    dists_km = np.where(inside_flags, 0.0, dists_km).astype(np.float32)

    # Assign nearest PA metadata for close events if not already inside
    for i in range(n_events):
        if pa_ids[i] is None:
            near_idx = nearest_indices[i]
            pa_ids[i] = str(comb_df.iloc[near_idx]["SITE_ID"])
            pa_names[i] = str(comb_df.iloc[near_idx]["NAME_ENG"])
            pa_desigs[i] = str(comb_df.iloc[near_idx]["DESIG_ENG"])

    return pd.DataFrame({
        "inside_protected_area": inside_flags,
        "protected_area_id": pd.Series(pa_ids, dtype="string"),
        "protected_area_name": pd.Series(pa_names, dtype="string"),
        "protected_area_designation": pd.Series(pa_desigs, dtype="string"),
        "distance_to_protected_area_km": dists_km,
        "protected_area_within_1km": dists_km <= 1.0,
        "protected_area_within_5km": dists_km <= 5.0
    }, index=events_df.index)
