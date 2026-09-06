# ThermoTrace Data Asset Architecture & Storage Guidelines

This directory contains the multi-source data repository for the ThermoTrace project.

---

## 1. Directory Structure

```
data/
├── raw/                         # IMMUTABLE SOURCE ASSETS (NEVER MODIFY OR COMMIT)
│   ├── firms/                   # VIIRS and MODIS CSV archives
│   ├── osm/                     # OpenStreetMap PBF extracts (india-260901.osm.pbf)
│   ├── population/              # WorldPop 2025 India 100m GeoTIFF (ind_pop_2025_...tif)
│   ├── worldcover/              # ESA WorldCover 10m 2021 v200 GeoTIFF tiles (91 tiles)
│   ├── protected_areas/         # UNEP-WCMC WDPA ZIP archives
│   ├── boundaries/              # Survey of India boundary files (pending)
│   ├── weather/                 # Meteorological rasters (Layer-2)
│   ├── sentinel2/               # High-res optical imagery (Layer-2)
│   └── landsat/                 # Thermal infrared imagery (Layer-2)
│
├── processed/                   # CANONICAL PROCESSED REPOSITORIES
│   ├── firms/                   # firms_india_canonical.parquet
│   ├── events/                  # events_v0_1.parquet & event_detection_links.parquet
│   ├── osm/                     # osm_india.gpkg (facilities & infrastructure layers)
│   ├── population/              # population_india_100m.tif (tiled COG with pyramids)
│   ├── worldcover/              # worldcover_india_10m.tif
│   ├── protected_areas/         # protected_areas_india.gpkg (polygons & points)
│   ├── boundaries/              # india_admin.gpkg (pending)
│   └── features/                # event_features_v1.parquet & event_features_v2.parquet
│
└── reports/                     # GENERATED AUDIT & QUALITY ASSURANCE REPORTS
    ├── firms/
    ├── events/
    ├── osm/
    ├── population/
    ├── worldcover/
    ├── protected_areas/
    ├── boundaries/
    └── features/
```

---

## 2. Immutable vs Generated Files

| Directory / File | Type | Policy |
|---|---|---|
| `data/raw/*` | Raw Input | **STRICTLY IMMUTABLE.** Never edit, rename, overwrite, or delete. |
| `data/processed/firms/` | Canonical Layer-1 | Authoritative processed detections. |
| `data/processed/events/` | Canonical Layer-1 | Spatio-temporal event clusters (`events_v0_1.parquet`). |
| `data/processed/osm/` | Canonical Layer-1 | Consolidated facilities and infrastructure GeoPackage. |
| `data/processed/population/`| Canonical Layer-1 | Cloud-Optimized GeoTIFF raster. |
| `data/processed/protected_areas/` | Canonical Layer-1 | WDPA boundary polygons and points GeoPackage. |
| `data/processed/features/` | Derived Analytical | Feature tables (`event_features_v1.parquet`, `event_features_v2.parquet`). |

---

## 3. How to Obtain Datasets
1. **FIRMS Satellite Thermal Data:** Download via NASA Earthdata FIRMS portal for India bounding box `[68.1, 6.5, 97.4, 35.7]`.
2. **OpenStreetMap Data:** Download `india-latest.osm.pbf` from Geofabrik.
3. **WorldPop Population:** Download WorldPop 2025 India 100m unconstrained raster from `worldpop.org`.
4. **UNEP-WCMC WDPA:** Download WDPA September 2026 release for IND from `protectedplanet.net`.
5. **ESA WorldCover:** Download 91 tiles from `https://esa-worldcover.s3.eu-central-1.amazonaws.com`.

---

## 4. Git Exclusion Policy
Due to file sizes exceeding GitHub limits (total data directory exceeds 15 GB):
* **DO NOT COMMIT:** Any `.tif`, `.pbf`, `.gpkg`, `.parquet`, `.zip`, `.tar.gz`, or `.part` files.
* **DO COMMIT:** Metadata JSONs, small configuration YAMLs, schemas, documentation, and QA reports.
* Exclusions are strictly managed via the root `.gitignore` file.

---

## 5. How to Reproduce Processed Outputs

```bash
# 1. Regenerate OSM GeoPackage from raw PBF:
python -m data_pipeline.osm.qa_osm_gpkg

# 2. Regenerate Feature Engineering V1 (996,891 events):
python -m data_pipeline.features.build_event_features --v1

# 3. Regenerate Feature Engineering V2 (996,891 events):
python -m data_pipeline.features.build_event_features --v2

# 4. Run automated verification:
pytest tests/ -v
```
