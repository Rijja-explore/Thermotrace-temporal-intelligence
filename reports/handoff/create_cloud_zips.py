"""
ThermoTrace Cloud Package Zipper
================================

Creates compressed ZIP packages of the large geospatial assets for cloud transfer.
Calculates SHA-256 checksums of the resulting ZIP archives and updates cloud_data_manifest.json.
"""

import zipfile
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(r"d:\New folder (2)")
STAGE = ROOT / "cloud_handoff"
MANIFEST_PATH = ROOT / "reports" / "handoff" / "cloud_data_manifest.json"

PACKAGES = [
    {
        "zip_rel": "osm/osm_india_package.zip",
        "files": [
            ("osm/osm_india.gpkg", "osm_india.gpkg"),
            ("osm/india-260901.osm.pbf", "india-260901.osm.pbf")
        ],
        "dataset_id": "osm_india_package"
    },
    {
        "zip_rel": "population/population_india_package.zip",
        "files": [
            ("population/population_india_100m.tif", "population_india_100m.tif"),
            ("population/ind_pop_2025_CN_100m_R2025A_v1.tif", "ind_pop_2025_CN_100m_R2025A_v1.tif")
        ],
        "dataset_id": "population_india_package"
    },
    {
        "zip_rel": "worldcover/worldcover_india_mosaic.zip",
        "files": [
            ("worldcover/worldcover_india_10m.tif", "worldcover_india_10m.tif")
        ],
        "dataset_id": "worldcover_india_mosaic_package"
    },
    {
        "zip_rel": "protected_areas/protected_areas_india.zip",
        "files": [
            ("protected_areas/protected_areas_india.gpkg", "protected_areas_india.gpkg")
        ],
        "dataset_id": "protected_areas_package"
    },
    {
        "zip_rel": "features/event_features_v2_package.zip",
        "files": [
            ("features/event_features_v2.parquet", "event_features_v2.parquet")
        ],
        "dataset_id": "event_features_v2_package"
    }
]

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(16 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def create_packages():
    print("=" * 80)
    print("CREATING COMPRESSED ZIP PACKAGES FOR CLOUD TRANSFER")
    print("=" * 80)

    zip_results = {}

    for pkg in PACKAGES:
        zip_path = STAGE / pkg["zip_rel"]
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nCompressing {pkg['zip_rel']}...")
        t0 = time.time()

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for src_rel, arcname in pkg["files"]:
                src_file = STAGE / src_rel
                if src_file.exists():
                    print(f"  Adding {src_rel} ({round(src_file.stat().st_size / (1024**2), 2)} MB)...")
                    zf.write(src_file, arcname=arcname)
                else:
                    print(f"  Warning: {src_file} missing!")

        sz_mb = zip_path.stat().st_size / (1024 * 1024)
        cksum = sha256_file(zip_path)
        dur = time.time() - t0
        print(f"  Created {pkg['zip_rel']}: {sz_mb:.2f} MB in {dur:.1f}s")
        print(f"  SHA-256: {cksum}")

        zip_results[pkg["dataset_id"]] = {
            "archive_path": str(zip_path.relative_to(ROOT)),
            "archive_size_mb": round(sz_mb, 2),
            "archive_sha256": cksum,
            "duration_seconds": round(dur, 1)
        }

    # Update cloud manifest
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["zip_packages"] = zip_results
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        # Also mirror to cloud_handoff/metadata
        (STAGE / "metadata" / "cloud_data_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("\nUpdated cloud_data_manifest.json with zip archives metadata.")

    print("\n" + "=" * 80)
    print("ALL CLOUD ZIP PACKAGES SUCCESSFULLY CREATED")
    print("=" * 80)

if __name__ == "__main__":
    create_packages()
