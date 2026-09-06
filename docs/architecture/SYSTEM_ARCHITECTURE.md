# ThermoTrace System Architecture

## Overview

ThermoTrace is structured as a modular multi-service geospatial platform designed for high availability, offline robustness, and explainable decision-making.

```
+-----------------------------------------------------------------------------------+
|                                  REACT FRONTEND                                   |
|               (Dashboard, Investigation, Alerts, Facility, Evaluation)            |
+-----------------------------------------------------------------------------------+
                                         │ REST / JSON
                                         ▼
+-----------------------------------------------------------------------------------+
|                                 FASTAPI BACKEND                                   |
|       (Events Router, Facility Router, Alert Router, Incident Report Engine)      |
+-----------------------------------------------------------------------------------+
                   │                                         │
                   ▼                                         ▼
+------------------------------------+    +-----------------------------------------+
|   CLASSIFICATION SERVICE (M2 ML)   |    |  TEMPORAL INTELLIGENCE ENGINE (M3)      |
|  - M4-B HistGradientBoosting       |    |  - DBSCAN Event Clustering              |
|  - Rule-based Heuristic Fallback   |    |  - 7d/30d/90d Feature Extraction        |
|  - Approved Feature Vetting        |    |  - Facility Baseline & Z-Score Anomaly  |
|  - Class Probabilities & Evidence  |    |  - Industrial Likelihood & Risk Scoring |
+------------------------------------+    +-----------------------------------------+
                   │                                         │
                   +--------------------+--------------------+
                                        │
                                        ▼
+-----------------------------------------------------------------------------------+
|                                  DATA PERSISTENCE                                 |
|          - PostGIS Database (Events, Facilities, Audit Log)                       |
|          - Cached Offline Parquet & CSV Datasets (Offline Judge Demo Fallback)    |
+-----------------------------------------------------------------------------------+
```

## Core Service Layers

1. **Ingestion & Data Pipeline (`services/data_pipeline/`):**
   Normalizes raw NASA FIRMS satellite observations, validates coordinates/confidence, and executes DBSCAN spatial/temporal clustering.

2. **AI Classification Service (`services/classification/`):**
   Evaluates feature vectors against trained model checkpoints (`best_m4_class_balance_variant.joblib`) or transparent rule-based heuristics. Produces probability distributions across 6 canonical classes.

3. **Temporal Intelligence & Anomaly Engine (`services/temporal_intelligence/`):**
   Computes pre-period facility baselines, Z-scores, modified MAD robust anomalies, composite 6-component industrial likelihood, and 5-component operational risk scores.

4. **REST API & Report Generator (`apps/backend/` & `services/report_engine/`):**
   Serves REST endpoints for frontend mission control and dynamically compiles self-contained HTML/PDF incident reports.

5. **GIS Frontend UI (`apps/frontend/`):**
   React 19 single-page application powered by MapLibre GL JS / Leaflet vector maps, real-time risk heat badges, and analyst decision audit flow.
