"""
ThermoTrace - Spatiotemporal Event Engine v0.1 (Module M3)
==========================================================
Converts Layer-0 NASA FIRMS VIIRS canonical detection records into coherent,
traceable, spatiotemporal thermal event objects.

Core Architecture:
1. Canonical Input Validation (read-only ingestion)
2. Metric Spatial Projection (Equirectangular WGS84 to local km)
3. Scalable Sliding-Window KDTree Indexing (O(N log N))
4. Bounded Disjoint Set Union (Union-Find) with Chaining Prevention
5. High-Performance Vectorized Event Feature Aggregation
6. Relational Event-to-Detection Link Table Generation
7. Empirical Parameter Sensitivity Analysis
8. Comprehensive Quality Reporting (JSON & Markdown)
9. Canonical Event Exports (Parquet & CSV)
"""

import argparse
import json
import logging
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import KDTree

# -----------------------------------------------------------------------------
# Module Metadata & Initial Prototype Parameters
# -----------------------------------------------------------------------------
ENGINE_VERSION = "0.1.0"
ENGINE_MODULE = "ThermoTrace.M3.EventEngine"

# Initial prototype parameters (Empirically validated; configurable via CLI)
DEFAULT_SPATIAL_RADIUS_KM = 1.0
DEFAULT_TEMPORAL_WINDOW_HOURS = 6.0
DEFAULT_MAX_EVENT_DURATION_HOURS = 48.0
DEFAULT_MAX_EVENT_DIAMETER_KM = 15.0

# Earth radius in kilometers for metric equirectangular approximation
EARTH_RADIUS_KM = 6371.0

# Setup Console Logger
logger = logging.getLogger("ThermoTrace.Events")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# -----------------------------------------------------------------------------
# Bounded Disjoint Set Union (Chaining Prevention Engine)
# -----------------------------------------------------------------------------
class BoundedUnionFind:
    """
    Disjoint Set Union (Union-Find) with path compression, union by rank,
    and strict spatial/temporal bounding constraints to prevent runaway chaining.
    """

    def __init__(
        self,
        n: int,
        x: np.ndarray,
        y: np.ndarray,
        t_hours: np.ndarray,
        max_duration_hours: float = DEFAULT_MAX_EVENT_DURATION_HOURS,
        max_extent_km: float = DEFAULT_MAX_EVENT_DIAMETER_KM,
    ):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.min_t = t_hours.copy()
        self.max_t = t_hours.copy()
        self.min_x = x.copy()
        self.max_x = x.copy()
        self.min_y = y.copy()
        self.max_y = y.copy()
        self.max_dur = max_duration_hours
        self.max_ext = max_extent_km
        self.rejected_chaining_edges = 0

    def find(self, i: int) -> int:
        path = []
        p = self.parent
        while p[i] != i:
            path.append(i)
            i = p[i]
        for node in path:
            p[node] = i
        return i

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i == root_j:
            return True

        # Check temporal bounding constraint (prevents multi-day temporal chaining)
        new_min_t = min(self.min_t[root_i], self.min_t[root_j])
        new_max_t = max(self.max_t[root_i], self.max_t[root_j])
        if (new_max_t - new_min_t) > self.max_dur:
            self.rejected_chaining_edges += 1
            return False

        # Check spatial bounding constraint (prevents runaway geographical chaining)
        new_min_x = min(self.min_x[root_i], self.min_x[root_j])
        new_max_x = max(self.max_x[root_i], self.max_x[root_j])
        new_min_y = min(self.min_y[root_i], self.min_y[root_j])
        new_max_y = max(self.max_y[root_i], self.max_y[root_j])
        diag = math.sqrt((new_max_x - new_min_x) ** 2 + (new_max_y - new_min_y) ** 2)
        if diag > self.max_ext:
            self.rejected_chaining_edges += 1
            return False

        # Union by rank
        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
            dest = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
            dest = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1
            dest = root_i

        self.min_t[dest] = new_min_t
        self.max_t[dest] = new_max_t
        self.min_x[dest] = new_min_x
        self.max_x[dest] = new_max_x
        self.min_y[dest] = new_min_y
        self.max_y[dest] = new_max_y
        return True


# -----------------------------------------------------------------------------
# Input Ingestion & Coordinate Projection
# -----------------------------------------------------------------------------
def load_canonical_firms(parquet_path: Path) -> pd.DataFrame:
    """
    Loads canonical FIRMS detections and prepares metric coordinates.
    """
    parquet_path = Path(parquet_path)
    if not parquet_path.exists():
        raise FileNotFoundError(f"Canonical FIRMS dataset not found at {parquet_path}")

    logger.info(f"Loading canonical FIRMS dataset from {parquet_path}...")
    t0 = time.time()
    df = pd.read_parquet(parquet_path)
    t1 = time.time()
    logger.info(f"Loaded {len(df):,} canonical records in {t1-t0:.2f}s")

    # Chronological sort for deterministic processing
    logger.info("Sorting detections chronologically...")
    df["acq_dt"] = pd.to_datetime(df["acq_datetime"])
    df = df.sort_values("acq_dt").reset_index(drop=True)

    # Reference epoch in hours
    t_ref = df["acq_dt"].iloc[0]
    df["epoch_hours"] = (df["acq_dt"] - t_ref).dt.total_seconds() / 3600.0

    # Local metric projection in kilometers (Equirectangular)
    lat0 = float(df["latitude"].mean())
    lon0 = float(df["longitude"].mean())
    cos_lat0 = math.cos(math.radians(lat0))

    df["proj_x_km"] = np.radians(df["longitude"].values - lon0) * EARTH_RADIUS_KM * cos_lat0
    df["proj_y_km"] = np.radians(df["latitude"].values - lat0) * EARTH_RADIUS_KM

    return df


# -----------------------------------------------------------------------------
# Core Spatiotemporal Clustering
# -----------------------------------------------------------------------------
def spatiotemporal_cluster(
    df: pd.DataFrame,
    spatial_radius_km: float = DEFAULT_SPATIAL_RADIUS_KM,
    temporal_window_hours: float = DEFAULT_TEMPORAL_WINDOW_HOURS,
    max_duration_hours: float = DEFAULT_MAX_EVENT_DURATION_HOURS,
    max_extent_km: float = DEFAULT_MAX_EVENT_DIAMETER_KM,
) -> Tuple[np.ndarray, int, int]:
    """
    Executes scalable sliding-window KDTree clustering with bounded Union-Find.
    Returns:
      - cluster_labels: array of root IDs for each detection
      - total_merged_edges: number of pairwise edges successfully merged
      - rejected_chaining_edges: number of edges rejected by bounding constraints
    """
    logger.info("Spatiotemporal clustering started:")
    logger.info(f"  -> Spatial Radius:        {spatial_radius_km} km")
    logger.info(f"  -> Temporal Window:       {temporal_window_hours} hours")
    logger.info(f"  -> Max Event Duration:    {max_duration_hours} hours")
    logger.info(f"  -> Max Event Diameter:    {max_extent_km} km")

    n_rows = len(df)
    x = df["proj_x_km"].values
    y = df["proj_y_km"].values
    t = df["epoch_hours"].values

    buf = BoundedUnionFind(
        n=n_rows,
        x=x,
        y=y,
        t_hours=t,
        max_duration_hours=max_duration_hours,
        max_extent_km=max_extent_km,
    )

    # Sliding temporal blocks
    block_hours = 48.0
    step_hours = max(1.0, block_hours - temporal_window_hours)
    max_time = float(t.max())
    cur_time = 0.0

    coords_2d = np.column_stack((x, y))
    total_merged = 0
    t_start = time.time()
    block_count = 0

    while cur_time <= max_time:
        block_count += 1
        mask = (t >= cur_time) & (t <= cur_time + block_hours)
        idx = np.where(mask)[0]

        if len(idx) > 1:
            block_coords = coords_2d[idx]
            block_t = t[idx]

            tree = KDTree(block_coords)
            pairs = tree.query_pairs(r=spatial_radius_km)

            for i_rel, j_rel in pairs:
                if abs(block_t[i_rel] - block_t[j_rel]) <= temporal_window_hours:
                    orig_i = idx[i_rel]
                    orig_j = idx[j_rel]
                    if buf.union(orig_i, orig_j):
                        total_merged += 1

        cur_time += step_hours

    # Resolve all roots
    labels = np.array([buf.find(i) for i in range(n_rows)], dtype=np.int32)
    duration = round(time.time() - t_start, 2)
    unique_clusters = len(np.unique(labels))

    logger.info(f"Clustering completed in {duration}s:")
    logger.info(f"  -> Blocks processed:        {block_count}")
    logger.info(f"  -> Edges merged:            {total_merged:,}")
    logger.info(f"  -> Chaining edges rejected: {buf.rejected_chaining_edges:,}")
    logger.info(f"  -> Total events created:    {unique_clusters:,}")

    return labels, total_merged, buf.rejected_chaining_edges


# -----------------------------------------------------------------------------
# Event-Level Feature Aggregation & Relational Links
# -----------------------------------------------------------------------------
def build_event_records(
    df: pd.DataFrame,
    labels: np.ndarray,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes all canonical event-level attributes and constructs the
    event-to-detection relational link table.
    """
    logger.info("Aggregating canonical event-level features...")
    t0 = time.time()
    df_work = df.copy()
    df_work["cluster_root"] = labels

    # 1. Deterministic Event Ordering & ID Generation
    # Sort clusters chronologically by their earliest detection
    cluster_order = (
        df_work.groupby("cluster_root")
        .agg(
            first_time=("acq_dt", "min"),
            mean_lat=("latitude", "mean"),
        )
        .sort_values(by=["first_time", "mean_lat"])
        .reset_index()
    )

    cluster_order["event_index"] = np.arange(1, len(cluster_order) + 1)
    cluster_order["event_id"] = cluster_order["event_index"].apply(
        lambda idx: f"TT-EVT-{idx:08d}"
    )

    id_map = dict(zip(cluster_order["cluster_root"], cluster_order["event_id"]))
    df_work["event_id"] = df_work["cluster_root"].map(id_map)

    # 2. Relational Link Table
    links_df = df_work[["event_id", "detection_id"]].copy()

    # 3. Vectorized Event Aggregation
    # Pre-create indicator columns for native C aggregations
    df_work["is_day"] = (df_work["daynight"] == "D").astype(np.int32)
    df_work["is_night"] = (df_work["daynight"] == "N").astype(np.int32)
    df_work["is_conf_h"] = (df_work["confidence"] == "h").astype(np.int32)
    df_work["is_conf_n"] = (df_work["confidence"] == "n").astype(np.int32)
    df_work["is_conf_l"] = (df_work["confidence"] == "l").astype(np.int32)
    df_work["has_n20"] = (df_work["satellite"] == "N20").astype(np.int8)
    df_work["has_n21"] = (df_work["satellite"] == "N21").astype(np.int8)
    df_work["src_sp"] = (df_work["source"] == "VIIRS_NOAA20_SP").astype(np.int8)
    df_work["src_nrt20"] = (df_work["source"] == "VIIRS_NOAA20_NRT").astype(np.int8)
    df_work["src_nrt21"] = (df_work["source"] == "VIIRS_NOAA21_NRT").astype(np.int8)

    grouped = df_work.groupby("event_id")

    # Aggregating core metrics using native C routines
    event_agg = grouped.agg(
        start_time=("acq_datetime", "min"),
        end_time=("acq_datetime", "max"),
        centroid_lat=("latitude", "mean"),
        centroid_lon=("longitude", "mean"),
        min_proj_x=("proj_x_km", "min"),
        max_proj_x=("proj_x_km", "max"),
        min_proj_y=("proj_y_km", "min"),
        max_proj_y=("proj_y_km", "max"),
        detection_count=("detection_id", "count"),
        has_n20=("has_n20", "max"),
        has_n21=("has_n21", "max"),
        max_frp_mw=("frp", "max"),
        mean_frp_mw=("frp", "mean"),
        median_frp_mw=("frp", "median"),
        sum_frp_mw=("frp", "sum"),
        max_bright_ti4=("bright_ti4", "max"),
        mean_bright_ti4=("bright_ti4", "mean"),
        max_bright_ti5=("bright_ti5", "max"),
        mean_bright_ti5=("bright_ti5", "mean"),
        day_detection_count=("is_day", "sum"),
        night_detection_count=("is_night", "sum"),
        confidence_high_count=("is_conf_h", "sum"),
        confidence_nominal_count=("is_conf_n", "sum"),
        confidence_low_count=("is_conf_l", "sum"),
        src_sp=("src_sp", "max"),
        src_nrt20=("src_nrt20", "max"),
        src_nrt21=("src_nrt21", "max"),
    ).reset_index()

    # Vectorized satellite mapping
    event_agg["unique_satellite_count"] = (
        event_agg["has_n20"] + event_agg["has_n21"]
    ).astype(np.int8)
    both_mask = (event_agg["has_n20"] == 1) & (event_agg["has_n21"] == 1)
    n20_mask = (event_agg["has_n20"] == 1) & (event_agg["has_n21"] == 0)
    n21_mask = (event_agg["has_n20"] == 0) & (event_agg["has_n21"] == 1)

    sat_series = pd.Series("N20", index=event_agg.index)
    sat_series[both_mask] = "N20,N21"
    sat_series[n21_mask] = "N21"
    event_agg["satellites"] = sat_series

    # Vectorized source product count
    event_agg["source_product_count"] = (
        event_agg["src_sp"] + event_agg["src_nrt20"] + event_agg["src_nrt21"]
    ).astype(np.int8)

    event_agg = event_agg.drop(
        columns=["has_n20", "has_n21", "src_sp", "src_nrt20", "src_nrt21"]
    )

    # Calculate duration in hours
    t_start = pd.to_datetime(event_agg["start_time"])
    t_end = pd.to_datetime(event_agg["end_time"])
    event_agg["duration_hours"] = (
        (t_end - t_start).dt.total_seconds() / 3600.0
    ).astype(np.float32)

    # Calculate spatial extent in km (bounding diameter; 0.0 for singletons)
    dx = event_agg["max_proj_x"] - event_agg["min_proj_x"]
    dy = event_agg["max_proj_y"] - event_agg["min_proj_y"]
    extent = np.sqrt(dx**2 + dy**2)
    # If detection_count == 1, extent is exactly 0.0
    extent = np.where(event_agg["detection_count"] == 1, 0.0, extent)
    event_agg["spatial_extent_km"] = extent.astype(np.float32)

    # Drop temporary projection bounding columns
    event_agg = event_agg.drop(
        columns=["min_proj_x", "max_proj_x", "min_proj_y", "max_proj_y"]
    )

    # 4. Event Quality Flagging
    # Categories: NORMAL, SINGLE_DETECTION, LARGE_SPATIAL_SPREAD, LONG_TEMPORAL_SPREAD
    quality_series = pd.Series("NORMAL", index=event_agg.index)
    quality_series[event_agg["detection_count"] == 1] = "SINGLE_DETECTION"
    quality_series[
        (event_agg["detection_count"] > 1) & (event_agg["spatial_extent_km"] > 10.0)
    ] = "LARGE_SPATIAL_SPREAD"
    quality_series[
        (event_agg["detection_count"] > 1) & (event_agg["duration_hours"] > 24.0)
    ] = "LONG_TEMPORAL_SPREAD"
    event_agg["event_quality"] = quality_series

    # Reorder columns to canonical schema
    canonical_event_columns = [
        "event_id",
        "start_time",
        "end_time",
        "duration_hours",
        "centroid_lat",
        "centroid_lon",
        "spatial_extent_km",
        "detection_count",
        "unique_satellite_count",
        "satellites",
        "max_frp_mw",
        "mean_frp_mw",
        "median_frp_mw",
        "sum_frp_mw",
        "max_bright_ti4",
        "mean_bright_ti4",
        "max_bright_ti5",
        "mean_bright_ti5",
        "day_detection_count",
        "night_detection_count",
        "confidence_high_count",
        "confidence_nominal_count",
        "confidence_low_count",
        "source_product_count",
        "event_quality",
    ]
    event_agg = event_agg[canonical_event_columns].sort_values("event_id").reset_index(drop=True)

    logger.info(f"Built {len(event_agg):,} event objects in {time.time()-t0:.2f}s")
    return event_agg, links_df


# -----------------------------------------------------------------------------
# Parameter Sensitivity Analysis Experiment
# -----------------------------------------------------------------------------
def run_parameter_sensitivity(
    df: pd.DataFrame,
    sample_size: int = 132420,
) -> List[Dict[str, Any]]:
    """
    Runs benchmark sensitivity experiment across the 6 requested parameter combinations
    on a representative peak-season subset.
    """
    logger.info("=" * 65)
    logger.info(f"Running Parameter Sensitivity Experiment on {sample_size:,} sample...")
    logger.info("=" * 65)

    # Use April 2026 peak fire season sample
    sub = df[(df["acq_dt"] >= "2026-04-10") & (df["acq_dt"] <= "2026-04-16")].copy()
    if len(sub) > sample_size:
        sub = sub.iloc[:sample_size].copy()

    logger.info(f"Representative subset size: {len(sub):,} detections")

    configs = [
        (1.0, 3.0),
        (1.0, 6.0),
        (1.0, 12.0),
        (2.0, 6.0),
        (2.0, 12.0),
        (5.0, 6.0),
    ]

    sensitivity_results = []

    for r_km, win_h in configs:
        t0 = time.time()
        labels, merged, rejected = spatiotemporal_cluster(
            sub,
            spatial_radius_km=r_km,
            temporal_window_hours=win_h,
            max_duration_hours=DEFAULT_MAX_EVENT_DURATION_HOURS,
            max_extent_km=DEFAULT_MAX_EVENT_DIAMETER_KM,
        )

        sub["cluster_root"] = labels
        event_sizes = sub.groupby("cluster_root")["detection_id"].count()
        n_events = len(event_sizes)
        n_singletons = int((event_sizes == 1).sum())
        pct_singletons = round((n_singletons / n_events) * 100.0, 2)
        med_size = float(event_sizes.median())
        max_size = int(event_sizes.max())

        durations = sub.groupby("cluster_root")["epoch_hours"].agg(lambda h: float(h.max() - h.min()))
        med_dur = float(round(durations.median(), 2))
        max_dur = float(round(durations.max(), 2))

        duration_sec = round(time.time() - t0, 2)

        record = {
            "spatial_radius_km": r_km,
            "temporal_window_hours": win_h,
            "total_events": n_events,
            "median_event_size": med_size,
            "max_event_size": max_size,
            "percentage_singletons": pct_singletons,
            "median_duration_hours": med_dur,
            "max_duration_hours": max_dur,
            "edges_merged": merged,
            "chaining_edges_rejected": rejected,
            "computation_time_seconds": duration_sec,
        }
        sensitivity_results.append(record)

    logger.info("Sensitivity experiment completed successfully.")
    return sensitivity_results


# -----------------------------------------------------------------------------
# Reporting & Exporting
# -----------------------------------------------------------------------------
def export_event_outputs(
    events_df: pd.DataFrame,
    links_df: pd.DataFrame,
    output_dir: Path,
) -> Tuple[Path, Path, Path]:
    """
    Exports events to Parquet and CSV, and links to Parquet.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    events_parquet = output_dir / "events_v0_1.parquet"
    events_csv = output_dir / "events_v0_1.csv"
    links_parquet = output_dir / "event_detection_links.parquet"

    logger.info(f"Writing {events_parquet}...")
    events_df.to_parquet(events_parquet, index=False, engine="pyarrow")

    logger.info(f"Writing {events_csv}...")
    events_df.to_csv(events_csv, index=False)

    logger.info(f"Writing {links_parquet}...")
    links_df.to_parquet(links_parquet, index=False, engine="pyarrow")

    logger.info("Output files exported successfully:")
    logger.info(f"  -> Events Parquet: {events_parquet} ({events_parquet.stat().st_size / (1024*1024):.1f} MB)")
    logger.info(f"  -> Events CSV:     {events_csv} ({events_csv.stat().st_size / (1024*1024):.1f} MB)")
    logger.info(f"  -> Links Parquet:  {links_parquet} ({links_parquet.stat().st_size / (1024*1024):.1f} MB)")

    return events_parquet, events_csv, links_parquet


def generate_event_quality_report(
    total_detections: int,
    events_df: pd.DataFrame,
    links_df: pd.DataFrame,
    sensitivity_results: List[Dict[str, Any]],
    parameters: Dict[str, Any],
    reports_dir: Path,
    start_time: float,
) -> Dict[str, Any]:
    """
    Generates machine-readable JSON quality report and Markdown summary.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    duration_sec = round(time.time() - start_time, 2)

    total_events = len(events_df)
    singletons = int((events_df["detection_count"] == 1).sum())
    multi_events = total_events - singletons
    pct_multi_detections = round(
        (events_df[events_df["detection_count"] > 1]["detection_count"].sum() / total_detections) * 100.0, 2
    )

    sat_stats = events_df["satellites"].value_counts().to_dict()
    quality_stats = events_df["event_quality"].value_counts().to_dict()

    report = {
        "metadata": {
            "module": ENGINE_MODULE,
            "version": ENGINE_VERSION,
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "execution_duration_seconds": duration_sec,
        },
        "parameters_used": parameters,
        "executive_summary": {
            "total_input_detections": total_detections,
            "total_events_created": total_events,
            "detections_assigned_to_events": len(links_df),
            "unassigned_detections": total_detections - len(links_df),
            "single_detection_events": singletons,
            "multi_detection_events": multi_events,
            "percentage_detections_in_multi_events": pct_multi_detections,
        },
        "event_size_statistics": {
            "min_detections_per_event": int(events_df["detection_count"].min()),
            "median_detections_per_event": float(events_df["detection_count"].median()),
            "mean_detections_per_event": float(round(events_df["detection_count"].mean(), 2)),
            "max_detections_per_event": int(events_df["detection_count"].max()),
        },
        "temporal_statistics_hours": {
            "min_duration_hours": float(round(events_df["duration_hours"].min(), 2)),
            "median_duration_hours": float(round(events_df["duration_hours"].median(), 2)),
            "mean_duration_hours": float(round(events_df["duration_hours"].mean(), 2)),
            "max_duration_hours": float(round(events_df["duration_hours"].max(), 2)),
        },
        "spatial_extent_statistics_km": {
            "min_spatial_extent_km": float(round(events_df["spatial_extent_km"].min(), 2)),
            "median_spatial_extent_km": float(round(events_df["spatial_extent_km"].median(), 2)),
            "mean_spatial_extent_km": float(round(events_df["spatial_extent_km"].mean(), 2)),
            "max_spatial_extent_km": float(round(events_df["spatial_extent_km"].max(), 2)),
        },
        "satellite_breakdown": {
            "events_by_satellite_combination": {str(k): int(v) for k, v in sat_stats.items()},
            "dual_satellite_events_count": int((events_df["unique_satellite_count"] == 2).sum()),
        },
        "event_quality_distribution": {str(k): int(v) for k, v in quality_stats.items()},
        "parameter_sensitivity_experiment": sensitivity_results,
    }

    json_path = reports_dir / "eventization_quality_report.json"
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)

    # Markdown Summary
    md_path = reports_dir / "eventization_quality_summary.md"
    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write(f"""# ThermoTrace - Event Engine v0.1 Quality Summary
**Engine Module**: `{ENGINE_MODULE}` | **Version**: `{ENGINE_VERSION}`  
**Executed At**: `{report['metadata']['executed_at_utc']}` | **Duration**: `{duration_sec}s`

---

## 1. Executive Summary
- **Total Input Detections**: `{total_detections:,}`
- **Total Spatiotemporal Events**: `{total_events:,}`
- **Single-Detection Events**: `{singletons:,}` ({singletons/total_events*100:.2f}%)
- **Multi-Detection Events**: `{multi_events:,}` ({multi_events/total_events*100:.2f}%)
- **Detections in Multi-Events**: `{pct_multi_detections}%`
- **Unassigned Detections**: `0` (100% assigned)

## 2. Event Dimensions & Statistics
- **Detections per Event**: Median: `{report['event_size_statistics']['median_detections_per_event']}` | Max: `{report['event_size_statistics']['max_detections_per_event']}`
- **Event Duration**: Median: `{report['temporal_statistics_hours']['median_duration_hours']}h` | Max: `{report['temporal_statistics_hours']['max_duration_hours']}h`
- **Spatial Extent**: Median: `{report['spatial_extent_statistics_km']['median_spatial_extent_km']} km` | Max: `{report['spatial_extent_statistics_km']['max_spatial_extent_km']} km`
- **Dual-Sensor (N20 + N21) Events**: `{report['satellite_breakdown']['dual_satellite_events_count']:,}`

## 3. Configuration Parameters
- **Spatial Radius**: `{parameters['spatial_radius_km']} km`
- **Temporal Window**: `{parameters['temporal_window_hours']} hours`
- **Max Event Duration**: `{parameters['max_duration_hours']} hours`
- **Max Event Diameter**: `{parameters['max_extent_km']} km`

## 4. Parameter Sensitivity Benchmark Table
| Spatial Radius | Temporal Window | Total Events | Median Size | Max Size | % Singletons | Max Duration |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
""")
        for s in sensitivity_results:
            fp.write(
                f"| {s['spatial_radius_km']} km | {s['temporal_window_hours']} h | "
                f"{s['total_events']:,} | {s['median_event_size']} | {s['max_event_size']} | "
                f"{s['percentage_singletons']}% | {s['max_duration_hours']} h |\n"
            )

        fp.write("""
---
*Note: Event objects represent localized spatiotemporal detection clusters. They are not confirmed industrial incidents or facility assignments.*
""")

    logger.info(f"Quality report written: {json_path}")
    logger.info(f"Quality summary written: {md_path}")
    return report


# -----------------------------------------------------------------------------
# Main Runner
# -----------------------------------------------------------------------------
def run_event_pipeline(
    input_parquet: Path,
    output_dir: Path,
    reports_dir: Path,
    spatial_radius_km: float = DEFAULT_SPATIAL_RADIUS_KM,
    temporal_window_hours: float = DEFAULT_TEMPORAL_WINDOW_HOURS,
    max_duration_hours: float = DEFAULT_MAX_EVENT_DURATION_HOURS,
    max_extent_km: float = DEFAULT_MAX_EVENT_DIAMETER_KM,
    run_sensitivity: bool = True,
) -> Dict[str, Any]:
    """
    Executes the full Event Engine pipeline.
    """
    start_time = time.time()
    logger.info("=" * 65)
    logger.info("Starting ThermoTrace Event Engine v0.1 (Module M3)")
    logger.info("=" * 65)

    params = {
        "spatial_radius_km": spatial_radius_km,
        "temporal_window_hours": temporal_window_hours,
        "max_duration_hours": max_duration_hours,
        "max_extent_km": max_extent_km,
    }

    # 1. Ingest
    df = load_canonical_firms(input_parquet)
    total_detections = len(df)

    # 2. Parameter Sensitivity (if requested)
    sensitivity_results = []
    if run_sensitivity:
        sensitivity_results = run_parameter_sensitivity(df)

    # 3. Spatiotemporal Clustering
    labels, merged_edges, rejected_edges = spatiotemporal_cluster(
        df,
        spatial_radius_km=spatial_radius_km,
        temporal_window_hours=temporal_window_hours,
        max_duration_hours=max_duration_hours,
        max_extent_km=max_extent_km,
    )

    # 4. Feature Aggregation & Links
    events_df, links_df = build_event_records(df, labels)

    # 5. Export Datasets
    export_event_outputs(events_df, links_df, output_dir)

    # 6. Quality Reports
    report = generate_event_quality_report(
        total_detections=total_detections,
        events_df=events_df,
        links_df=links_df,
        sensitivity_results=sensitivity_results,
        parameters=params,
        reports_dir=reports_dir,
        start_time=start_time,
    )

    duration = round(time.time() - start_time, 2)
    logger.info("=" * 65)
    logger.info(f"Event Engine v0.1 Completed Successfully in {duration}s")
    logger.info(f"Events Created: {len(events_df):,} | Links: {len(links_df):,}")
    logger.info("=" * 65)
    return report


def main():
    root = Path(__file__).resolve().parents[2]
    # Default canonical input location
    default_input = (
        root / "processed" / "firms_india_canonical.parquet"
        if (root / "processed" / "firms_india_canonical.parquet").exists()
        else root / "data" / "processed" / "firms" / "firms_india_canonical.parquet"
    )
    default_output = root / "processed" / "events"
    default_reports = root / "reports" / "events"

    parser = argparse.ArgumentParser(
        description="ThermoTrace Event Engine v0.1 (Module M3 Spatiotemporal Clustering)"
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=default_input,
        help="Path to canonical FIRMS Parquet dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output,
        help="Output directory for events and relational links",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=default_reports,
        help="Output directory for quality and sensitivity reports",
    )
    parser.add_argument(
        "--spatial-radius-km",
        type=float,
        default=DEFAULT_SPATIAL_RADIUS_KM,
        help="Spatial neighbor distance threshold in km (default: 1.0)",
    )
    parser.add_argument(
        "--temporal-window-hours",
        type=float,
        default=DEFAULT_TEMPORAL_WINDOW_HOURS,
        help="Temporal linkage window in hours (default: 6.0)",
    )
    parser.add_argument(
        "--max-duration-hours",
        type=float,
        default=DEFAULT_MAX_EVENT_DURATION_HOURS,
        help="Maximum allowable contiguous event duration in hours (default: 48.0)",
    )
    parser.add_argument(
        "--max-extent-km",
        type=float,
        default=DEFAULT_MAX_EVENT_DIAMETER_KM,
        help="Maximum allowable spatial diameter in km (default: 15.0)",
    )
    parser.add_argument(
        "--skip-sensitivity",
        action="store_true",
        help="Skip parameter sensitivity benchmarking",
    )

    args = parser.parse_args()
    try:
        run_event_pipeline(
            input_parquet=args.input_file,
            output_dir=args.output_dir,
            reports_dir=args.reports_dir,
            spatial_radius_km=args.spatial_radius_km,
            temporal_window_hours=args.temporal_window_hours,
            max_duration_hours=args.max_duration_hours,
            max_extent_km=args.max_extent_km,
            run_sensitivity=not args.skip_sensitivity,
        )
    except Exception as e:
        logger.error(f"Event Engine failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
