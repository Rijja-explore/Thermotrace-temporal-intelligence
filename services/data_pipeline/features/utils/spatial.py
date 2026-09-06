"""
ThermoTrace Spatial Math Utilities
==================================

Vectorized spherical distance calculations and spatial grid binning.
"""

import numpy as np

EARTH_RADIUS_KM = 6371.0088

def haversine_vectorized(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Computes great-circle distances in kilometers between coordinate pairs."""
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = (np.sin(delta_phi / 2.0) ** 2 +
         np.cos(phi1) * np.cos(phi2) * (np.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * np.arcsin(np.clip(np.sqrt(a), 0.0, 1.0))
    return (EARTH_RADIUS_KM * c).astype(np.float32)

def compute_grid_cell(lats: np.ndarray, lons: np.ndarray, cell_size_deg: float = 0.05) -> np.ndarray:
    """
    Computes a deterministic discrete integer spatial grid cell ID.
    0.05 degrees ~ 5.5 km.
    """
    grid_y = np.floor(lats / cell_size_deg).astype(np.int32)
    grid_x = np.floor(lons / cell_size_deg).astype(np.int32)
    return (grid_y.astype(np.int64) << 32) | (grid_x.astype(np.int64) & 0xFFFFFFFF)
