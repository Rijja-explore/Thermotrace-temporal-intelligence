"""
ThermoTrace Cloud Handoff Staging Script
========================================

Stages all large datasets into cloud_handoff/ structure using zero-copy NTFS hard links.
Preserves original integrity and creates clean organization for Google Drive upload.
"""

import os
import shutil
from pathlib import Path

ROOT = Path(r"d:\New folder (2)")
STAGE = ROOT / "cloud_handoff"

def stage_file(src_rel: str, dst_rel: str):
    src = ROOT / src_rel
    dst = STAGE / dst_rel
    if not src.exists():
        print(f"Warning: Source file {src} not found!")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
        print(f"Hardlinked {src_rel} -> cloud_handoff/{dst_rel}")
    except Exception:
        shutil.copy2(src, dst)
        print(f"Copied {src_rel} -> cloud_handoff/{dst_rel}")

def main():
    print("Staging cloud datasets into cloud_handoff/...")

    # 1. OSM
    stage_file("data/processed/osm/osm_india.gpkg", "osm/osm_india.gpkg")
    stage_file("data/raw/osm/india/india-260901.osm.pbf", "osm/india-260901.osm.pbf")

    # 2. Population
    stage_file("data/processed/population/population_india_100m.tif", "population/population_india_100m.tif")
    stage_file("data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif", "population/ind_pop_2025_CN_100m_R2025A_v1.tif")

    # 3. WorldCover
    stage_file("data/processed/worldcover/worldcover_india_10m.tif", "worldcover/worldcover_india_10m.tif")

    # 4. Protected Areas
    stage_file("data/processed/protected_areas/protected_areas_india.gpkg", "protected_areas/protected_areas_india.gpkg")

    # 5. Features V2 (large Parquet > 100MB)
    stage_file("data/processed/features/event_features_v2.parquet", "features/event_features_v2.parquet")

    # 6. Metadata
    stage_file("data/data_manifest.yaml", "metadata/data_manifest.yaml")
    stage_file("reports/handoff/cloud_data_manifest.json", "metadata/cloud_data_manifest.json")

    print("\nCloud handoff staging complete!")

if __name__ == "__main__":
    main()
