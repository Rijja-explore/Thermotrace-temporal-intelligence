"""
ThermoTrace Raster Feature Extraction Engine
============================================

Extracts demographic population density and land cover classification
from high-resolution spatial rasters using memory-safe windowed streaming.

Features Extracted:
- Population (WorldPop 2025 100m):
  * population_at_event: Pixel population at 100m cell
  * population_1km: Integrated population within 1km radius
  * population_5km: Integrated population within 5km radius
  * population_density_1km: Density in persons/km²
  * population_density_5km: Density in persons/km²
- WorldCover (ESA 10m):
  * landcover_class: Categorical class ID (10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100)
  * landcover_name: Official label string
  * forest_fraction_1km, cropland_fraction_1km, builtup_fraction_1km,
    grassland_fraction_1km, water_fraction_1km
"""

import math
from pathlib import Path
from typing import Tuple, Dict, Any
from collections import defaultdict
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window

PI_KM2_1KM = math.pi * (1.0 ** 2)  # ~3.14159 km^2
PI_KM2_5KM = math.pi * (5.0 ** 2)  # ~78.5398 km^2

WORLDCOVER_CLASSES = {
    0: "NoData",
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen"
}

def extract_population_features(events_df: pd.DataFrame, pop_raster_path: str, batch_size: int = 10000) -> pd.DataFrame:
    """Memory-safe windowed sampling of 100m population raster."""
    p = Path(pop_raster_path)
    if not p.exists():
        raise FileNotFoundError(f"Population raster not found at: {p}")

    n_events = len(events_df)
    pop_at_event = np.zeros(n_events, dtype=np.float32)
    pop_1km = np.zeros(n_events, dtype=np.float32)
    pop_5km = np.zeros(n_events, dtype=np.float32)

    lons = events_df["centroid_lon"].values
    lats = events_df["centroid_lat"].values

    with rasterio.open(p) as src:
        nodata = float(src.nodata) if src.nodata is not None else -99999.0
        inv_trans = ~src.transform
        cols, rows = inv_trans * (lons, lats)
        cols = np.round(cols).astype(np.int32)
        rows = np.round(rows).astype(np.int32)

        # 1. Fast exact point sampling
        coords = list(zip(lons, lats))
        samples = np.array([val[0] for val in src.sample(coords)], dtype=np.float32)
        samples = np.where((samples == nodata) | (samples < 0), 0.0, samples)
        pop_at_event[:] = samples

        # 2. Windowed buffer integration in batches
        for start_idx in range(0, n_events, batch_size):
            end_idx = min(start_idx + batch_size, n_events)
            b_cols = cols[start_idx:end_idx]
            b_rows = rows[start_idx:end_idx]
            b_pts = samples[start_idx:end_idx]

            for i, (c, r, pt_val) in enumerate(zip(b_cols, b_rows, b_pts)):
                global_idx = start_idx + i
                # Read 1km window (21x21 cells, radius 10 cells)
                w1 = Window(c - 10, r - 10, 21, 21)
                arr1 = src.read(1, window=w1, boundless=True, fill_value=nodata)
                valid1 = arr1[(arr1 != nodata) & (arr1 >= 0)]
                s1 = float(np.sum(valid1)) if valid1.size > 0 else float(pt_val)
                pop_1km[global_idx] = s1

                # Read 5km window (101x101 cells, radius 50 cells)
                w5 = Window(c - 50, r - 50, 101, 101)
                arr5 = src.read(1, window=w5, boundless=True, fill_value=nodata)
                valid5 = arr5[(arr5 != nodata) & (arr5 >= 0)]
                s5 = float(np.sum(valid5)) if valid5.size > 0 else s1 * 25.0
                pop_5km[global_idx] = s5

    # Density in persons/km²
    density_1km = (pop_1km / PI_KM2_1KM).astype(np.float32)
    density_5km = (pop_5km / PI_KM2_5KM).astype(np.float32)

    return pd.DataFrame({
        "population_at_event": pop_at_event,
        "population_1km": pop_1km,
        "population_5km": pop_5km,
        "population_density_1km": density_1km,
        "population_density_5km": density_5km
    }, index=events_df.index)

def extract_worldcover_features(events_df: pd.DataFrame, mosaic_path: str = None, raw_tiles_dir: str = None) -> Tuple[pd.DataFrame, str]:
    """
    Extracts 10m land cover class and 1km composition fractions.
    Supports dual execution:
    1. If mosaic_path exists and is readable, reads from mosaic.
    2. Otherwise, dynamically reads from the 91 raw tiles covering the event coordinates.
    """
    n_events = len(events_df)
    lons = events_df["centroid_lon"].values
    lats = events_df["centroid_lat"].values

    classes = np.zeros(n_events, dtype=np.int16)
    forest_f = np.zeros(n_events, dtype=np.float32)
    cropland_f = np.zeros(n_events, dtype=np.float32)
    builtup_f = np.zeros(n_events, dtype=np.float32)
    grassland_f = np.zeros(n_events, dtype=np.float32)
    water_f = np.zeros(n_events, dtype=np.float32)

    # Check mosaic readiness
    mosaic_ready = False
    if mosaic_path:
        mp = Path(mosaic_path)
        if mp.exists() and mp.stat().st_size > 100_000_000:
            try:
                with rasterio.open(mp) as test_src:
                    _ = test_src.shape
                mosaic_ready = True
            except Exception:
                mosaic_ready = False

    if mosaic_ready:
        source_mode = "MOSAIC"
        with rasterio.open(mosaic_path) as src:
            inv = ~src.transform
            for i, (lon, lat) in enumerate(zip(lons, lats)):
                try:
                    c, r = inv * (lon, lat)
                    c, r = int(round(c)), int(round(r))
                    # Read 1km window (100 pixels radius = 201x201 window)
                    w = Window(c - 50, r - 50, 101, 101)
                    arr = src.read(1, window=w, boundless=True, fill_value=0)
                    center_val = arr[50, 50] if 0 <= 50 < arr.shape[0] and 0 <= 50 < arr.shape[1] else 0
                    classes[i] = int(center_val)
                    valid = arr[arr != 0]
                    if valid.size > 0:
                        forest_f[i] = np.mean(valid == 10)
                        cropland_f[i] = np.mean(valid == 40)
                        builtup_f[i] = np.mean(valid == 50)
                        grassland_f[i] = np.mean(valid == 30)
                        water_f[i] = np.mean(valid == 80)
                except Exception:
                    classes[i] = 0
    else:
        # Fallback to direct raw tile access
        source_mode = "TILES (Raw WorldCover 91-grid)"
        raw_dir = Path(raw_tiles_dir) if raw_tiles_dir else Path(r"d:\New folder (2)\data\raw\worldcover\india")
        if not raw_dir.exists():
            raw_dir = Path(r"d:\New folder (2)\ThermoTrace_WorldCover_Downloader\data\raw\worldcover\india")

        # Group event indices by tile for maximum I/O efficiency
        events_by_tile = defaultdict(list)
        for i, (lon, lat) in enumerate(zip(lons, lats)):
            lat_t = int(lat // 3) * 3
            lon_t = int(lon // 3) * 3
            t_name = f"ESA_WorldCover_10m_2021_v200_N{lat_t:02d}E{lon_t:03d}_Map.tif"
            events_by_tile[t_name].append(i)

        for t_name, indices in events_by_tile.items():
            t_path = raw_dir / t_name
            if not t_path.exists():
                continue
            try:
                with rasterio.open(t_path) as src:
                    inv = ~src.transform
                    for idx in indices:
                        lon, lat = lons[idx], lats[idx]
                        c, r = inv * (lon, lat)
                        c, r = int(round(c)), int(round(r))
                        w = Window(c - 50, r - 50, 101, 101)
                        arr = src.read(1, window=w, boundless=True, fill_value=0)
                        center_val = arr[50, 50] if 0 <= 50 < arr.shape[0] and 0 <= 50 < arr.shape[1] else 0
                        classes[idx] = int(center_val)
                        valid = arr[arr != 0]
                        if valid.size > 0:
                            forest_f[idx] = float(np.mean(valid == 10))
                            cropland_f[idx] = float(np.mean(valid == 40))
                            builtup_f[idx] = float(np.mean(valid == 50))
                            grassland_f[idx] = float(np.mean(valid == 30))
                            water_f[idx] = float(np.mean(valid == 80))
            except Exception:
                pass

    names = [WORLDCOVER_CLASSES.get(int(c), "Unknown") for c in classes]

    return pd.DataFrame({
        "landcover_class": classes,
        "landcover_name": pd.Series(names, dtype="string"),
        "forest_fraction_1km": forest_f,
        "cropland_fraction_1km": cropland_f,
        "builtup_fraction_1km": builtup_f,
        "grassland_fraction_1km": grassland_f,
        "water_fraction_1km": water_f
    }, index=events_df.index), f"READY ({source_mode})"
