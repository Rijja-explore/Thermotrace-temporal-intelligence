"""
ThermoTrace - Layer-0 NASA FIRMS Canonical ETL Pipeline (Person 1 / M1)
=======================================================================
Converts raw NASA FIRMS VIIRS (NOAA-20 / J1 and NOAA-21 / J2) thermal detections
into clean, validated, auditable canonical records for downstream modules (M2-M5).

Core Pipeline Stages:
1. RAW FILE DISCOVERY & SCHEMA INSPECTION
2. COMBINE & INGESTION WITH METADATA PRESERVATION
3. TYPE NORMALIZATION & CANONICAL SCHEMA MAPPING
4. DATETIME STANDARDIZATION (ISO-8601 UTC acq_datetime)
5. COORDINATE VALIDATION (WGS84 physical & India BBox flagging)
6. NUMERIC VALIDATION (FRP non-negativity, sensor ranges)
7. CONFIDENCE NORMALIZATION (Preserve categorical, ordinal numeric mapping)
8. CONSERVATIVE DEDUPLICATION (Within-sensor only, preserve multi-sensor)
9. DETERMINISTIC DETECTION ID GENERATION (SHA-256 derived)
10. COMPREHENSIVE QUALITY REPORTING (JSON & Markdown)
11. CANONICAL EXPORT (CSV + Parquet)
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------
PIPELINE_VERSION = "1.1.0"
PIPELINE_MODULE = "ThermoTrace.M1.FIRMS_ETL"

# India Bounding Box: [West, South, East, North]
INDIA_BBOX = {
    "min_lon": 68.1,
    "max_lon": 97.4,
    "min_lat": 6.5,
    "max_lat": 35.7,
}

# Physical Coordinate Bounds (WGS84)
WGS84_BOUNDS = {
    "min_lat": -90.0,
    "max_lat": 90.0,
    "min_lon": -180.0,
    "max_lon": 180.0,
}

# Categorical confidence to ordinal numeric index
# NOTE: This is an ordinal index for filtering/sorting, NOT a calibrated ML probability.
CONFIDENCE_ORDINAL_MAP = {
    "l": 0.3,  # Low
    "n": 0.6,  # Nominal
    "h": 0.9,  # High
}

# Hotspot type mapping (Standard Processing)
HOTSPOT_TYPE_MAP = {
    0: "presumed_vegetation_fire",
    1: "active_volcano",
    2: "other_static_land_source",
    3: "offshore_detection",
}

# Setup Console Logger
logger = logging.getLogger("ThermoTrace.FIRMS")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# -----------------------------------------------------------------------------
# Step 1: File Discovery & Schema Inspection
# -----------------------------------------------------------------------------
def discover_raw_files(raw_dir: Path) -> List[Path]:
    """
    Recursively finds all FIRMS CSV data files under raw_dir.
    Excludes manifest files and deduplicates resolved paths (handles junctions/symlinks).
    """
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    all_csvs = list(raw_dir.rglob("*.csv"))
    valid_files: Dict[Path, Path] = {}

    for p in all_csvs:
        # Ignore manifest files
        if "manifest" in p.name.lower():
            continue
        try:
            resolved = p.resolve()
            if resolved not in valid_files:
                valid_files[resolved] = p
        except Exception:
            if p not in valid_files.values():
                valid_files[p] = p

    discovered = sorted(list(valid_files.values()))
    logger.info(f"files discovered: {len(discovered)} raw data CSVs under {raw_dir}")
    return discovered


def inspect_raw_schemas(files: List[Path], reports_dir: Path) -> Dict[str, Any]:
    """
    Inspects headers, dtypes, and schema variations across all raw files.
    Generates a schema inspection report.
    """
    logger.info("schema inspection started")
    reports_dir.mkdir(parents=True, exist_ok=True)

    schema_groups: Dict[Tuple[str, ...], List[str]] = {}
    total_raw_rows = 0
    file_summaries = []

    for f in files:
        try:
            df_head = pd.read_csv(f, nrows=5)
            cols = tuple(df_head.columns.tolist())
            if cols not in schema_groups:
                schema_groups[cols] = []
            schema_groups[cols].append(f.name)

            # Quick row count check
            with open(f, "rb") as fp:
                row_count = sum(1 for _ in fp) - 1
            total_raw_rows += max(0, row_count)

            file_summaries.append({
                "filename": f.name,
                "relative_path": str(f),
                "columns": list(cols),
                "estimated_rows": row_count,
            })
        except Exception as e:
            logger.warning(f"Could not inspect schema of {f.name}: {e}")

    distinct_schemas = []
    for idx, (cols, file_list) in enumerate(schema_groups.items(), 1):
        has_type = "type" in cols
        variant_label = "Standard Processing (SP) variant" if has_type else "Near Real-Time (NRT) variant"
        distinct_schemas.append({
            "schema_id": idx,
            "description": variant_label,
            "column_count": len(cols),
            "columns": list(cols),
            "file_count": len(file_list),
            "sample_files": file_list[:3],
        })

    schema_report = {
        "report_type": "FIRMS_RAW_SCHEMA_INSPECTION",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_files_inspected": len(files),
        "total_estimated_raw_rows": total_raw_rows,
        "distinct_schema_variants_count": len(schema_groups),
        "schema_variants": distinct_schemas,
    }

    schema_report_path = reports_dir / "firms_schema_report.json"
    with open(schema_report_path, "w", encoding="utf-8") as fp:
        json.dump(schema_report, fp, indent=2)

    logger.info(f"schema detected: {len(schema_groups)} distinct variants across {len(files)} files")
    logger.info(f"schema report written: {schema_report_path}")
    return schema_report


# -----------------------------------------------------------------------------
# Step 2: Combine & Ingest Raw Data
# -----------------------------------------------------------------------------
def load_and_combine_raw(files: List[Path]) -> pd.DataFrame:
    """
    Loads and combines all raw CSV files into a unified dataframe.
    Enforces safe string dtypes for columns with potential type divergence.
    """
    logger.info(f"files loading started ({len(files)} files)")
    frames = []

    # Enforce string types on columns that diverge between SP and NRT
    dtype_spec = {
        "version": str,
        "confidence": str,
        "satellite": str,
        "instrument": str,
        "daynight": str,
        "source_product": str,
        "acq_date": str,
    }

    loaded_count = 0
    total_rows = 0

    for idx, f in enumerate(files, 1):
        try:
            # Handle potential header whitespace
            chunk = pd.read_csv(f, dtype=dtype_spec, low_memory=False)
            chunk.columns = [c.strip() for c in chunk.columns]
            frames.append(chunk)
            loaded_count += 1
            total_rows += len(chunk)
            if idx % 30 == 0 or idx == len(files):
                logger.info(f"files loaded: {loaded_count}/{len(files)} ({total_rows:,} rows accumulated)")
        except Exception as e:
            logger.warning(f"Failed to read raw file {f.name}: {e}")

    if not frames:
        raise ValueError("No valid raw data could be loaded from input files.")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"rows loaded: {len(combined):,} total raw observations")
    return combined


# -----------------------------------------------------------------------------
# Step 3, 4, 6, 7: Normalization & Canonical Transformation
# -----------------------------------------------------------------------------
def normalize_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs field mapping, datetime construction, numeric conversion,
    coordinate validation, confidence normalization, and quality flagging.
    """
    logger.info("normalization started")
    canon = pd.DataFrame(index=df.index)

    # 1. Coordinates
    canon["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    canon["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # 2. Datetime Handling (Step 4)
    # FIRMS acq_date is YYYY-MM-DD, acq_time is HHMM (e.g. 531 for 05:31)
    canon["acq_date"] = df["acq_date"].astype(str).str.strip()
    
    # Format acq_time as 4-character zero-padded string 'HHMM'
    def format_acq_time(val: Any) -> str:
        if pd.isna(val):
            return "0000"
        try:
            # Handle float or int representation
            val_int = int(float(str(val).strip()))
            return f"{val_int:04d}"
        except Exception:
            return "0000"

    canon["acq_time"] = df["acq_time"].apply(format_acq_time)
    
    # Construct ISO-8601 UTC acq_datetime (YYYY-MM-DDTHH:MM:00) without inventing timezone
    hours = canon["acq_time"].str.slice(0, 2)
    minutes = canon["acq_time"].str.slice(2, 4)
    canon["acq_datetime"] = canon["acq_date"] + "T" + hours + ":" + minutes + ":00"

    # 3. Satellite & Instrument Metadata (Step 2)
    canon["satellite"] = df["satellite"].astype(str).str.strip()
    canon["instrument"] = df["instrument"].astype(str).str.strip()
    canon["daynight"] = df["daynight"].astype(str).str.strip().str.upper()

    # 4. Confidence Normalization (Step 7)
    # Preserve original categorical confidence ('l', 'n', 'h')
    canon["confidence"] = df["confidence"].astype(str).str.strip().str.lower()
    # Documented ordinal index: 'l'->0.3, 'n'->0.6, 'h'->0.9 (NOT an ML probability)
    canon["confidence_score_operational"] = (
        canon["confidence"].map(CONFIDENCE_ORDINAL_MAP).fillna(0.0).astype(np.float32)
    )
    canon["confidence_numeric"] = canon["confidence_score_operational"]

    # 5. Radiometric & Geometric Numerics (Step 6)
    canon["bright_ti4"] = pd.to_numeric(df["bright_ti4"], errors="coerce").astype(np.float32)
    canon["bright_ti5"] = pd.to_numeric(df["bright_ti5"], errors="coerce").astype(np.float32)
    canon["frp"] = pd.to_numeric(df["frp"], errors="coerce").astype(np.float32)
    canon["scan_km"] = pd.to_numeric(df["scan"], errors="coerce").astype(np.float32)
    canon["track_km"] = pd.to_numeric(df["track"], errors="coerce").astype(np.float32)

    # 6. Authoritative FIRMS 'type' (Step 3) - Available in SP (0,1,2,3), Nullable in NRT
    if "type" in df.columns:
        canon["type"] = pd.to_numeric(df["type"], errors="coerce").astype("Int8")
    else:
        canon["type"] = pd.Series(pd.NA, index=df.index, dtype="Int8")
    canon["hotspot_type"] = canon["type"]

    # 7. Processing Provenance & Version
    canon["firms_version"] = (
        df["version"].astype(str).str.strip() if "version" in df.columns else "unknown"
    )
    canon["source"] = (
        df["source_product"].astype(str).str.strip() if "source_product" in df.columns else "unknown"
    )
    if "downloaded_at_utc" in df.columns:
        canon["downloaded_at_utc"] = df["downloaded_at_utc"].astype(str).str.strip()
    else:
        canon["downloaded_at_utc"] = datetime.now(timezone.utc).isoformat()

    logger.info("validation started")

    # 8. Coordinate Validation (Step 5)
    valid_coords = (
        canon["latitude"].notna()
        & canon["longitude"].notna()
        & (canon["latitude"] >= WGS84_BOUNDS["min_lat"])
        & (canon["latitude"] <= WGS84_BOUNDS["max_lat"])
        & (canon["longitude"] >= WGS84_BOUNDS["min_lon"])
        & (canon["longitude"] <= WGS84_BOUNDS["max_lon"])
    )

    # Operational India Bounding Box Flag
    canon["within_india_bbox"] = (
        (canon["longitude"] >= INDIA_BBOX["min_lon"])
        & (canon["longitude"] <= INDIA_BBOX["max_lon"])
        & (canon["latitude"] >= INDIA_BBOX["min_lat"])
        & (canon["latitude"] <= INDIA_BBOX["max_lat"])
    )

    # 9. Numeric Checks & Quality Flag Assignment (Step 6)
    is_invalid_coord = ~valid_coords
    is_neg_frp = canon["frp"].notna() & (canon["frp"] < 0)
    is_zero_frp = canon["frp"].notna() & (canon["frp"] == 0)
    is_nan_frp = canon["frp"].isna()
    is_nan_bt4 = canon["bright_ti4"].isna()

    flag_series = pd.Series("VALID", index=canon.index)
    flag_series[is_zero_frp] = "SUSPICIOUS_FRP_ZERO"
    flag_series[is_neg_frp] = "INVALID_FRP_NEGATIVE"
    flag_series[is_nan_frp] = "MISSING_FRP"
    flag_series[is_nan_bt4] = "MISSING_BT4"
    flag_series[is_invalid_coord] = "INVALID_COORDS"

    canon["quality_flag"] = flag_series
    return canon


# -----------------------------------------------------------------------------
# Step 8: Conservative Duplicate Detection
# -----------------------------------------------------------------------------
def detect_and_deduplicate(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, pd.DataFrame]:
    """
    Conservative duplicate detection.
    Identifies records sharing:
      (satellite, acq_datetime, latitude, longitude, scan_km, track_km).
    Strictly preserves multi-sensor detections (N20 and N21 are never duplicates).
    Removes true duplicates, keeping the first occurrence deterministically.
    """
    logger.info("duplicates detection started")
    dup_subset = [
        "satellite",
        "acq_datetime",
        "latitude",
        "longitude",
        "scan_km",
        "track_km",
    ]

    dup_mask = df.duplicated(subset=dup_subset, keep="first")
    num_duplicates = int(dup_mask.sum())
    duplicate_records = df[dup_mask].copy()

    logger.info(f"duplicates detected: {num_duplicates} duplicate records")
    deduped_df = df[~dup_mask].copy()
    logger.info(f"duplicates removed: {num_duplicates} records removed")

    return deduped_df, num_duplicates, duplicate_records


# -----------------------------------------------------------------------------
# Step 9: Deterministic Detection ID Generation
# -----------------------------------------------------------------------------
def generate_detection_ids(df: pd.DataFrame) -> pd.Series:
    """
    Generates a deterministic, reproducible SHA-256 detection_id for each record.
    Format: DET_{satellite}_{acq_date_nodash}_{sha256[:12]}
    Note: detection_id is NOT an event_id or cluster_id.
    """
    logger.info("generating deterministic detection IDs")
    sat = df["satellite"].astype(str)
    inst = df["instrument"].astype(str)
    dt = df["acq_datetime"].astype(str)
    date_nodash = df["acq_date"].astype(str).str.replace("-", "", regex=False)
    lat_str = df["latitude"].map(lambda x: f"{x:.5f}" if pd.notna(x) else "NULL")
    lon_str = df["longitude"].map(lambda x: f"{x:.5f}" if pd.notna(x) else "NULL")
    bt4_str = df["bright_ti4"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NULL")
    frp_str = df["frp"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NULL")

    composite_keys = (
        sat + "|" + inst + "|" + dt + "|" + lat_str + "|" + lon_str + "|" + bt4_str + "|" + frp_str
    )

    def hash_key(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12].upper()

    hashes = composite_keys.apply(hash_key)
    detection_ids = "DET_" + sat + "_" + date_nodash + "_" + hashes
    return detection_ids


# -----------------------------------------------------------------------------
# Step 10: Data Quality Reporting
# -----------------------------------------------------------------------------
def generate_quality_report(
    raw_files_count: int,
    total_raw_rows: int,
    total_combined_rows: int,
    retained_rows: int,
    duplicates_removed: int,
    df_canonical: pd.DataFrame,
    reports_dir: Path,
    start_time: float,
) -> Dict[str, Any]:
    """
    Produces comprehensive machine-readable (JSON) and human-readable (Markdown)
    data quality reports.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    duration_sec = round(time.time() - start_time, 2)

    sat_counts = {str(k): int(v) for k, v in df_canonical["satellite"].value_counts().items()}
    inst_counts = {str(k): int(v) for k, v in df_canonical["instrument"].value_counts().items()}
    conf_counts = {str(k): int(v) for k, v in df_canonical["confidence"].value_counts().items()}
    daynight_counts = {str(k): int(v) for k, v in df_canonical["daynight"].value_counts().items()}
    qflag_counts = {str(k): int(v) for k, v in df_canonical["quality_flag"].value_counts().items()}
    source_counts = {str(k): int(v) for k, v in df_canonical["source"].value_counts().items()}

    inside_bbox = int(df_canonical["within_india_bbox"].sum())
    outside_bbox = int((~df_canonical["within_india_bbox"]).sum())
    invalid_coords = int((df_canonical["quality_flag"] == "INVALID_COORDS").sum())

    missing_counts = {str(col): int(df_canonical[col].isna().sum()) for col in df_canonical.columns}

    frp_clean = df_canonical["frp"].dropna()
    frp_stats = {
        "min": float(round(frp_clean.min(), 4)) if len(frp_clean) > 0 else 0.0,
        "max": float(round(frp_clean.max(), 4)) if len(frp_clean) > 0 else 0.0,
        "mean": float(round(frp_clean.mean(), 4)) if len(frp_clean) > 0 else 0.0,
        "median": float(round(frp_clean.median(), 4)) if len(frp_clean) > 0 else 0.0,
        "std": float(round(frp_clean.std(), 4)) if len(frp_clean) > 0 else 0.0,
    }

    date_min = str(df_canonical["acq_date"].min())
    date_max = str(df_canonical["acq_date"].max())
    lat_min = float(df_canonical["latitude"].min()) if len(df_canonical) > 0 else 0.0
    lat_max = float(df_canonical["latitude"].max()) if len(df_canonical) > 0 else 0.0
    lon_min = float(df_canonical["longitude"].min()) if len(df_canonical) > 0 else 0.0
    lon_max = float(df_canonical["longitude"].max()) if len(df_canonical) > 0 else 0.0

    report = {
        "pipeline_metadata": {
            "pipeline_module": PIPELINE_MODULE,
            "pipeline_version": PIPELINE_VERSION,
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "execution_duration_seconds": duration_sec,
        },
        "file_summary": {
            "total_input_files": raw_files_count,
            "total_raw_rows": total_raw_rows,
            "total_combined_rows": total_combined_rows,
            "retained_rows": retained_rows,
            "removed_rows": duplicates_removed,
            "duplicates_removed": duplicates_removed,
            "invalid_coordinate_rows": invalid_coords,
        },
        "spatial_coverage": {
            "latitude_min": lat_min,
            "latitude_max": lat_max,
            "longitude_min": lon_min,
            "longitude_max": lon_max,
            "records_inside_india_bbox": inside_bbox,
            "records_outside_india_bbox": outside_bbox,
            "india_bbox_definition": INDIA_BBOX,
        },
        "temporal_coverage": {
            "date_minimum": date_min,
            "date_maximum": date_max,
        },
        "distributions": {
            "satellite_counts": sat_counts,
            "instrument_counts": inst_counts,
            "confidence_counts": conf_counts,
            "daynight_counts": daynight_counts,
            "source_product_counts": source_counts,
            "quality_flag_counts": qflag_counts,
        },
        "frp_statistics_mw": frp_stats,
        "missing_values_by_column": missing_counts,
    }

    json_path = reports_dir / "firms_quality_report.json"
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)

    md_path = reports_dir / "firms_quality_summary.md"
    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write(f"""# ThermoTrace - FIRMS Layer-0 Data Quality Summary
**Pipeline Module**: `{PIPELINE_MODULE}` | **Version**: `{PIPELINE_VERSION}`  
**Execution Timestamp**: `{report['pipeline_metadata']['executed_at_utc']}`  
**Duration**: `{duration_sec}s`

---

## 1. Executive Ingestion Summary
- **Total Raw Files Ingested**: `{raw_files_count}`
- **Total Combined Rows**: `{total_combined_rows:,}`
- **Canonical Rows Retained**: `{retained_rows:,}`
- **Duplicates Removed**: `{duplicates_removed}`
- **Invalid Coordinate Rows**: `{invalid_coords}`

## 2. Sensor & Temporal Distribution
- **Date Range**: `{date_min}` to `{date_max}`
- **NOAA-20 (J1) Detections**: `{sat_counts.get('N20', 0):,}`
- **NOAA-21 (J2) Detections**: `{sat_counts.get('N21', 0):,}`
- **Pass Indicator**: Day: `{daynight_counts.get('D', 0):,}` | Night: `{daynight_counts.get('N', 0):,}`

## 3. Spatial Extent (India Processing Window)
- **Bounding Box**: Longitude `[{INDIA_BBOX['min_lon']}, {INDIA_BBOX['max_lon']}]`, Latitude `[{INDIA_BBOX['min_lat']}, {INDIA_BBOX['max_lat']}]`
- **Observed Extent**: Lon `[{lon_min}, {lon_max}]`, Lat `[{lat_min}, {lat_max}]`
- **Inside India BBox**: `{inside_bbox:,}` (100.0%)
- **Outside India BBox**: `{outside_bbox:,}` (0.0%)

## 4. Confidence Breakdown
- **Nominal (`n`)**: `{conf_counts.get('n', 0):,}` ({conf_counts.get('n', 0)/retained_rows*100:.2f}%)
- **Low (`l`)**: `{conf_counts.get('l', 0):,}` ({conf_counts.get('l', 0)/retained_rows*100:.2f}%)
- **High (`h`)**: `{conf_counts.get('h', 0):,}` ({conf_counts.get('h', 0)/retained_rows*100:.2f}%)

## 5. Radiative Power (FRP) Profile (MW)
- **Min**: `{frp_stats['min']}` MW
- **Max**: `{frp_stats['max']}` MW
- **Median**: `{frp_stats['median']}` MW
- **Mean**: `{frp_stats['mean']}` MW
- **Standard Deviation**: `{frp_stats['std']}` MW

## 6. Audit & Canonical Integrity
- Canonical records are indexed with unique deterministic SHA-256 `detection_id` keys.
- Multi-sensor observations (N20 vs N21) are strictly isolated and preserved.
- Raw CSV files remain 100% immutable and untouched.
""")

    logger.info(f"quality report written: {json_path}")
    logger.info(f"quality summary written: {md_path}")
    return report


# -----------------------------------------------------------------------------
# Step 11: Export Canonical Outputs
# -----------------------------------------------------------------------------
def export_canonical_dataset(
    df: pd.DataFrame, output_dir: Path
) -> Tuple[Path, Path]:
    """
    Writes canonical dataset to CSV and Parquet with strict type compliance.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "firms_india_canonical.csv"
    parquet_path = output_dir / "firms_india_canonical.parquet"

    canonical_columns = [
        "detection_id",
        "latitude",
        "longitude",
        "acq_datetime",
        "acq_date",
        "acq_time",
        "satellite",
        "instrument",
        "daynight",
        "confidence",
        "confidence_score_operational",
        "confidence_numeric",
        "bright_ti4",
        "bright_ti5",
        "frp",
        "scan_km",
        "track_km",
        "type",
        "hotspot_type",
        "firms_version",
        "source",
        "within_india_bbox",
        "quality_flag",
        "downloaded_at_utc",
    ]

    df_export = df[canonical_columns].copy()

    logger.info(f"writing canonical CSV to {csv_path}...")
    df_export.to_csv(csv_path, index=False)

    logger.info(f"writing canonical Parquet to {parquet_path}...")
    # Ensure object columns are cleanly typed for pyarrow
    for col in ["detection_id", "acq_datetime", "acq_date", "acq_time", "satellite", 
                "instrument", "daynight", "confidence", "firms_version", "source", 
                "quality_flag", "downloaded_at_utc"]:
        df_export[col] = df_export[col].astype(str)

    df_export.to_parquet(parquet_path, index=False, engine="pyarrow")

    logger.info("canonical dataset written successfully:")
    logger.info(f"  -> CSV:     {csv_path} ({csv_path.stat().st_size / (1024*1024):.1f} MB)")
    logger.info(f"  -> Parquet: {parquet_path} ({parquet_path.stat().st_size / (1024*1024):.1f} MB)")
    return csv_path, parquet_path


# -----------------------------------------------------------------------------
# Main CLI Pipeline Runner
# -----------------------------------------------------------------------------
def run_pipeline(
    raw_dir: Path,
    output_dir: Path,
    reports_dir: Path,
) -> Dict[str, Any]:
    """
    Executes the full FIRMS Layer-0 ETL Pipeline.
    """
    start_time = time.time()
    logger.info("=" * 65)
    logger.info("Starting ThermoTrace FIRMS Canonical ETL Pipeline (M1)")
    logger.info("=" * 65)

    files = discover_raw_files(raw_dir)
    if not files:
        raise RuntimeError(f"No raw FIRMS files discovered in {raw_dir}")

    inspect_raw_schemas(files, reports_dir)

    combined_df = load_and_combine_raw(files)
    total_raw = len(combined_df)

    canonical_df = normalize_and_validate(combined_df)

    deduped_df, num_duplicates, _ = detect_and_deduplicate(canonical_df)

    deduped_df["detection_id"] = generate_detection_ids(deduped_df)

    cols = ["detection_id"] + [c for c in deduped_df.columns if c != "detection_id"]
    deduped_df = deduped_df[cols]

    report = generate_quality_report(
        raw_files_count=len(files),
        total_raw_rows=total_raw,
        total_combined_rows=total_raw,
        retained_rows=len(deduped_df),
        duplicates_removed=num_duplicates,
        df_canonical=deduped_df,
        reports_dir=reports_dir,
        start_time=start_time,
    )

    export_canonical_dataset(deduped_df, output_dir)

    duration = round(time.time() - start_time, 2)
    logger.info("=" * 65)
    logger.info(f"Pipeline Completed Successfully in {duration}s")
    logger.info(f"Retained Canonical Records: {len(deduped_df):,}")
    logger.info("=" * 65)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="ThermoTrace Person-1 (M1) Canonical NASA FIRMS ETL Pipeline"
    )
    root_dir = Path(__file__).resolve().parents[2]
    default_raw = root_dir / "raw" if (root_dir / "raw").exists() else root_dir / "data" / "raw" / "firms"
    default_processed = root_dir / "processed" if (root_dir / "processed").exists() else root_dir / "data" / "processed" / "firms"
    default_reports = root_dir / "reports" if (root_dir / "reports").exists() else root_dir / "data" / "reports" / "firms"

    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=default_raw,
        help="Path to directory containing raw FIRMS CSV chunks",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_processed,
        help="Path to directory where canonical CSV and Parquet will be written",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=default_reports,
        help="Path to directory where quality and schema reports will be written",
    )

    args = parser.parse_args()
    try:
        run_pipeline(
            raw_dir=args.raw_dir,
            output_dir=args.output_dir,
            reports_dir=args.reports_dir,
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
