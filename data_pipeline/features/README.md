# ThermoTrace Feature Engineering Engine (V1 & V2)

**Handoff Documentation & Technical Reference Manual**  
*Project:* ThermoTrace (Advanced Spatio-Temporal Thermal Anomaly Analytics)  
*Version:* 2.0.0  
*Target Dataset:* India Continental Subcontinent (996,891 M3 Cluster Events)  

---

## Table of Contents
1. [Overview & Purpose](#1-overview--purpose)
2. [Data Consumed & Ingestion Lineage](#2-data-consumed--ingestion-lineage)
3. [Source Asset Storage Map](#3-source-asset-storage-map)
4. [What V1 Contains](#4-what-v1-contains)
5. [What V2 Contains](#5-what-v2-contains)
6. [Folder Structure](#6-folder-structure)
7. [Module Directory & File Inventory](#7-module-directory--file-inventory)
8. [How to Run the Pipeline](#8-how-to-run-the-pipeline)
9. [How to Run Automated Test Suites](#9-how-to-run-automated-test-suites)
10. [Expected Outputs](#10-expected-outputs)
11. [Feature Groups & Specifications](#11-feature-groups--specifications)
12. [Mathematical Formulations](#12-mathematical-formulations)
13. [Data Lineage & Traceability Graph](#13-data-lineage--traceability-graph)
14. [Null Value Semantics & Boundary Handling](#14-null-value-semantics--boundary-handling)
15. [Explainable Baseline Risk Methodology](#15-explainable-baseline-risk-methodology)
16. [Risk Score Limitations & Disclaimers](#16-risk-score-limitations--disclaimers)
17. [How Recurrence Is Calculated](#17-how-recurrence-is-calculated)
18. [How Spatial Density Is Calculated](#18-how-spatial-density-is-calculated)
19. [Zero Temporal Leakage Guarantee](#19-zero-temporal-leakage-guarantee)
20. [How to Add a New Feature](#20-how-to-add-a-new-feature)
21. [How to Add a New Data Source](#21-how-to-add-a-new-data-source)
22. [Immutable Datasets (NEVER Modify)](#22-immutable-datasets-never-modify)
23. [Canonical vs Derived Datasets](#23-canonical-vs-derived-datasets)
24. [Connection to Future ML / Modeling Layer](#24-connection-to-future-ml--modeling-layer)
25. [Connection to Future ThermoTrace UI](#25-connection-to-future-thermotrace-ui)
26. [Known Limitations](#26-known-limitations)
27. [Troubleshooting Guide](#27-troubleshooting-guide)
28. [Git, LFS & Storage Instructions](#28-git-lfs--storage-instructions)
29. [Handoff Checklist](#29-handoff-checklist)

---

### 1. Overview & Purpose
The ThermoTrace Feature Engineering engine bridges raw multi-modal geospatial data (satellite thermal detections, population censuses, protected area boundaries, OpenStreetMap infrastructure networks, and high-resolution land cover) into unified, canonical event-level analytical feature tables:
* **`event_features_v1.parquet`**: Base multi-source enrichment (65 features).
* **`event_features_v2.parquet`**: Advanced behavioural, leak-free recurrence, spatial density, exposure indicators, explainable baseline risk scores, and contextual reason tags (144 total features).

**Critical Grain Rule:**  
**1 Event = Exactly 1 Row**. Every record corresponds to a single spatio-temporal M3 thermal cluster event (`event_id`). Spatial and multi-detection relationships are aggregated, never multiplied.

---

### 2. Data Consumed & Ingestion Lineage
The feature engine consumes data from six independent sources:
1. **FIRMS M3 Thermal Clusters:** Spatio-temporal event clusters derived from VIIRS (VNP14IMGTDL, VJ114IMGTDL, VJ214IMGTDL) and MODIS (MOD14/MYD14).
2. **WorldPop 2025 India Population:** 100m Cloud-Optimized GeoTIFF raster of estimated human population density.
3. **UNEP-WCMC World Database on Protected Areas (WDPA):** September 2026 release of official national parks, wildlife sanctuaries, and conservation reserves across India.
4. **OpenStreetMap (OSM) India:** Canonical extraction of 169,927 industrial facilities and 1,137,267 infrastructure features.
5. **ESA WorldCover 10m 2021 v200:** 91 Cloud-Optimized GeoTIFF tiles providing 11-class global land cover classification.
6. **Administrative Boundaries:** Country assignment ("India") with documented pending status awaiting official Survey of India boundary ingestion.

---

### 3. Source Asset Storage Map
```
data/
├── raw/                                # STRICTLY IMMUTABLE (NEVER OVERWRITE)
│   ├── firms/                          # Raw VIIRS / MODIS CSV downloads
│   ├── osm/india/india-260901.osm.pbf  # Raw 1.7 GB OSM India extract
│   ├── population/ind_pop_2025_...tif  # Raw 778 MB WorldPop raster
│   ├── worldcover/india/               # 91 Raw WorldCover 10m GeoTIFF tiles (6.4 GB)
│   └── protected_areas/                # Raw UNEP-WCMC WDPA ZIP archives
│
└── processed/                          # CANONICAL PROCESSED REPOSITORIES
    ├── events/events_v0_1.parquet      # 996,891 M3 thermal events
    ├── osm/osm_india.gpkg              # Layer-1 GeoPackage (facilities + infra)
    ├── population/population_...tif    # Layer-1 100m tiled COG with pyramids
    ├── protected_areas/...gpkg         # Layer-1 GeoPackage (63 polygons + 27 points)
    └── features/
        ├── event_features_v1.parquet   # 65 canonical features (93.98 MB)
        └── event_features_v2.parquet   # 144 canonical features (210.97 MB)
```

---

### 4. What V1 Contains
`event_features_v1.parquet` contains **65 canonical features**:
* Base M3 Cluster: `event_id`, `start_time`, `end_time`, `duration_hours`, `centroid_lat`, `centroid_lon`, `spatial_extent_km`, `detection_count`, `unique_satellite_count`, `satellites`, `max_frp_mw`, `mean_frp_mw`, `median_frp_mw`, `sum_frp_mw`, `event_quality`.
* Temporal: `year`, `month`, `day`, `day_of_week`, `hour`, `season`, `is_day`, `is_night`, `is_weekend`.
* Population: `population_at_event`, `population_1km`, `population_5km`, `population_density_1km`, `population_density_5km`.
* Conservation: `inside_protected_area`, `protected_area_id`, `protected_area_name`, `protected_area_designation`, `distance_to_protected_area_km`, `protected_area_within_1km`, `protected_area_within_5km`.
* Industrial Context: `nearest_facility_id`, `nearest_facility_type`, `nearest_facility_name`, `distance_to_facility_km`, proximity flags (`near_power_plant`, `near_factory`, `near_refinery`, `near_mine`, `near_quarry`, `near_storage_facility`, `near_substation`).
* Infrastructure Corridors: `distance_to_major_road_km`, `distance_to_railway_km`, `distance_to_power_line_km`, `distance_to_pipeline_km`, `distance_to_airport_km`, `distance_to_port_km`.
* Land Cover: `landcover_class`, `landcover_name`, `forest_fraction_1km`, `cropland_fraction_1km`, `builtup_fraction_1km`, `grassland_fraction_1km`, `water_fraction_1km`.
* Administrative: `country`, `state`, `state_code`, `district`, `district_code` (nullable).

---

### 5. What V2 Contains
`event_features_v2.parquet` appends **79 advanced features** (total: **144 columns**):
* **Thermal Behaviour (10 features):** `log_max_frp`, `log_mean_frp`, `log_sum_frp`, `thermal_intensity`, `thermal_frp_variability`, `thermal_frp_per_detection`, `thermal_frp_per_hour`, `thermal_detection_density`, `thermal_persistence_indicator`, `thermal_concentration_indicator`.
* **Cyclical Temporal (6 features):** `hour_sin`, `hour_cos`, `month_sin`, `month_cos`, `day_of_week_sin`, `day_of_week_cos`.
* **Historical Recurrence (10 features - Leak-Free):** `events_previous_7d`, `events_previous_30d`, `events_previous_90d`, `frp_previous_7d`, `frp_previous_30d`, `frp_previous_90d`, `active_days_previous_7d`, `active_days_previous_30d`, `active_days_previous_90d`, `time_since_previous_event_hours`.
* **Spatial Density (8 features):** `events_local_1km`, `events_local_5km`, `events_local_10km`, `thermal_density_1km`, `thermal_density_5km`, `thermal_density_10km`, `events_local_7d`, `events_local_30d`.
* **Population Exposure (4 features):** `population_exposure_score`, `high_population_exposure_flag`, `population_density_class`, `population_pressure_indicator`.
* **Environmental Sensitivity (6 features):** `forest_exposure_score`, `cropland_exposure_score`, `builtup_exposure_score`, `grassland_exposure_score`, `natural_land_fraction`, `environmental_sensitivity_score`.
* **Conservation Sensitivity (3 features):** `conservation_sensitivity_score`, `protected_area_alert_flag`, `protected_area_proximity_class`.
* **Industrial Context (9 features):** `industrial_proximity_score`, `industrial_context_flag`, context flags (`power_generation_context`, `factory_context`, `quarry_context`, `refinery_context`, `mining_context`, `storage_context`, `substation_context`).
* **Infrastructure Context (6 features):** `road_proximity_score`, `railway_proximity_score`, `power_infrastructure_proximity`, `pipeline_proximity_score`, `transport_corridor_flag`, `infrastructure_context_score`.
* **Data Quality & Confidence (5 features):** `multi_satellite_confirmation`, `data_confidence_score`, `high_confidence_event`, `low_confidence_event`, `event_observation_quality`.
* **Baseline Risk Engine (9 features):** `thermal_risk_component`, `exposure_risk_component`, `environmental_risk_component`, `conservation_risk_component`, `industrial_context_component`, `infrastructure_context_component`, `recurrence_component`, `baseline_risk_score`, `baseline_risk_level`.
* **Contextual Explanations (3 features):** `risk_reason_1`, `risk_reason_2`, `risk_reason_3`.

---

### 6. Folder Structure
```
data_pipeline/features/
├── __init__.py                     # Package re-exports for backward compatibility
├── README.md                       # This technical reference manual
├── build_event_features.py         # Master CLI orchestrator (triggers V1 or V2)
│
├── v1/                             # V1 Feature Pipeline (Preserved)
│   ├── __init__.py
│   ├── spatial_features.py         # Spherical cKDTree & Haversine distance
│   ├── temporal_features.py        # Astronomical & IMD seasons
│   ├── raster_features.py          # Windowed population & WorldCover sampling
│   ├── protected_area_features.py  # STRtree polygon containment & distance
│   ├── osm_features.py             # OSM facility & infrastructure distance
│   ├── boundary_features.py        # Administrative hierarchy fallback
│   ├── feature_schema.py           # V1 Schema dictionary
│   └── feature_config.yaml         # Configuration & thresholds
│
├── v2/                             # V2 Feature Pipeline
│   ├── __init__.py
│   ├── thermal_features.py         # Radiative intensity & concentration
│   ├── temporal_features.py        # Sinusoidal cyclical encodings
│   ├── recurrence_features.py      # Leak-free temporal recurrence (7d/30d/90d)
│   ├── spatial_density_features.py # Fixed-grid multi-scale clustering
│   ├── population_features.py      # Exposure scores & settlement classes
│   ├── landcover_features.py       # Fuel load & ecological vulnerability
│   ├── conservation_features.py    # Protected area sensitivity & alerts
│   ├── industrial_features.py      # OSM facility proximity scoring
│   ├── infrastructure_features.py  # Transport & utility corridor flags
│   ├── quality_confidence_features.py # Observation quality & multi-sat confirmation
│   ├── risk_indicators.py          # Explainable baseline risk engine
│   ├── risk_explanations.py        # Top-3 contextual risk driver tags
│   ├── validation.py               # Rigorous 22-point assertion engine
│   └── build_v2_features.py        # V2 execution pipeline & report generator
│
└── utils/                          # Shared Utility Functions
    ├── __init__.py
    ├── io.py                       # Safe Parquet / GeoPackage reading & writing
    ├── spatial.py                  # Haversine & grid hash calculations
    └── logging.py                  # Structured console formatting
```

---

### 7. Module Directory & File Inventory
* `build_event_features.py`: Accepts `--v1` or `--v2` (default: V2). Invokes `build_v2_features.py` or chunked V1 builder.
* `v2/thermal_features.py`: Implements log1p transforms, FRP variability, persistence ratio.
* `v2/temporal_features.py`: Implements diurnal `sin/cos(2*pi*hour/24)`, annual `sin/cos(2*pi*month/12)`, weekly `sin/cos(2*pi*dow/7)`.
* `v2/recurrence_features.py`: Sorts chronologically, groups into discrete spatial cells ($0.05^\circ$), and queries prior activity with `searchsorted` ($t < T$).
* `v2/spatial_density_features.py`: Computes spatial clustering counts across 1km, 5km, and 10km grid resolutions.
* `v2/population_features.py`: Maps population densities to 5 settlement tiers (`UNINHABITED` to `URBAN_DENSE`) and continuous exposure scores.
* `v2/landcover_features.py`: Computes fuel load sensitivity from tree cover, cropland, grassland, and built-up fractions.
* `v2/conservation_features.py`: Computes exponential distance decay score from protected area boundaries.
* `v2/industrial_features.py`: Evaluates proximity to 7 OSM industrial facility categories.
* `v2/infrastructure_features.py`: Quantifies proximity to transport and utility networks.
* `v2/quality_confidence_features.py`: Classifies detection confidence and sensor agreement.
* `v2/risk_indicators.py`: Synthesizes 7 component scores into unified `baseline_risk_score` (0–100) and severity rating (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
* `v2/risk_explanations.py`: Assigns `risk_reason_1`, `risk_reason_2`, `risk_reason_3`.
* `v2/validation.py`: Enforces mathematical bounds, zero temporal leakage, non-negativity, and schema consistency.

---

### 8. How to Run the Pipeline

#### A. Generate V2 Canonical Dataset (Full 996,891 Events)
```bash
python -m data_pipeline.features.build_event_features --v2
# or directly:
python -m data_pipeline.features.v2.build_v2_features
```
*Duration:* **~78 seconds** across 1 million rows.

#### B. Run in Sample Mode (e.g. 1,000 Events for Fast Validation)
```bash
python -m data_pipeline.features.v2.build_v2_features 1000
```

#### C. Regenerate V1 Dataset from Raw Sources (Full 996,891 Events)
```bash
python -m data_pipeline.features.build_event_features --v1
```

---

### 9. How to Run Automated Test Suites
Both V1 and V2 have independent, comprehensive pytest test suites:

```bash
# Run V2 22-point test suite (Passing 22/22)
pytest tests/test_event_features_v2.py -v

# Run V1 20-point regression test suite (Passing 20/20)
pytest tests/test_event_features.py -v

# Run all project tests
pytest tests/ -v
```

---

### 10. Expected Outputs
Running the pipeline produces:
* **`data/processed/features/event_features_v2.parquet`**: 210.97 MB, 996,891 rows, 144 columns.
* **`reports/features/event_features_v2_schema.json`**: Machine-readable schema documenting every feature, data type, formula, and lineage.
* **`reports/features/event_features_v2_quality_report.json`**: Comprehensive statistical distribution report and cardinalities.
* **`reports/features/event_features_v2_quality_summary.md`**: Executive summary with breakdown of risk tiers, component averages, and top drivers.

---

### 11. Feature Groups & Specifications
| Feature Group | Features | Input Sources | Output Types |
|---|---|---|---|
| **Thermal Behaviour** | 10 | M3 Cluster attributes | `float32` (MW, log, ratios) |
| **Temporal Cyclical** | 6 | Event timestamps | `float32` [-1.0, 1.0] |
| **Historical Recurrence** | 10 | Spatial coordinates + time | `int32`, `float32`, `int16` |
| **Spatial Density** | 8 | Coordinates + Recurrence | `int32`, `float32` (events/km²) |
| **Population Exposure** | 4 | WorldPop 100m metrics | `float32`, `boolean`, `string` |
| **Land-Cover Sensitivity**| 6 | ESA WorldCover fractions | `float32` [0.0 - 100.0] |
| **Conservation Sensitivity**| 3 | WDPA spatial joins | `float32`, `boolean`, `string` |
| **Industrial Context** | 9 | OSM industrial facilities | `float32`, `boolean` |
| **Infrastructure Context**| 6 | OSM transport & utility networks | `float32`, `boolean` |
| **Quality & Confidence** | 5 | Sensor counts & detections | `float32`, `boolean`, `string` |
| **Baseline Risk Engine** | 9 | All component scores | `float32` [0-100], `string` tier |
| **Risk Explanations** | 3 | High-scoring driver tags | `string` (`risk_reason_1/2/3`) |

---

### 12. Mathematical Formulations

#### A. Thermal Intensity & Variability
$$\text{thermal\_intensity} = \frac{\text{sum\_frp\_mw}}{\text{spatial\_extent\_km} + 0.1}$$
$$\text{thermal\_frp\_variability} = \min\left(100.0, \frac{\text{max\_frp\_mw} - \text{mean\_frp\_mw}}{\text{mean\_frp\_mw} + 0.001}\right)$$

#### B. Sinusoidal Cyclical Temporal Encodings
$$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$
$$\text{month\_sin} = \sin\left(\frac{2\pi \cdot (\text{month} - 1)}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot (\text{month} - 1)}{12}\right)$$

#### C. Exponential Proximity Decay Scores (0 – 100)
For any physical distance $d$ in kilometers with characteristic decay distance $\lambda$:
$$S(d) = 100 \cdot \exp\left(-\frac{d}{\lambda}\right)$$
* Protected Areas: $\lambda = 3.0\text{ km}$ ($S = 100$ if inside)
* Industrial Facilities: $\lambda = 3.0\text{ km}$
* Roads, Railways, Power Lines: $\lambda = 2.0\text{ km}$
* Pipelines: $\lambda = 5.0\text{ km}$

#### D. Environmental Flammability Index (0 – 100)
$$S_{env} = \min\left(100.0, 70 \cdot f_{forest} + 20 \cdot f_{grass} + 10 \cdot f_{crop}\right)$$

#### E. Unified Explainable Baseline Risk Score
$$S_{risk} = 0.25 S_{thermal} + 0.20 S_{exposure} + 0.15 S_{env} + 0.15 S_{conservation} + 0.10 S_{industrial} + 0.05 S_{infra} + 0.10 S_{recurrence}$$
* Severity thresholds: `LOW` ($<30$), `MODERATE` ($30–60$), `HIGH` ($60–80$), `CRITICAL` ($\ge 80$).

---

### 13. Data Lineage & Traceability Graph
```
[Raw VIIRS/MODIS] ────► [firms_canonical] ────► [events_v0_1]
                                                    │
[Raw WorldPop 100m] ──► [population_100m.tif] ──────┤
                                                    │
[Raw OSM PBF] ────────► [osm_india.gpkg] ───────────┼──► [event_features_v1]
                                                    │           │
[Raw WDPA Archives] ──► [protected_areas.gpkg] ─────┤           │
                                                    │           ▼
[Raw WorldCover 10m] ─► [91 Tiles / Mosaic] ────────┘    [event_features_v2]
                                                                │
                                                         ┌──────┴──────┐
                                                         ▼             ▼
                                                    [ML Engine]   [Dashboard]
```

---

### 14. Null Value Semantics & Boundary Handling
* **Mandatory Non-Nullable Columns:** All thermal, temporal, population, conservation, landcover, industrial, infrastructure, recurrence, quality, and risk score columns have **0 nulls** across all 996,891 rows.
* **Documented Nullable Columns:**
  * `nearest_facility_name`: Null when OpenStreetMap object lacks an explicit `name` tag.
  * `state`, `state_code`, `district`, `district_code`: Explicitly `<NA>` pending authoritative administrative boundary dataset ingestion from Survey of India.

---

### 15. Explainable Baseline Risk Methodology
The baseline risk engine evaluates multi-criteria danger without relying on black-box heuristics:
1. **Thermal Intensity (25%):** How energetic and persistent is the thermal signature?
2. **Human Exposure (20%):** Are humans inhabiting the immediate 1km or 5km perimeter?
3. **Environmental Fuel Load (15%):** Is dense flammable forest or grassland dominant?
4. **Conservation Proximity (15%):** Does the thermal event threaten a national park or wildlife sanctuary?
5. **Industrial Facilities (10%):** Is it near high-hazard structures (refineries, power plants, chemical storage)?
6. **Infrastructure Corridors (5%):** Is it near transport arteries or transmission lines?
7. **Historical Recurrence (10%):** Has repeated thermal activity occurred in this cell in the previous 30 days?

---

### 16. Risk Score Limitations & Disclaimers
> [!WARNING]
> The `baseline_risk_score` is an **engineering baseline for operational ranking and prototype prioritization**. It is **NOT** a scientifically validated physical probability of wildfire ignition or spread. It serves to stratify anomalies before machine learning training.

---

### 17. How Recurrence Is Calculated
1. Each event is assigned to a discrete spatial cell ($0.05^\circ \times 0.05^\circ \approx 5.5\text{km} \times 5.5\text{km}$).
2. Events are sorted chronologically by UTC timestamp.
3. For each event in cell $C$ at timestamp $T$, a vectorized binary search (`searchsorted`) queries events in the interval $[T - \Delta t, T)$.
4. Cumulative sums compute historical FRP, active calendar days, and time since previous detection in $O(\log K)$ time.

---

### 18. How Spatial Density Is Calculated
Spatial clustering is evaluated across three concentric fixed-grid resolutions:
* **Local 1km:** $0.01^\circ \times 0.01^\circ$ (~1.1 km) cell frequency.
* **Local 5km:** $0.05^\circ \times 0.05^\circ$ (~5.5 km) cell frequency.
* **Local 10km:** $0.10^\circ \times 0.10^\circ$ (~11.0 km) cell frequency.
* Densities are normalized per square kilometer ($N / \pi R^2$).

---

### 19. Zero Temporal Leakage Guarantee
* In `v2/recurrence_features.py`, the search window is strictly $[T - \Delta t, T)$.
* The current event $T$ and any future events $t > T$ are mathematically excluded from prior count and sum accumulators.
* Verified by automated test `test_14_recurrence_never_uses_future_events` in `tests/test_event_features_v2.py`.

---

### 20. How to Add a New Feature
1. Create or open the relevant module in `data_pipeline/features/v2/` (e.g. `v2/thermal_features.py`).
2. Implement your vectorized NumPy/Pandas function taking `df: pd.DataFrame` and returning a DataFrame with new columns.
3. Add the feature calculation call to `run_v2_pipeline` in `v2/build_v2_features.py`.
4. Add the column metadata, formula, and description to `V2_DESCRIPTIONS` in `build_v2_features.py`.
5. Add unit test assertions in `tests/test_event_features_v2.py`.
6. Run `pytest tests/test_event_features_v2.py -v`.

---

### 21. How to Add a New Data Source
1. Store immutable raw files under `data/raw/<new_source>/`.
2. Implement a Layer-1 canonical consolidation script in `data_pipeline/<new_source>/` saving to `data/processed/<new_source>/<new_source>_india.gpkg` (or `.tif` / `.parquet`).
3. Create spatial indexing (`cKDTree` or `STRtree`) for rapid coordinate lookups.
4. Integrate the enrichment step into `data_pipeline/features/` without violating the 1-row-per-event rule.
5. Update `tests/` to verify source immutability and valid column derivation.

---

### 22. Immutable Datasets (NEVER Modify)
The following datasets are **read-only source assets**:
* `data/raw/*` (Raw PBF, WorldPop GeoTIFF, WorldCover tiles, WDPA archives)
* `data/processed/firms/firms_india_canonical.parquet`
* `data/processed/events/events_v0_1.parquet`
* `data/processed/osm/osm_india.gpkg`
* `data/processed/population/population_india_100m.tif`
* `data/processed/protected_areas/protected_areas_india.gpkg`
* `data/processed/features/event_features_v1.parquet`

---

### 23. Canonical vs Derived Datasets
* **Canonical Datasets:** Authoritative source-specific representations of real-world inputs (e.g. `osm_india.gpkg`, `events_v0_1.parquet`).
* **Derived Datasets:** Downstream consolidated analytical tables (`event_features_v1.parquet`, `event_features_v2.parquet`) generated deterministically from canonical datasets.

---

### 24. Connection to Future ML / Modeling Layer
* `event_features_v2.parquet` provides clean, leak-free, scaled, and cyclically encoded features directly ingestible by:
  * **Gradient Boosted Trees (LightGBM, XGBoost, CatBoost):** using `log_max_frp`, `population_density_1km`, `events_previous_30d`, `forest_fraction_1km`, `distance_to_major_road_km`.
  * **Unsupervised Anomaly Detectors (Isolation Forest, One-Class SVM):** identifying rare extreme industrial or ecological thermal excursions.
  * **Deep Neural Networks (MLP / Autoencoders):** using normalized continuous features and cyclical sine/cosine coordinates.

---

### 25. Connection to Future ThermoTrace UI
* The UI can display individual event cards showing:
  * `baseline_risk_score` and `baseline_risk_level` (colored badges: Green/Yellow/Orange/Red).
  * `risk_reason_1`, `risk_reason_2`, `risk_reason_3` (human-readable tags e.g. "HIGH THERMAL INTENSITY", "NEAR PROTECTED AREA").
  * Context popups showing nearest facility, protected area, and population within 1km.

---

### 26. Known Limitations
1. **Administrative Boundaries:** State and district fields remain nullable until official Survey of India boundary shapefiles are ingested.
2. **Weather / Wind:** Weather rasters (wind speed, direction, ambient temperature) are scheduled for Layer-2 data integration.
3. **WorldCover Mosaic Finalization:** 90/91 tiles verified; sampling works seamlessly across individual tiles.

---

### 27. Troubleshooting Guide
* **`ModuleNotFoundError: No module named 'data_pipeline'`:**  
  Always execute Python with the `-m` switch from the workspace root:  
  `python -m data_pipeline.features.v2.build_v2_features`
* **`FileNotFoundError: event_features_v1.parquet not found`:**  
  Run `python -m data_pipeline.features.build_event_features --v1` to rebuild V1.
* **Pytest import issues:**  
  `tests/` automatically inserts `PROJECT_ROOT` into `sys.path`. Run `pytest tests/test_event_features_v2.py -v`.

---

### 28. Git, LFS & Storage Instructions
* Never commit `.parquet`, `.gpkg`, `.tif`, `.pbf`, or `.zip` files directly to standard Git commits.
* See [data/README.md](file:///d:/New%20folder%20(2)/data/README.md) for detailed storage rules.

---

### 29. Handoff Checklist
```
HANDOFF CHECKLIST
-----------------
[X] V1 verified and passing 20/20 regression tests
[X] V2 pipeline built, verified, and passing 22/22 tests
[X] event_features_v2.parquet generated (996,891 rows x 144 columns)
[X] Full data dictionary schema generated (event_features_v2_schema.json)
[X] QA quality report and markdown summary generated
[X] All raw and canonical source datasets verified 100% untouched
[X] Zero temporal data leakage verified
[X] Comprehensive README handoff guide completed
[X] data/README.md and .gitignore created
[X] Next-stage ML / model owner can reproduce V2 in <2 minutes
```
