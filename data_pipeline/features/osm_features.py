"""
ThermoTrace OSM Industrial & Infrastructure Proximity Engine
============================================================

Extracts industrial contextual associations and infrastructure distances
from canonical layers in data/processed/osm/osm_india.gpkg.

IMPORTANT METHODOLOGICAL SAFEGUARDS:
- Representative coordinates (rep_lon, rep_lat) are geometric centroids for
  spatial index matching, NOT exact thermal vent / chimney locations.
- Proximity indicates spatial association only, not legal factory attribution.
"""

from pathlib import Path
from typing import Dict
import numpy as np
import pandas as pd
import pyogrio
from .spatial_features import SphericalSpatialIndex

def extract_osm_features(events_df: pd.DataFrame, osm_gpkg_path: str) -> pd.DataFrame:
    """Computes nearest industrial facility and infrastructure proximity metrics."""
    p = Path(osm_gpkg_path)
    if not p.exists():
        raise FileNotFoundError(f"OSM GeoPackage not found at: {p}")

    n_events = len(events_df)
    ev_lats = events_df["centroid_lat"].values
    ev_lons = events_df["centroid_lon"].values

    # 1. Load Facilities
    fac_df = pyogrio.read_dataframe(
        str(p),
        layer="osm_facilities",
        columns=["osm_id", "name", "facility_category", "rep_lon", "rep_lat"]
    )

    fac_lats = fac_df["rep_lat"].values.astype(np.float64)
    fac_lons = fac_df["rep_lon"].values.astype(np.float64)
    fac_ids = fac_df["osm_id"].values
    fac_cats = fac_df["facility_category"].values
    fac_names = fac_df["name"].fillna("").values

    # Global nearest facility query
    global_fac_index = SphericalSpatialIndex(fac_lats, fac_lons)
    dist_facility_km, near_fac_idx = global_fac_index.query_nearest(ev_lats, ev_lons)

    nearest_facility_id = pd.Series(fac_ids[near_fac_idx], dtype="string")
    nearest_facility_type = pd.Series(fac_cats[near_fac_idx], dtype="string")
    nearest_facility_name = pd.Series(np.where(fac_names[near_fac_idx] == "", None, fac_names[near_fac_idx]), dtype="string")

    # Category-specific proximity flags
    def make_proximity_flag(cat_name: str, radius_km: float) -> np.ndarray:
        mask = (fac_cats == cat_name)
        if not np.any(mask):
            return np.zeros(n_events, dtype=bool)
        idx = SphericalSpatialIndex(fac_lats[mask], fac_lons[mask])
        return idx.query_radius_flag(ev_lats, ev_lons, radius_km)

    near_power_plant = make_proximity_flag("POWER_PLANT", 2.0)
    near_factory = make_proximity_flag("FACTORY", 2.0)
    near_refinery = make_proximity_flag("REFINERY", 5.0)
    near_mine = make_proximity_flag("MINE", 5.0)
    near_quarry = make_proximity_flag("QUARRY", 3.0)
    near_storage_facility = make_proximity_flag("STORAGE_FACILITY", 2.0)
    near_substation = make_proximity_flag("SUBSTATION", 2.0)

    # 2. Infrastructure Distances
    # Read infrastructure categories
    inf_df = pyogrio.read_dataframe(
        str(p),
        layer="osm_infrastructure",
        columns=["osm_id", "infrastructure_category"]
    )

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        inf_centroids = inf_df.geometry.centroid
    inf_lats = inf_centroids.y.values.astype(np.float64)
    inf_lons = inf_centroids.x.values.astype(np.float64)
    inf_cats = inf_df["infrastructure_category"].values

    def compute_infra_distance(cat_name: str) -> np.ndarray:
        mask = (inf_cats == cat_name)
        if not np.any(mask):
            return np.full(n_events, 999.0, dtype=np.float32)
        idx = SphericalSpatialIndex(inf_lats[mask], inf_lons[mask])
        dists, _ = idx.query_nearest(ev_lats, ev_lons)
        return dists.astype(np.float32)

    dist_major_road = compute_infra_distance("MAJOR_ROAD")
    dist_railway = compute_infra_distance("RAILWAY")
    dist_power_line = compute_infra_distance("POWER_LINE")
    dist_pipeline = compute_infra_distance("PIPELINE")
    dist_airport = compute_infra_distance("AIRPORT")
    dist_port = compute_infra_distance("PORT")

    return pd.DataFrame({
        "nearest_facility_id": nearest_facility_id,
        "nearest_facility_type": nearest_facility_type,
        "nearest_facility_name": nearest_facility_name,
        "distance_to_facility_km": dist_facility_km,
        "near_power_plant": near_power_plant,
        "near_factory": near_factory,
        "near_refinery": near_refinery,
        "near_mine": near_mine,
        "near_quarry": near_quarry,
        "near_storage_facility": near_storage_facility,
        "near_substation": near_substation,
        "distance_to_major_road_km": dist_major_road,
        "distance_to_railway_km": dist_railway,
        "distance_to_power_line_km": dist_power_line,
        "distance_to_pipeline_km": dist_pipeline,
        "distance_to_airport_km": dist_airport,
        "distance_to_port_km": dist_port
    }, index=events_df.index)
