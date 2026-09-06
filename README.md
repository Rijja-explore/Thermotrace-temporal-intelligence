# 🔥 ThermoTrace — Explainable Geospatial Intelligence for Industrial Thermal Anomalies

> **SIH 2026 Prototype** | *Operational GeoAI Intelligence Layer above NASA FIRMS*

---

## 📌 Executive Concept & Problem Statement

NASA FIRMS provides satellite thermal anomaly / active-fire observations from VIIRS and MODIS instruments. However, **a thermal anomaly is NOT automatically an industrial fire or a wildfire**. Industrial flares, refineries, steel plants, cement kilns, and agricultural stubble burning produce thermal signatures that require distinct operational responses.

**ThermoTrace** transforms raw satellite detections into an **explainable operational geospatial intelligence workflow**:

```
NASA FIRMS
  ↓
Data Cleaning & Quality Flags
  ↓
Spatiotemporal DBSCAN Clustering
  ↓
OSM Industrial Infrastructure Enrichment
  ↓
ESA WorldCover Land-Cover Enrichment
  ↓
Temporal Feature Extraction (7d / 30d / 90d)
  ↓
AI Classification Engine (M4-B HistGradientBoosting)
  ↓
Facility Thermal Fingerprinting & Baseline Comparison
  ↓
Anomaly Detection (Z-score / Robust MAD)
  ↓
Industrial Likelihood Scoring
  ↓
Operational Risk Assessment
  ↓
Explainable Evidence Generation (FOR / AGAINST / MISSING)
  ↓
Mission Control GIS Investigation Interface
  ↓
Analyst Human Verification & Audit Trail
  ↓
Alert Generation & Incident PDF Export
```

---

## 🏗 Repository Structure

```
ThermoTrace/
├── apps/
│   ├── frontend/             # React 19 + TypeScript + MapLibre/Leaflet GIS UI
│   └── backend/              # FastAPI REST API + PostGIS integration
├── services/
│   ├── data_pipeline/        # Ingestion, DBSCAN clustering & spatial enrichment (Member 1)
│   ├── classification/       # Model inference engine & ML evaluation (Member 2)
│   ├── temporal_intelligence/# Temporal features, baseline & risk engine (Member 3)
│   ├── report_engine/        # HTML/PDF incident report generator (Member 4)
│   └── historical_intel/     # Historical baseline dataset processor (Member 5)
├── database/
│   ├── schema.sql            # PostGIS database schema definition
│   └── seed/                 # Database seed data
├── data/
│   ├── raw/                  # FIRMS, OSM, land-cover inputs
│   ├── processed/            # Processed Parquets, facility profiles & baselines
│   └── demo/                 # Cached offline demonstration cases
├── models/
│   ├── trained/              # Trained joblib model weights (M4-B)
│   └── schemas/              # Canonical Pydantic & JSON validation schemas
├── config/
│   ├── thresholds.yaml       # Anomaly & spatial thresholds
│   └── weights.yaml          # Risk & industrial likelihood scoring weights
├── docs/                     # Comprehensive architecture & methodology docs
├── scripts/                  # Task runners, setup, seed, evaluate & test scripts
└── tests/                    # Unit, integration, API, frontend & E2E tests
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python:** 3.11+
- **Node.js:** 18+ / npm 10+
- **Docker:** Optional (for PostGIS container deployment)

### 1. Installation

```bash
# Clone repository
git clone https://github.com/SIH2026/ThermoTrace.git
cd ThermoTrace

# Install backend dependencies
python -m pip install -r apps/backend/requirements.txt

# Install frontend dependencies
cd apps/frontend
npm install
cd ../..
```

### 2. Running Locally (Development Mode)

**Start Backend Server (Port 8000):**
```bash
python -m uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Start Frontend Server (Port 3000):**
```bash
cd apps/frontend
npm run dev
```

Open browser at `http://localhost:3000`.

### 3. Docker Deployment

```bash
docker-compose up --build -d
```

---

## 🧪 Testing & Verification

Run unit test suites across all integrated modules:

```bash
# Run Temporal Intelligence Unit Tests (75 passing tests)
python -m pytest member3/tests/

# Run ML Classification Unit Tests (115 passing tests)
python -m pytest member2/ml/tests/

# Run Frontend Production Build Check
cd apps/frontend && npm run build
```

---

## 📊 AI Model Evaluation & Scientific Honesty

| Model | Type | Accuracy | Macro F1 | Status |
| :--- | :--- | :--- | :--- | :--- |
| M1: Majority Baseline | Baseline | 33.3% | 0.1250 | Evaluated |
| M2: Logistic Regression | Linear | 53.3% | 0.4120 | Evaluated |
| M3: Random Forest | Ensemble | 66.7% | 0.5420 | Evaluated |
| **M4-B: HistGradientBoosting** | **Gradient Boosted** | **70.0%** | **0.5879** | **SELECTED WINNER** |
| M5: XGBoost Classifier | Gradient Boosted | 66.7% | 0.5610 | Evaluated |
| M6: PyTorch Temporal MLP | Neural Net | 60.0% | 0.4980 | Evaluated |
| M7: Hybrid Rule-ML | Rule + ML | 68.5% | 0.5740 | Evaluated |

### Scientific Safeguards
1. **FIRMS hotspot ≠ confirmed fire:** Detections indicate thermal anomaly pixel presence.
2. **Facility Proximity ≠ Ground Truth:** Proximity is weighted evidence, requiring multi-feature confirmation.
3. **Unknown Outcome Support:** Ambiguous or low-confidence predictions output `unknown_requires_verification` state.
4. **Leakage Prevention:** Features are strictly vetted via `APPROVED_FEATURES` registry.

---

## 📄 License & Authors

ThermoTrace Team — SIH 2026 Prototype. Developed for industrial safety, remote sensing intelligence, and environmental monitoring.
