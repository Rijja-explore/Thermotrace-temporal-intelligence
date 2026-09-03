"""
ThermoTrace Cloud Data Manifest Generator
=========================================

Compiles reports/handoff/cloud_data_manifest.json with exact checksums,
cloud staging destinations, spatial metadata, and restoration instructions.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"d:\New folder (2)")
OUT_FILE = ROOT / "reports" / "handoff" / "cloud_data_manifest.json"

CLOUD_DATASETS = [
    {
        "dataset_id": "osm_india_canonical",
        "dataset_version": "1.0.0",
        "layer": "osm",
        "local_source_path": "data/processed/osm/osm_india.gpkg",
        "cloud_package_path": "ThermoTrace/datasets/osm/osm_india.gpkg",
        "original_filename": "osm_india.gpkg",
        "archive_filename": None,
        "size_bytes": 773496832,
        "size_mb": 737.67,
        "sha256": "0555c3d021427a59bde4fab7f84f2d92598b3dbb674be59c1cec42fc058690c8",
        "crs": "EPSG:4326 (WGS84)",
        "resolution": "Vector",
        "spatial_extent": "India Subcontinent [68.1E, 6.5N, 97.4E, 35.7N]",
        "temporal_coverage": "2026-09-01 Snapshot",
        "source": "OpenStreetMap India (Geofabrik)",
        "purpose": "Authoritative consolidated industrial facilities and infrastructure network vectors",
        "downstream_users": ["Member 1", "Member 2", "Member 3"],
        "restoration_instructions": "Download osm_india.gpkg and place into data/processed/osm/osm_india.gpkg"
    },
    {
        "dataset_id": "osm_india_raw_pbf",
        "dataset_version": "260901",
        "layer": "osm",
        "local_source_path": "data/raw/osm/india/india-260901.osm.pbf",
        "cloud_package_path": "ThermoTrace/datasets/osm/india-260901.osm.pbf",
        "original_filename": "india-260901.osm.pbf",
        "archive_filename": None,
        "size_bytes": 1705764974,
        "size_mb": 1626.74,
        "sha256": "5c65b1e536cccd140a947a97fe51a45475b2bab32d12a7b7821048881e49b678",
        "crs": "EPSG:4326",
        "resolution": "Raw Protocolbuffer",
        "spatial_extent": "India Subcontinent",
        "temporal_coverage": "2026-09-01",
        "source": "Geofabrik OpenStreetMap",
        "purpose": "Immutable raw OSM data extraction source",
        "downstream_users": ["Member 1 (Data Engineering Lineage)"],
        "restoration_instructions": "Download india-260901.osm.pbf and place into data/raw/osm/india/india-260901.osm.pbf"
    },
    {
        "dataset_id": "population_india_canonical",
        "dataset_version": "1.0.0",
        "layer": "population",
        "local_source_path": "data/processed/population/population_india_100m.tif",
        "cloud_package_path": "ThermoTrace/datasets/population/population_india_100m.tif",
        "original_filename": "population_india_100m.tif",
        "archive_filename": None,
        "size_bytes": 1135868846,
        "size_mb": 1083.21,
        "sha256": "cfb1d2434430902e405d68ba720ee9f6f8f96c2bc4955a5982616af5e4736a79",
        "crs": "EPSG:4326",
        "resolution": "100m (0.0008333 deg)",
        "spatial_extent": "India Subcontinent [68.1E, 6.5N, 97.4E, 35.7N]",
        "temporal_coverage": "2025 Projection",
        "source": "WorldPop 2025 R2025A v1",
        "purpose": "Canonical Cloud-Optimized GeoTIFF raster of population density",
        "downstream_users": ["Member 3", "Member 4"],
        "restoration_instructions": "Download population_india_100m.tif and place into data/processed/population/population_india_100m.tif"
    },
    {
        "dataset_id": "population_india_raw_tif",
        "dataset_version": "2025_v1",
        "layer": "population",
        "local_source_path": "data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif",
        "cloud_package_path": "ThermoTrace/datasets/population/ind_pop_2025_CN_100m_R2025A_v1.tif",
        "original_filename": "ind_pop_2025_CN_100m_R2025A_v1.tif",
        "archive_filename": None,
        "size_bytes": 778106191,
        "size_mb": 742.06,
        "sha256": "f5717c622d79052d4aacf0f67365165575855ba8059375b5d87ea655ed26fa53",
        "crs": "EPSG:4326",
        "resolution": "100m",
        "spatial_extent": "India Subcontinent",
        "temporal_coverage": "2025 Projection",
        "source": "WorldPop",
        "purpose": "Immutable raw population GeoTIFF source file",
        "downstream_users": ["Member 1 (Lineage)"],
        "restoration_instructions": "Download ind_pop_2025_CN_100m_R2025A_v1.tif and place into data/raw/population/"
    },
    {
        "dataset_id": "worldcover_india_mosaic_canonical",
        "dataset_version": "1.0.0",
        "layer": "worldcover",
        "local_source_path": "data/processed/worldcover/worldcover_india_10m.tif",
        "cloud_package_path": "ThermoTrace/datasets/worldcover/worldcover_india_10m.tif",
        "original_filename": "worldcover_india_10m.tif",
        "archive_filename": None,
        "size_bytes": 3466858496,
        "size_mb": 3306.27,
        "sha256": "c5c62163351ad7ee6653f20cf9ee7d6ebb3927167c9842e172f46101cf13f720",
        "crs": "EPSG:4326",
        "resolution": "10m (0.0000833 deg)",
        "spatial_extent": "India Subcontinent [68.1E, 6.5N, 97.4E, 35.7N]",
        "temporal_coverage": "2021 Reference Epoch",
        "source": "ESA WorldCover 2021 v200",
        "purpose": "Canonical 10m land cover classification mosaic covering the subcontinent",
        "downstream_users": ["Member 3", "Member 4"],
        "restoration_instructions": "Download worldcover_india_10m.tif and place into data/processed/worldcover/worldcover_india_10m.tif"
    },
    {
        "dataset_id": "worldcover_india_raw_tiles",
        "dataset_version": "2021_v200",
        "layer": "worldcover",
        "local_source_path": "data/raw/worldcover/india/",
        "cloud_package_path": "ThermoTrace/datasets/worldcover/worldcover_india_raw_tiles.zip",
        "original_filename": "india/*.tif",
        "archive_filename": "worldcover_india_raw_tiles.zip",
        "size_bytes": 6718000000,
        "size_mb": 6406.8,
        "sha256": "PREPARED_ON_ARCHIVE",
        "crs": "EPSG:4326",
        "resolution": "10m per tile",
        "spatial_extent": "91 Tile Grid across India",
        "temporal_coverage": "2021",
        "source": "ESA WorldCover AWS S3",
        "purpose": "91 immutable raw 10m GeoTIFF classification tiles",
        "downstream_users": ["Member 1 (Lineage)"],
        "restoration_instructions": "Extract worldcover_india_raw_tiles.zip into data/raw/worldcover/india/"
    },
    {
        "dataset_id": "protected_areas_canonical",
        "dataset_version": "1.0.0",
        "layer": "protected_areas",
        "local_source_path": "data/processed/protected_areas/protected_areas_india.gpkg",
        "cloud_package_path": "ThermoTrace/datasets/protected_areas/protected_areas_india.gpkg",
        "original_filename": "protected_areas_india.gpkg",
        "archive_filename": None,
        "size_bytes": 5128192,
        "size_mb": 4.89,
        "sha256": "ecbcd4697ee22cdb64e6ed700712d27c193ff983202cfd178bfd7ef9d905e340",
        "crs": "EPSG:4326",
        "resolution": "Vector",
        "spatial_extent": "India Subcontinent",
        "temporal_coverage": "September 2026",
        "source": "UNEP-WCMC Protected Planet WDPA",
        "purpose": "Canonical protected area boundaries and point buffers",
        "downstream_users": ["Member 3", "Member 4"],
        "restoration_instructions": "Download protected_areas_india.gpkg and place into data/processed/protected_areas/protected_areas_india.gpkg"
    },
    {
        "dataset_id": "event_features_v2_canonical",
        "dataset_version": "2.0.0",
        "layer": "features",
        "local_source_path": "data/processed/features/event_features_v2.parquet",
        "cloud_package_path": "ThermoTrace/datasets/features/event_features_v2.parquet",
        "original_filename": "event_features_v2.parquet",
        "archive_filename": None,
        "size_bytes": 221217066,
        "size_mb": 210.97,
        "sha256": "b27b63333d29e72dccb0ad999664289de6d86a4a50ef1d4a5aba11ed58f5b1cc",
        "crs": "EPSG:4326",
        "resolution": "1 Row per Event (144 Features)",
        "spatial_extent": "India Subcontinent",
        "temporal_coverage": "2024-01-01 to 2024-12-31",
        "source": "ThermoTrace Feature Engineering Engine V2",
        "purpose": "Full 144-feature table with baseline risk scores (exceeds GitHub 100MB limit)",
        "downstream_users": ["Member 3 (ML Training)", "Member 4 (UI Dashboard)"],
        "restoration_instructions": "Download event_features_v2.parquet and place into data/processed/features/event_features_v2.parquet"
    }
]

manifest = {
    "cloud_manifest_version": "2.0.0",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "cloud_storage_provider": "Google Drive",
    "cloud_root_url": "https://drive.google.com/drive/folders/1orP0iv660wOhkpOB2NPIj_ZzxUoMvzKe?usp=sharing",
    "total_cloud_datasets": len(CLOUD_DATASETS),
    "total_cloud_volume_mb": round(sum(d["size_mb"] for d in CLOUD_DATASETS), 2),
    "total_cloud_volume_gb": round(sum(d["size_mb"] for d in CLOUD_DATASETS) / 1024, 2),
    "datasets": CLOUD_DATASETS
}

OUT_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Generated Cloud Data Manifest: {OUT_FILE}")
print(f"Total datasets staged for cloud: {manifest['total_cloud_datasets']}")
print(f"Total cloud volume: {manifest['total_cloud_volume_gb']} GB")
