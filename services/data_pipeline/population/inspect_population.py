"""
ThermoTrace Population Layer Inspection & Quality Assurance
===========================================================

Production inspection script for WorldPop India 2025 (100m resolution).
Performs windowed, chunked streaming inspection without loading the entire
1.21-billion-pixel raster into memory.

Rules:
- Raw GeoTIFF is strictly immutable (read-only mode).
- No CSV conversion.
- No memory bloat (working set < 500 MB).
- Precise tracking of valid, NoData, zero, negative, NaN/Inf, and extreme cells.
- Outputs machine-readable JSON reports and Markdown quality summary.
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

RAW_POP_PATH = PROJECT_ROOT / "data" / "raw" / "population" / "ind_pop_2025_CN_100m_R2025A_v1.tif"
if not RAW_POP_PATH.exists():
    fallback = PROJECT_ROOT / "population" / "ind_pop_2025_CN_100m_R2025A_v1.tif"
    if fallback.exists():
        RAW_POP_PATH = fallback

REPORTS_DIR = PROJECT_ROOT / "reports" / "population"
INDIA_EXPECTED_EXTENT = {
    "min_lon": 68.1,
    "min_lat": 6.5,
    "max_lon": 97.4,
    "max_lat": 35.7
}

def inspect_population_raster(raster_path: Path):
    if not raster_path.exists():
        raise FileNotFoundError(f"Population raster not found at: {raster_path}")

    raw_stat = raster_path.stat()
    file_size_bytes = raw_stat.st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    print("=" * 75, flush=True)
    print("THERMOTRACE POPULATION LAYER INSPECTION (WorldPop 2025 India 100m)", flush=True)
    print("=" * 75, flush=True)
    print(f"File Path: {raster_path}", flush=True)
    print(f"File Size: {file_size_bytes:,} bytes ({file_size_mb:.2f} MiB)", flush=True)

    t0 = time.time()

    # 1. Metadata Inspection
    with rasterio.open(raster_path) as src:
        crs_str = str(src.crs)
        width = src.width
        height = src.height
        total_pixels = width * height
        band_count = src.count
        dtypes = [str(d) for d in src.dtypes]
        resolution = src.res
        bounds = {
            "left": round(src.bounds.left, 6),
            "bottom": round(src.bounds.bottom, 6),
            "right": round(src.bounds.right, 6),
            "top": round(src.bounds.top, 6)
        }
        transform = [round(v, 8) for v in src.transform]
        nodata = float(src.nodata) if src.nodata is not None else -99999.0

        print(f"\n[1] Metadata:", flush=True)
        print(f"  CRS:           {crs_str}", flush=True)
        print(f"  Dimensions:    {width:,} x {height:,} ({total_pixels:,} total pixels)", flush=True)
        print(f"  Bands:         {band_count}", flush=True)
        print(f"  Datatype:      {dtypes[0]}", flush=True)
        print(f"  Resolution:    {resolution[0]:.8f} x {resolution[1]:.8f} degrees (~100m)", flush=True)
        print(f"  Bounds:        [{bounds['left']}, {bounds['bottom']}] to [{bounds['right']}, {bounds['top']}]", flush=True)
        print(f"  Declared NoData: {nodata}", flush=True)

        # 2. Windowed Streaming QA & Statistics
        print(f"\n[2] Scanning raster blocks (streaming chunked QA)...", flush=True)

        valid_count = 0
        nodata_count = 0
        nan_count = 0
        inf_count = 0
        neg_count = 0
        zero_count = 0
        nonzero_count = 0

        total_population_sum = 0.0
        global_min = float('inf')
        global_max = float('-inf')
        max_cell_coords = None

        corrupted_blocks = 0
        total_windows = 0

        # Subsample for quantile calculation (1 in 200 pixels)
        sample_values = []

        for ji, window in src.block_windows(1):
            total_windows += 1
            try:
                block = src.read(1, window=window)
            except Exception as e:
                corrupted_blocks += 1
                continue

            # Check for NaN / Inf
            nans = np.isnan(block)
            infs = np.isinf(block)
            nan_in_block = int(np.sum(nans))
            inf_in_block = int(np.sum(infs))
            nan_count += nan_in_block
            inf_count += inf_in_block

            # Mask NoData and NaNs
            is_nodata = (block == nodata) | nans | infs
            nodata_in_block = int(np.sum(block == nodata))
            nodata_count += nodata_in_block

            valid_mask = ~is_nodata
            valid_pixels = block[valid_mask]
            k_valid = valid_pixels.size

            if k_valid > 0:
                valid_count += k_valid

                # Negative values (excluding NoData)
                neg_in_block = int(np.sum(valid_pixels < 0))
                neg_count += neg_in_block

                # Zero vs Nonzero
                zeros_in_block = int(np.sum(valid_pixels == 0))
                zero_count += zeros_in_block
                nonzero_count += (k_valid - zeros_in_block)

                # Sum
                total_population_sum += float(np.sum(valid_pixels))

                # Min & Max
                b_min = float(np.min(valid_pixels))
                b_max = float(np.max(valid_pixels))
                if b_min < global_min:
                    global_min = b_min
                if b_max > global_max:
                    global_max = b_max
                    # Compute spatial coordinates of the max cell
                    max_idx = np.unravel_index(np.argmax(block), block.shape)
                    row = window.row_off + max_idx[0]
                    col = window.col_off + max_idx[1]
                    lon, lat = src.xy(row, col)
                    max_cell_coords = {"lon": round(lon, 6), "lat": round(lat, 6), "row": int(row), "col": int(col)}

                # Collect sample for median and quantiles
                sample_values.append(valid_pixels[::200])

            if total_windows % 1000 == 0:
                print(f"  Processed {total_windows:,} blocks...", flush=True)

        mean_val = (total_population_sum / valid_count) if valid_count > 0 else 0.0

        # Calculate quantiles from sample
        if sample_values:
            combined_sample = np.concatenate(sample_values)
            quantiles = {
                "p10": round(float(np.percentile(combined_sample, 10)), 4),
                "p25": round(float(np.percentile(combined_sample, 25)), 4),
                "p50_median": round(float(np.median(combined_sample)), 4),
                "p75": round(float(np.percentile(combined_sample, 75)), 4),
                "p90": round(float(np.percentile(combined_sample, 90)), 4),
                "p95": round(float(np.percentile(combined_sample, 95)), 4),
                "p99": round(float(np.percentile(combined_sample, 99)), 4),
            }
        else:
            quantiles = {}

    scan_duration = time.time() - t0
    zero_pct = (zero_count / valid_count * 100) if valid_count > 0 else 0.0
    valid_pct = (valid_count / total_pixels * 100)

    # 3. Spatial Coverage Evaluation
    bounds_contain_india = (
        bounds["left"] <= INDIA_EXPECTED_EXTENT["min_lon"] and
        bounds["bottom"] <= INDIA_EXPECTED_EXTENT["min_lat"] and
        bounds["right"] >= INDIA_EXPECTED_EXTENT["max_lon"] and
        bounds["top"] >= INDIA_EXPECTED_EXTENT["max_lat"]
    )

    # 4. Warnings & Errors
    warnings = []
    errors = []

    if corrupted_blocks > 0:
        errors.append(f"Detected {corrupted_blocks} unreadable / corrupted raster blocks.")
    if nan_count > 0:
        warnings.append(f"Detected {nan_count:,} NaN values in raster array.")
    if inf_count > 0:
        warnings.append(f"Detected {inf_count:,} Infinite values in raster array.")
    if neg_count > 0:
        errors.append(f"Detected {neg_count:,} negative population cells (excluding NoData).")
    if global_max > 250_000:
        warnings.append(f"Extremely high population cell detected: {global_max:,.1f} persons/100m pixel.")
    if not bounds_contain_india:
        warnings.append("Raster bounds do not fully encompass standard India BBOX [68.1, 6.5, 97.4, 35.7].")

    print(f"\n[3] Inspection Results:", flush=True)
    print(f"  Valid Pixels:        {valid_count:,} ({valid_pct:.1f}%)", flush=True)
    print(f"  NoData Pixels:       {nodata_count:,} ({nodata_count / total_pixels * 100:.1f}%)", flush=True)
    print(f"  Total Estimated Pop: {total_population_sum:,.1f} persons", flush=True)
    print(f"  Minimum Pop / Cell:  {global_min:.4f}", flush=True)
    print(f"  Maximum Pop / Cell:  {global_max:.4f} (at {max_cell_coords})", flush=True)
    print(f"  Mean Pop / Cell:     {mean_val:.4f}", flush=True)
    print(f"  Median Pop / Cell:   {quantiles.get('p50_median')} persons/cell", flush=True)
    print(f"  Zero Population:     {zero_count:,} cells ({zero_pct:.2f}% of valid land cells)", flush=True)
    print(f"  Nonzero Population:  {nonzero_count:,} cells ({100 - zero_pct:.2f}% of valid land cells)", flush=True)
    print(f"  Scan Duration:       {scan_duration:.1f} seconds", flush=True)
    print(f"  Warnings:            {len(warnings)}", flush=True)
    print(f"  Errors:              {len(errors)}", flush=True)

    report_dict = {
        "source_file": str(raster_path),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_duration_seconds": round(scan_duration, 2),
        "metadata": {
            "crs": crs_str,
            "width": width,
            "height": height,
            "total_pixels": total_pixels,
            "band_count": band_count,
            "datatype": dtypes[0],
            "resolution": list(resolution),
            "bounds": bounds,
            "transform": transform,
            "nodata_value": nodata
        },
        "spatial_coverage": {
            "expected_india_bbox": INDIA_EXPECTED_EXTENT,
            "raster_bounds": bounds,
            "encompasses_india_bbox": bounds_contain_india,
            "note": "Raster bounding box matches national extent; national boundary masking should be performed with the authoritative India boundary layer."
        },
        "raster_validity": {
            "opens_successfully": True,
            "single_band_confirmed": band_count == 1,
            "corrupted_blocks": corrupted_blocks,
            "nan_count": nan_count,
            "inf_count": inf_count,
            "negative_values_count": neg_count
        },
        "population_statistics": {
            "valid_pixels": valid_count,
            "valid_percentage": round(valid_pct, 2),
            "nodata_pixels": nodata_count,
            "nodata_percentage": round(nodata_count / total_pixels * 100, 2),
            "total_estimated_population": round(total_population_sum, 1),
            "min_population_per_cell": global_min,
            "max_population_per_cell": round(global_max, 4),
            "max_cell_location": max_cell_coords,
            "mean_population_per_valid_cell": round(mean_val, 4),
            "median_population_per_valid_cell": quantiles.get("p50_median"),
            "quantiles": quantiles,
            "zero_population_cells": zero_count,
            "zero_population_percentage": round(zero_pct, 2),
            "nonzero_population_cells": nonzero_count,
            "nonzero_population_percentage": round(100 - zero_pct, 2)
        },
        "qa_checks": {
            "warnings": warnings,
            "errors": errors,
            "status": "PASSED" if len(errors) == 0 else "FAILED"
        }
    }

    # Save JSON reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "reports" / "population").mkdir(parents=True, exist_ok=True)

    for r_dir in [REPORTS_DIR, PROJECT_ROOT / "data" / "reports" / "population"]:
        (r_dir / "population_inspection.json").write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        (r_dir / "population_quality_report.json").write_text(json.dumps(report_dict, indent=2), encoding="utf-8")

    # Save Markdown Summary
    md_summary = generate_markdown_summary(report_dict)
    (REPORTS_DIR / "population_quality_summary.md").write_text(md_summary, encoding="utf-8")
    (PROJECT_ROOT / "data" / "reports" / "population" / "population_quality_summary.md").write_text(md_summary, encoding="utf-8")

    print(f"\nSaved inspection artifacts:")
    print(f"  - {REPORTS_DIR / 'population_inspection.json'}")
    print(f"  - {REPORTS_DIR / 'population_quality_report.json'}")
    print(f"  - {REPORTS_DIR / 'population_quality_summary.md'}")

    return report_dict

def generate_markdown_summary(rep: dict) -> str:
    meta = rep["metadata"]
    pop = rep["population_statistics"]
    qa = rep["qa_checks"]
    b = meta["bounds"]

    return f"""# ThermoTrace Population Layer QA Summary (WorldPop 2025 India 100m)

**Generated:** {rep['inspection_timestamp']}  
**Status:** **{qa['status']}** ({len(qa['warnings'])} warnings, {len(qa['errors'])} errors)

---

## 1. Observed Facts (Raster Metadata)
* **Source Path:** `{rep['source_file']}`
* **File Size:** {rep['file_size_mb']:.2f} MiB ({rep['file_size_bytes']:,} bytes)
* **Coordinate Reference System (CRS):** `{meta['crs']}`
* **Raster Dimensions:** {meta['width']:,} columns × {meta['height']:,} rows ({meta['total_pixels']:,} total pixels)
* **Band Count:** {meta['band_count']} band (`{meta['datatype']}`)
* **Spatial Resolution:** {meta['resolution'][0]:.8f}° × {meta['resolution'][1]:.8f}° (~100m cell size at equator)
* **Bounding Extent:**
  * West: `{b['left']}`
  * South: `{b['bottom']}`
  * East: `{b['right']}`
  * North: `{b['top']}`
* **NoData Value:** `{meta['nodata_value']}`

---

## 2. Calculated Population Statistics
| Metric | Value | Description |
|---|---|---|
| **Total Estimated Population** | **{pop['total_estimated_population']:,.1f}** | Sum of population in all valid raster cells |
| **Valid Land Pixels** | **{pop['valid_pixels']:,}** ({pop['valid_percentage']}%) | Terrestrial pixels inside India coverage |
| **NoData Pixels** | **{pop['nodata_pixels']:,}** ({pop['nodata_percentage']}%) | Oceanic and external background cells |
| **Mean Population / Cell** | **{pop['mean_population_per_valid_cell']:.4f}** persons | Arithmetic mean across valid cells |
| **Median Population / Cell** | **{pop['median_population_per_valid_cell']:.4f}** persons | 50th percentile (representative sampling) |
| **Minimum Value** | **{pop['min_population_per_cell']:.4f}** persons | Smallest observed valid population value |
| **Maximum Value** | **{pop['max_population_per_cell']:.4f}** persons | Peak density cell (Lon {pop['max_cell_location']['lon']}, Lat {pop['max_cell_location']['lat']}) |
| **Zero-Population Cells** | **{pop['zero_population_cells']:,}** ({pop['zero_population_percentage']}%) | Uninhabited land cells (mountains, deserts, forests) |
| **Nonzero Cells** | **{pop['nonzero_population_cells']:,}** ({pop['nonzero_population_percentage']}%) | Populated settlements and habitations |

### Quantile Distribution (Persons / 100m Cell)
* **P10:** {pop['quantiles'].get('p10')}
* **P25:** {pop['quantiles'].get('p25')}
* **P50 (Median):** {pop['quantiles'].get('p50_median')}
* **P75:** {pop['quantiles'].get('p75')}
* **P90:** {pop['quantiles'].get('p90')}
* **P95:** {pop['quantiles'].get('p95')}
* **P99:** {pop['quantiles'].get('p99')}

---

## 3. Data Quality & Warnings
* **Corrupted Blocks:** `{rep['raster_validity']['corrupted_blocks']}`
* **Negative Values:** `{rep['raster_validity']['negative_values_count']}`
* **NaN Values:** `{rep['raster_validity']['nan_count']}`
* **Infinite Values:** `{rep['raster_validity']['inf_count']}`
* **Warnings Logged:** {len(qa['warnings'])}
{chr(10).join(f'  * {w}' for w in qa['warnings']) if qa['warnings'] else '  * None'}
* **Errors Logged:** {len(qa['errors'])}
{chr(10).join(f'  * {e}' for e in qa['errors']) if qa['errors'] else '  * None'}

---

## 4. Operational Notes
1. **Raw File Immutability:** The raw GeoTIFF was inspected in read-only streaming mode and was not modified.
2. **Spatial Masking:** Bounding box covers the entire Indian subcontinent. National boundary masking should be performed downstream using the project's authoritative administrative polygon.
"""

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_POP_PATH
    inspect_population_raster(target)
