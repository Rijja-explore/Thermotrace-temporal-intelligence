# ThermoTrace Downstream Team Data Requirements & Architecture Guide

**Handoff Document for Member-2, Member-3, and Member-4**  
*Author:* Member 1 (Data Engineering & Geospatial Pipeline Lead)  
*Status:* Complete & Verified  

---

## 1. Executive Summary

Member 1 has finalized the data engineering, multi-source ingestion, spatial indexing, canonicalization, M3 thermal eventization, and integrated feature engineering for the Indian subcontinent.

All datasets adhere strictly to the **One Row = Exactly One M3 Event** analytical grain rule.

```
RAW SOURCES (Immutable)
       │
       ▼
SOURCE CANONICAL DATASETS (Layer-1 GPKG / COG / Parquet)
       │
       ▼
FIRMS CANONICAL DETECTIONS (2,477,543 detection points)
       │
       ▼
M3 THERMAL EVENTS (996,891 clustered events)
       │
       ▼
INTEGRATED EVENT FEATURES V1 (65 features) / V2 (144 features)
       │
       ├───────────────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼
MEMBER 2 (ETL / Expansion)      MEMBER 3 (ML & Risk)            MEMBER 4 (UI / API)
```

---

## 2. Data Availability Matrix for Downstream Members

### A. Member 3: Spatio-Temporal Anomaly Detection & Machine Learning
Member 3 has access to the following ready-to-train datasets and features:

| Analytical Need | Available Dataset / Columns | Local Path | Git / Cloud |
|---|---|---|---|
| **Raw / Prior Detections** | 2,477,543 point detections (`acq_datetime`, `frp`, `confidence`, `scan`, `track`) | `data/processed/firms/firms_india_canonical.parquet` | Git (<70MB) |
| **Event Clusters** | 996,891 M3 events (`event_id`, `start_time`, `duration_hours`, `spatial_extent_km`, `max_frp_mw`) | `data/processed/events/events_v0_1.parquet` | Git (<50MB) |
| **Detection-to-Event Links**| Foreign key lookup linking every detection to its `event_id` | `data/processed/events/event_detection_links.parquet` | Git (<35MB) |
| **Base Event Features (V1)**| 65 canonical features including IMD seasons, 100m population, WDPA PAs, OSM infrastructure, ESA WorldCover | `data/processed/features/event_features_v1.parquet` | Git (<100MB) |
| **Advanced Features (V2)** | 144 features including **leak-free recurrence (7d/30d/90d)**, cyclical time (`hour_sin/cos`), and 1km/5km/10km spatial density | `data/processed/features/event_features_v2.parquet` | Cloud Google Drive (210MB) |
| **Baseline Risk Scoring** | Explainable Baseline Risk Score (0–100) and severity tiers (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) | Embedded in `event_features_v2.parquet` | Cloud Google Drive |
| **Demographic Exposure** | Continuous 100m population density at event, 1km, and 5km radii | `population_at_event`, `population_density_1km` | In Feature Tables |
| **Ecological Fuel Load** | ESA WorldCover 10m fractions (`forest_fraction_1km`, `cropland_fraction_1km`, etc.) | `forest_fraction_1km`, `natural_land_fraction` | In Feature Tables |
| **Industrial Proximity** | Distances and boolean proximity flags to 7 OSM industrial facility categories | `near_power_plant`, `near_factory`, `near_refinery` | In Feature Tables |
| **Transport Corridors** | Distances to roads, railways, transmission lines, and pipelines | `transport_corridor_flag`, `distance_to_major_road_km` | In Feature Tables |

> [!IMPORTANT]
> **Baseline Distinction for Member 3:**  
> The current baseline risk implementation is a **transparent, rule-based engineering baseline foundation**. It provides an operational benchmark and explainable scoring before model training. It is **NOT** a final machine learning classifier or scientifically calibrated physical fire propagation model. Building the predictive/anomaly machine learning models (e.g. LightGBM, XGBoost, Isolation Forest) remains the responsibility of Member 3.

---

### B. Member 4: Frontend UI, Dashboard & Visualization API
Member 4 can immediately consume event attributes and pre-calculated explainable risk indicators for dashboard visualization:

| UI Component | Recommended Data Source | Key Fields for Rendering |
|---|---|---|
| **Event Map View** | `events_v0_1.parquet` or `event_features_v1.parquet` | `centroid_lat`, `centroid_lon`, `max_frp_mw`, `duration_hours`, `detection_count` |
| **Risk Severity Badging** | `event_features_v2.parquet` | `baseline_risk_score` (0–100), `baseline_risk_level` (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) |
| **Explainability Tooltips** | `event_features_v2.parquet` | `risk_reason_1`, `risk_reason_2`, `risk_reason_3` (e.g., `HIGH_THERMAL_INTENSITY`, `REPEATED_ACTIVITY`, `NEAR_PROTECTED_AREA`) |
| **Facility Proximity Card** | `event_features_v1.parquet` | `nearest_facility_type`, `distance_to_facility_km`, `nearest_facility_name` |
| **Protected Area Alert** | `event_features_v1.parquet` | `inside_protected_area`, `protected_area_name`, `distance_to_protected_area_km` |
| **Demographic Impact** | `event_features_v1.parquet` | `population_density_1km`, `population_5km`, `high_population_exposure_flag` |
| **Temporal Filtering** | `event_features_v1.parquet` | `year`, `month`, `season` (`WINTER`, `PRE_MONSOON`, `MONSOON`, `POST_MONSOON`), `is_night` |

---

### C. Member 2: Data Pipeline Maintenance & Expansion
Member 2 is responsible for recurring ingestion runs and expanding source layers:
* Ingesting future FIRMS data using `data_pipeline/firms/canonical_etl.py`.
* Ingesting Survey of India official state/district administrative boundaries into `data/processed/boundaries/india_admin.gpkg`.
* Adding Layer-2 weather/wind data (ERA5/IMD) into `data/raw/weather/` and incorporating wind vector enrichment into the feature pipeline.

---

## 3. Data Integrity & Grain Guarantee

To prevent downstream model corruption or invalid aggregations:
1. **1 Row = 1 Event:** Under no circumstances should spatial joins multiply rows. The event table must always maintain 996,891 rows unless new events are ingested.
2. **Zero Temporal Leakage:** All recurrence and historical activity metrics use strictly prior observations ($t < T$).
3. **Traceability:** Any event row can be traced to its constituent detections via `event_detection_links.parquet` using `event_id`.
