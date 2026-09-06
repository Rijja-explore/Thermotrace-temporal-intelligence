# ThermoTrace Integration Audit & System Synthesis

**Project:** ThermoTrace — Explainable Geospatial Intelligence for Industrial Thermal Anomalies  
**Date:** September 6, 2026  
**Status:** Pre-Integration Assessment Complete  

---

## 1. Executive Summary & Audit Overview

ThermoTrace is designed to transition thermal anomaly monitoring from passive satellite observation (e.g. NASA FIRMS) to an operational geospatial intelligence workflow. The parent workspace contains contributions from five separate engineering workstreams (`member1` through `member5`). 

This audit evaluates each member's contributions, identifies duplicate implementations, resolves architectural conflicts, documents input/output schemas, and outlines the target unified architecture for the final demo-ready SIH 2026 prototype.

---

## 2. Comprehensive Member Workstream Analysis

### MEMBER 1: Data Pipeline & Remote Sensing GIS
* **Current Implementation:** Highly developed ETL pipeline for NASA FIRMS data ingestion, OSM industrial infrastructure extraction, WorldCover land-cover mosaic processing, and spatial event clustering engine (`build_events.py`).
* **Complete Features:**
  * FIRMS India canonical dataset processing (`firms_india_canonical.parquet` — 2,477,543 observations).
  * Spatial event clustering (`events_v0_1.parquet` — 996,891 events, `event_detection_links.parquet`).
  * Feature extraction engine generating 65 spatial/temporal/landcover features (`event_features_v1.parquet`).
  * Comprehensive test suite (74 unit/integration tests passing).
* **Partial Features:**
  * Large raster integration (WorldCover, WorldPop, OSM GeoPackage) depends on external Google Drive storage for full multi-GB files.
  * Feature extraction v2 schema (`event_features_v2.parquet` reference).
* **Missing Features:** Backend API, interactive web frontend, live API refresh server.
* **Broken Features / Issues:** `event_features_v2.parquet` in repo is an empty pointer file (~134 bytes).
* **Input/Output Schema:**
  * *Input:* Raw FIRMS CSVs (`latitude`, `longitude`, `frp`, `acq_date`, `acq_time`, `confidence`, `bright_ti4`, `bright_ti5`, `satellite`).
  * *Output:* Event-level parquets with clustered geometry, centroid, detection counts, FRP statistics, OSM distances (`dist_to_industrial`, `dist_to_power`), and landcover fractions (`lc_urban_100m`, `lc_forest_100m`).

---

### MEMBER 2: AI Classification & Machine Learning Engine
* **Current Implementation:** Rigorous 7-model ML benchmarking system evaluating traditional baseline, rule-based, decision tree, gradient boosted, neural, and hybrid models.
* **Complete Features:**
  * Taxonomy of 6 canonical target classes:
    1. `persistent_industrial_source`
    2. `industrial_fire_or_abnormal_event`
    3. `wildfire_or_forest_fire`
    4. `agricultural_burning`
    5. `mining_or_other_industrial_activity`
    6. `unknown_requires_verification`
  * Trained joblib/pt models for M1 through M7 saved in `member2/ml/models/benchmark/`.
  * Winner model: **M4-B (HistGradientBoosting with Class Balance Variant)** achieving 70.0% accuracy on N=30 human verified ground truth dataset, Macro F1 = 0.5879.
  * Leakage prevention framework with 47 explicitly approved features and strict exclusion lists (`features.py`).
  * Ground truth dataset with human verified annotations (`candidate_pool_v1.json`, `mock_remote_sensing_ground_truth.json`).
  * Comprehensive ML test suite (127 passing unit tests).
* **Partial Features:**
  * `inference.py` runtime loader currently returns `fail_prediction` state because model loading lifecycle was not wired to local `.joblib` files.
* **Missing Features:** Real-time API integration with backend services.
* **Broken Features / Issues:** Missing live API endpoint glue.
* **Input/Output Schema:**
  * *Input:* 47 spatial/temporal/landcover feature dict matching `PredictionContract`.
  * *Output:* `PredictionContract` containing `predicted_label`, `confidence`, `probabilities` dictionary, `top_evidence`, `evidence_against`, and `model_version`.

---

### MEMBER 3: Temporal Intelligence, Anomaly Detection & Risk Engine
* **Current Implementation:** Production-grade modular Python package (`thermotrace_temporal`) implementing full 12-step decision & scoring pipeline.
* **Complete Features:**
  * Pydantic schemas for observations, events, temporal features, baselines, deviation, anomaly, industrial likelihood, operational risk, evidence bundles, and alerts.
  * Temporal feature extraction (7-day, 30-day, 90-day activity windows).
  * Facility thermal fingerprinting and baseline calculation with pre-period filtering to eliminate leakage.
  * Multi-signal anomaly detection (Z-score, MAD, FRP jump, spatial shift, frequency jump).
  * Industrial Likelihood scoring (weighted 6-component model).
  * Operational Risk scoring (5-component model with graceful degradation).
  * Rule-based Alert generation engine.
  * Evidence generator creating structured `evidence_for`, `evidence_against`, and `missing_evidence`.
  * Configurable parameters via `config/thresholds.yaml` and `config/weights.yaml`.
  * 9 unit test modules + 4 end-to-end JSON scenario files.
* **Partial Features:** Isolated CLI/library implementation without REST wrapper.
* **Missing Features:** Web frontend, database persistence layer connection.
* **Broken Features / Issues:** None (Code is exceptionally well-structured and functional).
* **Input/Output Schema:**
  * *Input:* Event observation sequence + facility spatial lookup + config dict.
  * *Output:* `PipelineOutput` schema containing structured baseline, anomaly Z-scores, industrial likelihood, operational risk, evidence bundle, and generated alerts.

---

### MEMBER 4: GIS / Backend / Frontend & DB Architecture
* **Current Implementation:** Full-stack prototype with FastAPI backend, PostGIS spatial database schema, and React 19 / TypeScript / Vite frontend UI.
* **Complete Features:**
  * FastAPI server (`apps/backend`) with endpoints for `/api/events`, `/api/events/{id}`, `/api/facilities`, `/api/alerts`, and `/api/reports/{id}`.
  * HTML Incident Report generator with dark-themed styling.
  * PostGIS schema definition (`database/schema.sql`) with spatial indices and sample seed data.
  * React frontend UI (`Dashboard.tsx`, `EventInvestigation.tsx`, `Alerts.tsx`) with dark design system (19 KB `index.css`).
* **Partial Features:**
  * Frontend Map component (`MapView.tsx`) uses 3D CesiumJS/Resium requiring a paid Google Photorealistic Tiles / Cesium Ion token (`VITE_CESIUM_ION_TOKEN`), which blocks local deployment without paid keys.
  * Event schemas in frontend API client use simplified fields inconsistent with Member 3's Pydantic schemas.
* **Missing Features:** Dedicated Facility Profile page, Report Preview page, Model Evaluation page, Unknown state UI controls, Reclassify modal.
* **Broken Features / Issues:**
  * Map rendering fails without paid Cesium Ion token.
  * Backend returns mock event structures that lack Member 2 ML predictions and Member 3 temporal/anomaly fields.
  * `README.md` contains unmerged git conflict markers.
* **Input/Output Schema:**
  * *Input:* Simplified JSON REST payloads.
  * *Output:* Basic REST endpoints returning un-enriched thermal event objects.

---

### MEMBER 5: Historical Intelligence & Facility Baselines (Duplicate of Member 3 + Data Extractor)
* **Current Implementation:** Dual code base containing an identical copy of Member 3's `thermotrace_temporal` package alongside unique historical data processing scripts (`historical_intelligence/`).
* **Complete Features:**
  * Pre-computed facility baseline CSVs (`facility_baselines.csv` — 6 MB, `facility_profiles.csv` — 5.6 MB, `industrial_facilities.csv` — 33 MB).
  * Analysis notebooks (`baseline_analysis.ipynb`, `facility_analysis.ipynb`, `historical_exploration.ipynb`).
* **Partial Features:** Duplicate copy of `thermotrace_temporal` source code.
* **Missing Features:** Unique backend or API integration.
* **Broken Features / Issues:** Complete duplicate of Member 3's core package.
* **Input/Output Schema:** CSV processing inputs/outputs for historical facility baselines.

---

## 3. Cross-Member Inventory & Duplication Matrix

| Component | Member 1 | Member 2 | Member 3 | Member 4 | Member 5 | Selected Best Implementation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Cleaning & Ingestion** | ✅ (Parquet/ETL) | ❌ | ❌ | ❌ | ❌ | **Member 1** (`canonical_etl.py`) |
| **Event Clustering** | ✅ (DBSCAN/Parquet) | ❌ | ✅ (Pydantic/In-Memory) | ❌ | ❌ | **Member 1** (Offline) + **Member 3** (Runtime) |
| **AI Classification ML** | ❌ | ✅ (M4-B Benchmark) | ❌ | ❌ | ❌ | **Member 2** (`best_m4_class_balance_variant.joblib`) |
| **Temporal / Anomaly / Risk**| ❌ | ❌ | ✅ (Full Engine) | ❌ | ✅ (Duplicate) | **Member 3** (`thermotrace_temporal`) |
| **Historical Facility Data** | ❌ | ❌ | ❌ | ❌ | ✅ (CSV Datasets) | **Member 5** (`facility_baselines.csv`) |
| **Backend REST API** | ❌ | ❌ | ❌ | ✅ (FastAPI) | ❌ | **Member 4** (`apps/backend`) |
| **PostGIS Database** | ❌ | ❌ | ❌ | ✅ (`schema.sql`)| **Member 4** (`database/schema.sql`) extended |
| **Frontend UI** | ❌ | ❌ | ❌ | ✅ (React/TS/Vite) | ❌ | **Member 4** (Migrated to MapLibre GL JS) |

---

## 4. Integration Conflicts & Technical Risks

1. **Map Technology Blocker (Cesium Ion Token):**  
   Member 4's map relies on `resium` / `cesium` with `VITE_CESIUM_ION_TOKEN`. This fails or displays watermark/errors when no paid token is provided.  
   *Resolution:* Migrate frontend map component to **MapLibre GL JS**, using standard open-source vector/raster basemaps.

2. **Schema Incompatibility:**  
   Member 4's backend returned flat event objects (`lat`, `lon`, simple `evidence: string[]`). Member 3 defines structured Pydantic models (`location.latitude`, `evidence.evidence_for`, `evidence.evidence_against`). Member 2 returns `PredictionContract`.  
   *Resolution:* Establish **One Canonical Data Contract** (`schemas/Event.schema.json`) and adapt FastAPI endpoints to serialize Member 3/Member 2 outputs directly.

3. **Inference Engine Disconnect:**  
   Member 2's `inference.py` was hardcoded to return `fail_prediction` in uninitialized environments.  
   *Resolution:* Build a dedicated model loader in backend startup that loads `m4_class_balance/best_m4_class_balance_variant.joblib` and evaluates feature vectors dynamically.

4. **Offline Demo Fallback:**  
   Live FIRMS or OSM API calls might fail during live judging or offline evaluation.  
   *Resolution:* Embed Member 5 CSVs and Member 1 Parquet extracts into `data/demo/` and `backend/firms_data.json` as a fail-safe offline dataset.

---

## 5. Recommended Final Architecture

The five member workspaces will be unified into ONE single multi-service repository with clear separation of concerns:

```
ThermoTrace/
├── apps/
│   ├── frontend/             # React 19 + TypeScript + MapLibre GL JS + Tailwind CSS
│   └── backend/              # FastAPI REST API + PostGIS integration
├── services/
│   ├── data_pipeline/        # Ingestion, cleaning & spatial enrichment (from M1)
│   ├── classification/       # Model inference engine & ML evaluation (from M2)
│   ├── temporal_intelligence/# Temporal features, baseline & risk engine (from M3)
│   ├── report_engine/        # HTML/PDF incident report generator (from M4)
│   └── historical_intel/     # Historical baseline CSV processor (from M5)
├── database/
│   ├── schema.sql            # PostGIS tables (events, facilities, predictions, audit_log)
│   └── seed/                 # Seed data generators
├── data/
│   ├── raw/                  # FIRMS, OSM, landcover inputs
│   ├── processed/            # Parquets, baselines, facility datasets
│   └── demo/                 # Cached offline demonstration cases
├── models/
│   ├── trained/              # Saved .joblib model weights (M4-B)
│   └── schemas/              # Pydantic & JSON validation schemas
├── config/
│   ├── thresholds.yaml       # Anomaly & spatial thresholds
│   └── weights.yaml          # Risk & industrial likelihood scoring weights
├── docs/                     # Comprehensive architecture & methodology docs
├── scripts/                  # Task runners, setup, seed, evaluate & test scripts
└── tests/                    # Unit, integration, API, frontend & E2E tests
```

---

## 6. Action Plan & Phased Execution Roadmap

1. **Phase 4:** Define Canonical `Event.schema.json` and Pydantic DTOs.
2. **Phase 5-8:** Reorganize directory tree into `apps/`, `services/`, `data/`, `models/`, and `config/`. Wire ML Model M4-B into classification engine.
3. **Phase 9-10:** Extend PostGIS schema and update FastAPI endpoints to serve complete canonical event models with baseline, anomaly, and risk details.
4. **Phase 11-12:** Refactor React frontend: replace Cesium with MapLibre GL JS, implement missing pages (Facility Profile, Report Preview, Analytics), add Unknown state UI, and implement analyst action feedback flow.
5. **Phase 13-15:** Build three cached demo cases (Persistent Industrial, Agriculture/Wildfire, Ambiguous/Unknown), implement analyst audit persistence, and complete HTML report export.
6. **Phase 16-24:** Run full test suite, verify Docker orchestration, perform UI polish, and publish final documentation.
