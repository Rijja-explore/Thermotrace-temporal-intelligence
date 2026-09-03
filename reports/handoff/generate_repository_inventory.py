"""
ThermoTrace Repository Inventory Generator
==========================================

Scans all files across the repository and categorizes them by:
- purpose, source layer, and data tier (raw / canonical / derived / intermediate)
- downstream requirements (Member 2 / 3 / 4)
- Git tracking suitability vs Cloud staging requirement
- Removability criteria for duplicate/redundant assets
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"d:\New folder (2)")
OUT_FILE = ROOT / "reports" / "handoff" / "member1_repository_inventory.json"

def classify_file(p: Path, rel: str, sz: int, ext: str):
    rel_posix = rel.replace("\\", "/")
    
    # Defaults
    purpose = "General project asset"
    layer = "infrastructure"
    tier = "intermediate"
    downstream = False
    git_cand = False
    cloud_cand = False
    removable = False
    removal_reason = ""

    # 1. Source code and tests
    if rel_posix.startswith("data_pipeline/") or rel_posix.startswith("tests/"):
        layer = "pipeline_code"
        tier = "canonical"
        purpose = "Pipeline execution script or automated test"
        downstream = True
        if "__pycache__" in rel_posix or ext in [".pyc", ".pyo"]:
            tier = "intermediate"
            removable = True
            removal_reason = "Byte-compiled Python cache"
        else:
            git_cand = True

    # 2. Reports, documentation, configuration
    elif rel_posix.startswith("reports/") or rel_posix.startswith("data/reports/") or rel_posix in ["README.md", "data/README.md", ".gitignore"]:
        layer = "documentation_and_reports"
        tier = "canonical"
        purpose = "Technical documentation, QA report, or schema definition"
        downstream = True
        git_cand = True

    # 3. Canonical processed datasets
    elif rel_posix.startswith("data/processed/"):
        layer = rel_posix.split("/")[2] if len(rel_posix.split("/")) > 2 else "processed"
        tier = "canonical"
        downstream = True
        if "event_features_v1.parquet" in rel_posix:
            purpose = "Approved V1 integrated event feature analytical dataset (65 features)"
            git_cand = True
            cloud_cand = True
        elif "events_v0_1.parquet" in rel_posix:
            purpose = "Approved M3 thermal event cluster dataset"
            git_cand = True
            cloud_cand = True
        elif "event_detection_links.parquet" in rel_posix:
            purpose = "Relational bridge between raw FIRMS detections and M3 events"
            git_cand = True
            cloud_cand = True
        elif "firms_india_canonical.parquet" in rel_posix:
            purpose = "Approved canonical FIRMS thermal detections dataset"
            git_cand = True
            cloud_cand = True
        elif "event_features_v2.parquet" in rel_posix:
            purpose = "V2 analytical feature table (144 features, 210 MB - exceeds GitHub 100MB limit)"
            cloud_cand = True
        elif ext in [".tif", ".gpkg"]:
            purpose = f"Canonical Layer-1 processed {layer} asset"
            cloud_cand = True

    # 4. Raw datasets
    elif rel_posix.startswith("data/raw/"):
        layer = rel_posix.split("/")[2] if len(rel_posix.split("/")) > 2 else "raw"
        tier = "raw"
        downstream = True
        # Check if it is a duplicate tile in data/raw/worldcover/ (not in india/)
        if rel_posix.startswith("data/raw/worldcover/") and not rel_posix.startswith("data/raw/worldcover/india/"):
            removable = True
            removal_reason = "Duplicate WorldCover tile of identical tile in data/raw/worldcover/india/"
            tier = "intermediate"
            purpose = "Duplicate raw tile"
        else:
            purpose = f"Immutable raw {layer} source data"
            cloud_cand = True

    # 5. External redundant duplicate folders
    elif rel_posix.startswith("osm/"):
        layer = "osm"
        tier = "intermediate"
        removable = True
        removal_reason = "Duplicate of data/raw/osm/india/india-260901.osm.pbf"
        purpose = "Root-level duplicate OSM PBF"

    elif rel_posix.startswith("population/"):
        layer = "population"
        tier = "intermediate"
        removable = True
        removal_reason = "Duplicate of data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif"
        purpose = "Root-level duplicate population raster"

    elif rel_posix.startswith("firms_data/"):
        layer = "firms"
        tier = "intermediate"
        removable = True
        removal_reason = "Duplicate workspace of ThermoTrace_FIRMS_Downloader and data/raw/firms"
        purpose = "Duplicate FIRMS downloader workspace"

    elif rel_posix.startswith("ThermoTrace_FIRMS_Downloader/"):
        layer = "firms"
        if rel_posix.endswith(".csv"):
            removable = True
            removal_reason = "Redundant uncompressed CSV export (Parquet canonical exists)"
            purpose = "Redundant CSV export"
        else:
            tier = "intermediate"
            removable = True
            removal_reason = "Auxiliary downloader workspace; all raw CSVs exist in data/raw/firms/ and pipeline code in data_pipeline/"
            purpose = "Auxiliary downloader workspace"

    elif rel_posix.startswith("ThermoTrace_WorldCover_Downloader/"):
        layer = "worldcover"
        tier = "intermediate"
        removable = True
        removal_reason = "Auxiliary downloader workspace; all 91 tiles exist in data/raw/worldcover/india/"
        purpose = "Auxiliary WorldCover downloader workspace"

    elif rel_posix.startswith("ThermoTrace_ProtectedAREA/"):
        layer = "protected_areas"
        tier = "intermediate"
        removable = True
        removal_reason = "Unzipped WDPA files; canonical GPKG exists in data/processed/protected_areas/ and raw archives in data/raw/protected_areas/"
        purpose = "Extracted WDPA files"

    elif ".pytest_cache" in rel_posix:
        layer = "testing"
        tier = "intermediate"
        removable = True
        removal_reason = "Temporary pytest cache"

    return {
        "path": rel_posix,
        "file_type": ext or "no_extension",
        "size_bytes": sz,
        "size_mb": round(sz / (1024 * 1024), 3),
        "purpose": purpose,
        "source_layer": layer,
        "data_tier": tier,
        "required_by_downstream_members": downstream,
        "git_candidate": git_cand,
        "cloud_candidate": cloud_cand,
        "removable_candidate": removable,
        "removal_rationale": removal_reason
    }

def main():
    records = []
    total_sz = 0

    for p in ROOT.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(ROOT))
            sz = p.stat().st_size
            ext = p.suffix.lower()
            total_sz += sz
            records.append(classify_file(p, rel, sz, ext))

    summary = {
        "inventory_generated_at": datetime.now(timezone.utc).isoformat(),
        "total_files_scanned": len(records),
        "total_volume_mb": round(total_sz / (1024 * 1024), 2),
        "total_volume_gb": round(total_sz / (1024 * 1024 * 1024), 2),
        "git_candidate_count": sum(1 for r in records if r["git_candidate"]),
        "git_candidate_volume_mb": round(sum(r["size_mb"] for r in records if r["git_candidate"]), 2),
        "cloud_candidate_count": sum(1 for r in records if r["cloud_candidate"]),
        "cloud_candidate_volume_mb": round(sum(r["size_mb"] for r in records if r["cloud_candidate"]), 2),
        "removable_candidate_count": sum(1 for r in records if r["removable_candidate"]),
        "removable_candidate_volume_mb": round(sum(r["size_mb"] for r in records if r["removable_candidate"]), 2),
        "file_records": sorted(records, key=lambda x: x["path"])
    }

    OUT_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Generated repository inventory: {OUT_FILE}")
    print(f"Total files: {summary['total_files_scanned']}")
    print(f"Total size: {summary['total_volume_gb']} GB")
    print(f"Git candidates: {summary['git_candidate_count']} files ({summary['git_candidate_volume_mb']} MB)")
    print(f"Cloud candidates: {summary['cloud_candidate_count']} files ({summary['cloud_candidate_volume_mb']} MB)")
    print(f"Removable candidates: {summary['removable_candidate_count']} files ({summary['removable_candidate_volume_mb']} MB)")

if __name__ == "__main__":
    main()
