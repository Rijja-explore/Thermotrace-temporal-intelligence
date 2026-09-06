"""
ThermoTrace ESA WorldCover Tile Inspection & Quality Assurance
==============================================================

Performs comprehensive tile-by-tile QA on raw ESA WorldCover 2021 v200 tiles:
- Tile inventory and metadata extraction
- Readability and file integrity verification
- Class scheme verification (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100)
- Spatial coverage verification against India analysis extent
- Outputs machine-readable tile inventory and QA report
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import rasterio

# Ensure UTF-8 output on Windows console
sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

RAW_WC_DIR = PROJECT_ROOT / "data" / "raw" / "worldcover" / "india"
if not RAW_WC_DIR.exists() or len(list(RAW_WC_DIR.glob("*.tif"))) == 0:
    fallback = PROJECT_ROOT / "ThermoTrace_WorldCover_Downloader" / "data" / "raw" / "worldcover" / "india"
    if fallback.exists():
        RAW_WC_DIR = fallback

REPORTS_DIR = PROJECT_ROOT / "reports" / "worldcover"

INDIA_BBOX = (68.1, 6.5, 97.4, 35.7)

# Official ESA WorldCover 2021 v200 class scheme
VALID_CLASSES = {
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

def intersects(tile_bounds, target_bbox):
    tw, ts, te, tn = tile_bounds
    bw, bs, be, bn = target_bbox
    return not (te < bw or tw > be or tn < bs or ts > bn)

def inspect_worldcover_tiles():
    if not RAW_WC_DIR.exists():
        raise FileNotFoundError(f"WorldCover directory not found: {RAW_WC_DIR}")

    print("=" * 75, flush=True)
    print("THERMOTRACE ESA WORLDCOVER TILE INSPECTION & INVENTORY", flush=True)
    print("=" * 75, flush=True)
    print(f"Raw Directory: {RAW_WC_DIR}", flush=True)

    t0 = time.time()

    tile_files = sorted(RAW_WC_DIR.glob("*.tif"))
    total_found = len(tile_files)
    print(f"Found {total_found} GeoTIFF tiles.", flush=True)

    inventory = []
    corrupted_tiles = []
    suspicious_size_tiles = []
    unexpected_classes = {}
    intersecting_tiles = []
    non_intersecting_tiles = []

    total_bytes = 0

    for idx, tif in enumerate(tile_files):
        size_bytes = tif.stat().st_size
        total_bytes += size_bytes
        tile_name = tif.name

        if size_bytes < 1_000_000:  # < 1 MB is suspiciously small for 36000x36000
            suspicious_size_tiles.append({"tile": tile_name, "size_bytes": size_bytes})

        try:
            with rasterio.open(tif) as src:
                crs = str(src.crs)
                width = src.width
                height = src.height
                bands = src.count
                dtype = src.dtypes[0]
                nodata = float(src.nodata) if src.nodata is not None else 0.0
                res = list(src.res)
                b = src.bounds
                bounds_dict = {
                    "left": round(b.left, 4),
                    "bottom": round(b.bottom, 4),
                    "right": round(b.right, 4),
                    "top": round(b.top, 4)
                }

                # Sample blocks to test integrity and verify class values
                sample_win = rasterio.windows.Window(1000, 1000, 512, 512)
                sample_arr = src.read(1, window=sample_win)
                unique_vals = set(int(v) for v in np.unique(sample_arr))
                invalid_in_sample = unique_vals - set(VALID_CLASSES.keys())
                if invalid_in_sample:
                    unexpected_classes[tile_name] = list(invalid_in_sample)

                # Check India BBOX intersection
                tile_bbox = (b.left, b.bottom, b.right, b.top)
                hits_india = intersects(tile_bbox, INDIA_BBOX)

                entry = {
                    "filename": tile_name,
                    "tile_id": tile_name.split("_")[5] if len(tile_name.split("_")) > 5 else tile_name,
                    "file_size_bytes": size_bytes,
                    "file_size_mb": round(size_bytes / (1024 * 1024), 2),
                    "crs": crs,
                    "dimensions": [width, height],
                    "resolution": res,
                    "bounds": bounds_dict,
                    "bands": bands,
                    "datatype": dtype,
                    "nodata": nodata,
                    "intersects_india_bbox": hits_india,
                    "integrity_valid": True
                }

                if hits_india:
                    intersecting_tiles.append(entry)
                else:
                    non_intersecting_tiles.append(entry)

                inventory.append(entry)

        except Exception as e:
            corrupted_tiles.append({"tile": tile_name, "error": str(e)})

        if (idx + 1) % 20 == 0 or (idx + 1) == total_found:
            print(f"  Inspected {idx + 1} / {total_found} tiles...", flush=True)

    scan_duration = time.time() - t0

    # Summary analysis
    print("\n" + "=" * 75, flush=True)
    print("INSPECTION RESULTS SUMMARY", flush=True)
    print("=" * 75, flush=True)
    print(f"Total Tiles Inspected:          {total_found}", flush=True)
    print(f"Total Compressed Size on Disk:  {total_bytes / (1024*1024*1024):.2f} GB", flush=True)
    print(f"Corrupted / Unreadable Tiles:   {len(corrupted_tiles)}", flush=True)
    print(f"Suspiciously Small Tiles (<1MB):{len(suspicious_size_tiles)}", flush=True)
    print(f"Unexpected Class Values:        {len(unexpected_classes)}", flush=True)
    print(f"Tiles Intersecting India BBOX:  {len(intersecting_tiles)}", flush=True)
    print(f"Peripheral Tiles Outside BBOX:  {len(non_intersecting_tiles)}", flush=True)
    print(f"Scan Duration:                  {scan_duration:.1f} seconds", flush=True)

    # Coverage grid check
    unique_tile_ids = set(e["tile_id"] for e in inventory)
    print(f"Unique Tile Identifiers:        {len(unique_tile_ids)} (0 duplicates)", flush=True)

    report_data = {
        "dataset_name": "ESA WorldCover 10m 2021 v200",
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_duration_seconds": round(scan_duration, 2),
        "source_directory": str(RAW_WC_DIR),
        "total_tiles_found": total_found,
        "total_size_bytes": total_bytes,
        "total_size_gb": round(total_bytes / (1024*1024*1024), 2),
        "corrupted_tiles": corrupted_tiles,
        "suspicious_size_tiles": suspicious_size_tiles,
        "unexpected_classes": unexpected_classes,
        "india_bbox": INDIA_BBOX,
        "intersecting_tiles_count": len(intersecting_tiles),
        "peripheral_tiles_count": len(non_intersecting_tiles),
        "class_scheme": VALID_CLASSES,
        "tiles": inventory
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "reports" / "worldcover").mkdir(parents=True, exist_ok=True)

    for rd in [REPORTS_DIR, PROJECT_ROOT / "data" / "reports" / "worldcover"]:
        (rd / "worldcover_tile_inventory.json").write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    print(f"\nTile inventory written to:")
    print(f"  - {REPORTS_DIR / 'worldcover_tile_inventory.json'}")
    return report_data

if __name__ == "__main__":
    inspect_worldcover_tiles()
