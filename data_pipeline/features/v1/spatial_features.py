"""
ThermoTrace Spatial Feature Utilities & Proximity Calculators
============================================================

Vectorized spatial index utilities and geodesic distance calculations
between thermal event clusters and spatial features (facilities,
infrastructure networks, protected area boundaries).
"""

import numpy as np
from scipy.spatial import cKDTree

EARTH_RADIUS_KM = 6371.0088

def haversine_distance_matrix_km(lats1: np.ndarray, lons1: np.ndarray, lats2: np.ndarray, lons2: np.ndarray) -> np.ndarray:
    """Computes vectorized pairwise Haversine distances in km."""
    lat1, lon1 = np.radians(lats1), np.radians(lons1)
    lat2, lon2 = np.radians(lats2), np.radians(lons2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2.0 * np.arcsin(np.clip(np.sqrt(a), 0.0, 1.0))
    return EARTH_RADIUS_KM * c

def latlon_to_cartesian_unit(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Converts (lat, lon) in degrees to 3D Cartesian unit vectors (x, y, z) on Earth sphere."""
    phi = np.radians(lats)
    theta = np.radians(lons)
    x = np.cos(phi) * np.cos(theta)
    y = np.cos(phi) * np.sin(theta)
    z = np.sin(phi)
    return np.column_stack((x, y, z))

class SphericalSpatialIndex:
    """High-performance 3D Cartesian KD-Tree for spherical nearest-neighbor queries."""
    def __init__(self, lats: np.ndarray, lons: np.ndarray, payload: np.ndarray = None):
        self.coords_3d = latlon_to_cartesian_unit(lats, lons)
        self.tree = cKDTree(self.coords_3d)
        self.payload = payload
        self.size = len(lats)

    def query_nearest(self, query_lats: np.ndarray, query_lons: np.ndarray):
        """Returns (distances_km, nearest_indices)."""
        q_3d = latlon_to_cartesian_unit(query_lats, query_lons)
        chord_dists, indices = self.tree.query(q_3d, k=1)
        # Convert chord distance on unit sphere to great-circle arc length in km
        # chord = 2 * sin(theta/2) => theta = 2 * arcsin(chord / 2)
        chord_dists = np.clip(chord_dists / 2.0, 0.0, 1.0)
        arc_angles = 2.0 * np.arcsin(chord_dists)
        dists_km = EARTH_RADIUS_KM * arc_angles
        return dists_km.astype(np.float32), indices

    def query_radius_flag(self, query_lats: np.ndarray, query_lons: np.ndarray, radius_km: float) -> np.ndarray:
        """Returns boolean array indicating if any indexed point is within radius_km."""
        q_3d = latlon_to_cartesian_unit(query_lats, query_lons)
        # Convert radius_km to unit chord distance: chord = 2 * sin( (r/R) / 2 )
        arc_rad = radius_km / EARTH_RADIUS_KM
        chord_rad = 2.0 * np.sin(arc_rad / 2.0)
        counts = self.tree.query_ball_point(q_3d, r=chord_rad, return_length=True)
        return counts > 0
