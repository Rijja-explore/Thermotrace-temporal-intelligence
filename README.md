# ThermoTrace: Temporal & Spatial Thermal Anomaly Analytics

**Subcontinent Scale (India): Multi-Modal Geospatial Data Engineering & Feature Foundation**  
*Repository:* [ThermoTrace Temporal Intelligence](https://github.com/Rijja-explore/Thermotrace-temporal-intelligence)  
*Branch:* `member1-data-handoff`  
*Lead Author:* Member 1 (Data Engineering & Geospatial Pipeline Lead)  
*Status:* Phase 1 Complete (Ingestion, Canonicalization, Eventization, and Feature Engineering V1/V2 Verified)  

---

## 1. System Architecture Overview

ThermoTrace ingests, canonicalizes, clusters, and enriches satellite thermal observations and high-resolution contextual geospatial layers across the entire continental extent of India ($65^\circ\text{E} - 100^\circ\text{E}, 5^\circ\text{N} - 38^\circ\text{N}$).

```
RAW DATA (Immutable Source Layer)
├── FIRMS VIIRS/MODIS CSVs (148 files)
├── OpenStreetMap India PBF (1.63 GB)
├── WorldPop 2025 100m GeoTIFF (742 MB)
├── UNEP-WCMC WDPA Protected Areas (3 ZIPs)
└── ESA WorldCover 10m Tiles (91 GeoTIFFs, 6.4 GB)
                           │
                           ▼
SOURCE-SPECIFIC CANONICAL DATASETS (Layer-1 GeoPackages & COGs)
├── data/processed/osm/osm_india.gpkg (169k facilities, 1.1M infra)
├── data/processed/population/population_india_100m.tif (100m COG)
├── data/processed/protected_areas/protected_areas_india.gpkg (WDPA boundaries)
└── data/processed/worldcover/worldcover_india_10m.tif (10m Land Cover Mosaic)
                           │
                           ▼
FIRMS CANONICAL DETECTIONS (Layer-0)
└── data/processed/firms/firms_india_canonical.parquet (2,477,543 detections)
                           │
                           ▼
M3 THERMAL EVENT ENGINE (Layer-1)
├── data/processed/events/events_v0_1.parquet (996,891 clustered events)
└── data/processed/events/event_detection_links.parquet (2,477,543 relational links)
                           │
                           ▼
EVENT-LEVEL FEATURE ENGINE (Layer-2 & Layer-3)
├── data/processed/features/event_features_v1.parquet (65 canonical features)
└── data/processed/features/event_features_v2.parquet (144 features + Baseline Risk)
                           │
                           ▼
DOWNSTREAM INTELLIGENCE (Member 2: Expansion | Member 3: ML | Member 4: UI)
```

---

## 2. The Core Parquet Handoff Datasets

The analytical pipeline separates raw detection points, grouped cluster objects, and feature-enriched rows into distinct layers. **Never merge these layers into one replacement file.**

```
FIRMS DETECTION POINT (2,477,543 rows)
       │
       ▼ [Spatiotemporal Union-Find: <1km radius, <6h temporal window, chaining guards]
M3 THERMAL EVENT CLUSTER (996,891 rows)
       │
       ▼ [Geospatial Enrichment: Population, Land Cover, Distances, Recurrence, Risk]
EVENT FEATURE ROW (996,891 rows, 65 V1 / 144 V2 features)
```

### 1. FIRMS Canonical Detections
* **Path:** [`data/processed/firms/firms_india_canonical.parquet`](file:///d:/New%20folder%20(2)/data/processed/firms/firms_india_canonical.parquet)
* **Size:** 67.60 MB | **Row Count:** 2,477,543 detections
* **Grain:** 1 row = 1 satellite thermal detection point (VIIRS / MODIS).
* **Git Status:** In Git.

### 2. M3 Thermal Events
* **Path:** [`data/processed/events/events_v0_1.parquet`](file:///d:/New%20folder%20(2)/data/processed/events/events_v0_1.parquet)
* **Size:** 41.00 MB | **Row Count:** 996,891 events
* **Grain:** 1 row = 1 spatio-temporally grouped thermal event cluster (`event_id`).
* **Git Status:** In Git.

### 3. Event-to-Detection Relational Bridge
* **Path:** [`data/processed/events/event_detection_links.parquet`](file:///d:/New%20folder%20(2)/data/processed/events/event_detection_links.parquet)
* **Size:** 33.00 MB | **Row Count:** 2,477,543 links
* **Grain:** Relational join table mapping every `detection_id` to its parent `event_id`.
* **Git Status:** In Git.

### 4. Integrated Event Features V1
* **Path:** [`data/processed/features/event_features_v1.parquet`](file:///d:/New%20folder%20(2)/data/processed/features/event_features_v1.parquet)
* **Size:** 93.98 MB | **Row Count:** 996,891 rows | **Columns:** 65
* **Grain:** 1 row = 1 event enriched with base thermal, temporal, population, WDPA, OSM, and WorldCover features.
* **Git Status:** In Git.

### 5. Advanced Event Features V2 & Baseline Risk Engine
* **Path:** [`data/processed/features/event_features_v2.parquet`](file:///d:/New%20folder%20(2)/data/processed/features/event_features_v2.parquet)
* **Size:** 210.97 MB | **Row Count:** 996,891 rows | **Columns:** 144
* **Grain:** 1 row = 1 event with leak-free recurrence (7d/30d/90d), multi-scale spatial density (1km/5km/10km), cyclical time, and Explainable Baseline Risk Scores.
* **Cloud Status:** Staged for Google Drive (exceeds GitHub 100MB limit).

---

## 3. Large Geospatial Assets & Cloud Storage (Google Drive)

Large raster and vector datasets that exceed standard Git repository constraints are staged in Google Drive:

* **Official Cloud Storage Folder:** [Google Drive - ThermoTrace Datasets](https://drive.google.com/drive/folders/1orP0iv660wOhkpOB2NPIj_ZzxUoMvzKe?usp=sharing)
* **Cloud Manifest:** [`reports/handoff/cloud_data_manifest.json`](file:///d:/New%20folder%20(2)/reports/handoff/cloud_data_manifest.json)

| Dataset | Local Destination | Size | SHA-256 Checksum |
|---|---|---|---|
| **OSM India GeoPackage** | `data/processed/osm/osm_india.gpkg` | 737.67 MB | `0555c3d021427a59bde4fab7f84f2d92598b3dbb674be59c1cec42fc058690c8` |
| **OSM India Raw PBF** | `data/raw/osm/india/india-260901.osm.pbf` | 1,626.74 MB | `5c65b1e536cccd140a947a97fe51a45475b2bab32d12a7b7821048881e49b678` |
| **WorldPop 100m Raster** | `data/processed/population/population_india_100m.tif` | 1,083.21 MB | `cfb1d2434430902e405d68ba720ee9f6f8f96c2bc4955a5982616af5e4736a79` |
| **WorldPop Raw TIF** | `data/raw/population/ind_pop_2025_CN_100m_R2025A_v1.tif` | 742.06 MB | `f5717c622d79052d4aacf0f67365165575855ba8059375b5d87ea655ed26fa53` |
| **WorldCover 10m Mosaic**| `data/processed/worldcover/worldcover_india_10m.tif` | 3,306.27 MB | `c5c62163351ad7ee6653f20cf9ee7d6ebb3927167c9842e172f46101cf13f720` |
| **Event Features V2** | `data/processed/features/event_features_v2.parquet` | 210.97 MB | `b27b63333d29e72dccb0ad999664289de6d86a4a50ef1d4a5aba11ed58f5b1cc` |

---

## 4. Repository Directory Structure

```
.
├── .gitignore                      # Configured to exclude huge rasters/vectors while keeping code, tests, and Parquets
├── data/
│   ├── README.md                   # Data storage policy and layer documentation
│   ├── data_manifest.yaml          # Master machine-readable data architecture manifest
│   ├── raw/                        # Immutable raw assets (FIRMS, OSM, WorldPop, WDPA, WorldCover)
│   ├── processed/                  # Canonical processed datasets (firms, events, osm, population, wdpa, features)
│   └── reports/                    # Quality assurance and distribution reports
├── data_pipeline/
│   ├── firms/                      # Layer-0 FIRMS canonical ingestion ETL
│   ├── events/                     # Layer-1 M3 spatio-temporal cluster engine
│   ├── osm/                        # OSM facility and infrastructure vector processors
│   ├── population/                 # WorldPop 100m windowed extraction engine
│   ├── protected_areas/            # UNEP-WCMC WDPA spatial containment engine
│   ├── worldcover/                 # ESA WorldCover 10m sampling and mosaic builder
│   ├── features/                   # Event feature engineering engine (V1 & V2)
│   └── handoff/                    # Integrity verifiers and cloud restoration utilities
├── reports/
│   ├── handoff/                    # Member-1 handoff reports, manifests, and inventories
│   ├── features/                   # V1 & V2 quality summaries and schema dictionaries
│   ├── firms/                      # Layer-0 QA distribution and schema reports
│   ├── events/                     # M3 cluster QA reports
│   ├── osm/                        # OSM facility counts and boundary inspection
│   ├── population/                 # Population distribution and chunked statistics
│   └── protected_areas/            # WDPA polygon and point attribute audits
└── tests/                          # 74 automated unit, integration, and QA tests (100% passing)
```

---

## 5. Quickstart & Verification Guide

### 1. Verify Dataset Integrity & SHA-256 Checksums
```bash
python data_pipeline/handoff/verify_handoff_checksums.py
```

### 2. Run All Automated Tests (74 Tests)
```bash
pytest tests/ -v
```

### 3. Re-run Event Feature Pipeline
```bash
# Generate V1 Canonical Feature Table (65 columns):
python -m data_pipeline.features.build_event_features --v1

# Generate V2 Canonical Feature Table (144 columns, ~78s):
python -m data_pipeline.features.build_event_features --v2
```

---

## 6. Handoff Notes for Next-Stage Members

* **Member 2 (ETL & Pipeline Maintenance):** All ingestion code is centralized in `data_pipeline/`. Future FIRMS data can be ingested directly with `data_pipeline/firms/canonical_etl.py`.
* **Member 3 (Machine Learning & Modeling):** Ingest `event_features_v1.parquet` or `event_features_v2.parquet`. All historical recurrence features (`events_previous_7d`, `events_previous_30d`, etc.) are guaranteed **100% leak-free** ($t < T$).
* **Member 4 (Frontend UI & Dashboards):** Pre-computed `baseline_risk_score`, `baseline_risk_level`, and `risk_reason_1/2/3` are ready for direct dashboard badging and map overlays.
