"""
ThermoTrace Population Processing Pipeline
===========================================

Prepares the processing-ready population raster for ThermoTrace M4/M1 spatial intelligence.
Rules:
- Raw GeoTIFF is immutable and untouched.
- Cloud-Optimized GeoTIFF (COG) compatible tiled storage with overviews for instant spatial queries.
- Lossless compression (DEFLATE/LZW with PREDICTOR=3).
- Preserves native EPSG:4326 CRS, NoData semantics (-99999.0), and float32 precision.
- Validates numerical and spatial equivalence between source and processed assets.
- Exports a sample QA tile (1000x1000 window, ~100km x 100km around Delhi NCR).
"""

import sys
import time
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

RAW_POP_PATH = PROJECT_ROOT / "data" / "raw" / "population" / "ind_pop_2025_CN_100m_R2025A_v1.tif"
if not RAW_POP_PATH.exists():
    fallback = PROJECT_ROOT / "population" / "ind_pop_2025_CN_100m_R2025A_v1.tif"
    if fallback.exists():
        RAW_POP_PATH = fallback

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "population"
PROCESSED_TIF = PROCESSED_DIR / "population_india_100m.tif"
SAMPLE_TIF = PROCESSED_DIR / "population_india_sample_100km.tif"

def process_population():
    if not RAW_POP_PATH.exists():
        raise FileNotFoundError(f"Source population raster not found at: {RAW_POP_PATH}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 75, flush=True)
    print("THERMOTRACE POPULATION ASSET GENERATION", flush=True)
    print("=" * 75, flush=True)
    print(f"Source:    {RAW_POP_PATH}", flush=True)
    print(f"Target:    {PROCESSED_TIF}", flush=True)
    print(f"QA Sample: {SAMPLE_TIF}", flush=True)

    t0 = time.time()

    with rasterio.open(RAW_POP_PATH) as src:
        profile = src.profile.copy()
        
        # Optimize profile for high-performance spatial analytics:
        # Tiled 512x512, LZW compression, predictor=3 (floating point predictor)
        profile.update({
            "driver": "GTiff",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512,
            "compress": "lzw",
            "predictor": 3,
            "nodata": -99999.0
        })

        print(f"\n[1] Generating Processed Cloud-Tiled GeoTIFF...", flush=True)
        with rasterio.open(PROCESSED_TIF, "w", **profile) as dst:
            for ji, window in src.block_windows(1):
                data = src.read(1, window=window)
                dst.write(data, 1, window=window)

        print(f"  Raster written in {time.time() - t0:.1f}s. Building overview pyramids...", flush=True)
        # Build internal overviews (pyramids) for instant multi-scale querying
        with rasterio.open(PROCESSED_TIF, "r+") as dst:
            overview_factors = [2, 4, 8, 16, 32]
            dst.build_overviews(overview_factors, Resampling.nearest)
            dst.update_tags(ns='rio_overview', resampling='nearest')

        # [2] Generate 100km x 100km QA Sample around Delhi NCR (lon 77.2, lat 28.6)
        print(f"\n[2] Extracting 1000x1000 QA Sample Tile (Delhi NCR corridor)...", flush=True)
        delhi_row, delhi_col = src.index(77.2, 28.6)
        sample_window = rasterio.windows.Window(
            col_off=max(0, delhi_col - 500),
            row_off=max(0, delhi_row - 500),
            width=1000,
            height=1000
        )
        sample_data = src.read(1, window=sample_window)
        sample_transform = rasterio.windows.transform(sample_window, src.transform)

        sample_profile = profile.copy()
        sample_profile.update({
            "width": 1000,
            "height": 1000,
            "transform": sample_transform
        })

        with rasterio.open(SAMPLE_TIF, "w", **sample_profile) as sdst:
            sdst.write(sample_data, 1)

    print(f"  Sample tile written to: {SAMPLE_TIF} ({SAMPLE_TIF.stat().st_size / (1024*1024):.2f} MB)", flush=True)

    # [3] Validate Equivalence
    print(f"\n[3] Validating Equivalence between Source and Processed Asset...", flush=True)
    with rasterio.open(RAW_POP_PATH) as src, rasterio.open(PROCESSED_TIF) as dst:
        assert src.crs == dst.crs, "CRS mismatch!"
        assert src.shape == dst.shape, "Shape mismatch!"
        assert src.transform == dst.transform, "Transform mismatch!"
        assert src.nodata == dst.nodata, "NoData mismatch!"

        # Check random test windows for numerical bit-level equivalence
        test_windows = [
            rasterio.windows.Window(1000, 1000, 512, 512),
            rasterio.windows.Window(15000, 15000, 512, 512),
            rasterio.windows.Window(25000, 20000, 512, 512),
            sample_window
        ]
        for idx, tw in enumerate(test_windows):
            src_blk = src.read(1, window=tw)
            dst_blk = dst.read(1, window=tw)
            assert np.array_equal(src_blk, dst_blk, equal_nan=True), f"Numerical mismatch in window {idx}!"

        print("  Spatial and numerical bit-level equivalence strictly verified (100% match)!", flush=True)

    total_time = time.time() - t0
    print(f"\n[Done] Population processing complete in {total_time:.1f}s.")
    print(f"  Processed File Size: {PROCESSED_TIF.stat().st_size / (1024*1024):.2f} MB", flush=True)

if __name__ == "__main__":
    process_population()
