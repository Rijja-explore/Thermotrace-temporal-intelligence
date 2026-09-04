# ThermoTrace: Temporal & Spatial Thermal Anomaly Analytics

**Subcontinent Scale (India): Multi-Modal Geospatial Engineering & Machine Learning Intelligence**  
*Repository:* [ThermoTrace Temporal Intelligence](https://github.com/Rijja-explore/Thermotrace-temporal-intelligence)  
*Branch:* `member2-ai-ml`  
*Lead Authors:* Member 1 (Geospatial Data Engineering) & Member 2 (Machine Learning & Classifier System Lead)  
*Status:* Data Pipeline Complete (Layer 0-3 Verified) & ML Subsystem Verified (7-Model Benchmark, M4-B Class-Balance Selection, Independent Human Reliability Infrastructure, Empirical Human GT Benchmark — 100% Passing, 127 Unit Tests)

---

## 1. System Architecture Overview

ThermoTrace ingests, canonicalizes, clusters, enriches, and classifies satellite thermal observations and high-resolution geospatial contextual layers across continental India ($65^\circ\text{E} - 100^\circ\text{E}, 5^\circ\text{N} - 38^\circ\text{N}$).

```
RAW DATA (Immutable Source Layer)
├── FIRMS VIIRS/MODIS CSVs (148 files, 2.47M detections)
├── OpenStreetMap India PBF (1.63 GB, 169k facilities, 1.1M infra)
├── WorldPop 2025 100m GeoTIFF (742 MB population raster)
├── UNEP-WCMC WDPA Protected Areas (3 ZIPs)
└── ESA WorldCover 10m Tiles (91 GeoTIFFs, 6.4 GB land cover mosaic)
                           │
                           ▼
CANONICAL DATASETS & CLUSTERING ENGINE (Layer 0 & Layer 1)
├── data/processed/firms/firms_india_canonical.parquet (2.47M points)
├── data/processed/events/events_v0_1.parquet (996,891 clustered events)
└── data/processed/events/event_detection_links.parquet (2.47M relational links)
                           │
                           ▼
EVENT-LEVEL FEATURE ENGINE (Layer 2 & Layer 3)
└── data/processed/features/event_features_v2.parquet (144 features + Baseline Risk)
                           │
                           ▼
MACHINE LEARNING CLASSIFICATION SUBSYSTEM (Member 2 - ml/)
├── 7-Model Training & Evaluation Benchmark (M1..M7)
├── M4 Class-Balance Experiment Suite (Selected Winner: M4-B Sample Weighting)
├── Feature & Error Diagnostics Suite (N=280 Validation Set)
├── Independent Human Reliability Infrastructure (Double-Blind N=30, κ = 1.0000)
└── Empirical Human Ground-Truth Benchmark (human_ground_truth_30.json, Acc = 70.00%)
```

---

## 2. Core Datasets & Feature Foundations

The project strictly separates raw detections, spatio-temporal clusters, feature matrices, and target labels into distinct layers:

```
FIRMS DETECTION POINT (2,477,543 rows)
       │
       ▼ [Spatiotemporal Union-Find: <1km radius, <6h temporal window]
M3 THERMAL EVENT CLUSTER (996,891 rows)
       │
       ▼ [Geospatial Enrichment: Population, Land Cover, Infrastructure, Recurrence]
EVENT FEATURE MATRIX (996,891 rows, 47 Approved ML Features)
       │
       ▼ [Chronological 80/20 Split: Cutoff 2026-04-07T20:42:00]
ML TRAINING CANDIDATES (N=1,120 Train / N=280 Validation)
```

1. **FIRMS Canonical Detections**: `data/processed/firms/firms_india_canonical.parquet` (2,477,543 points)
2. **M3 Thermal Events**: `data/processed/events/events_v0_1.parquet` (996,891 clustered events)
3. **Event Detection Links**: `data/processed/events/event_detection_links.parquet` (2,477,543 relational links)
4. **Event Features V2**: `data/processed/features/event_features_v2.parquet` (996,891 rows, 144 columns)

---

## 3. Machine Learning Subsystem Highlights (`ml/`)

Detailed documentation for the ML subsystem is available in [`ml/README.md`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/README.md).

### 1. Canonical Event Taxonomy
All thermal events are categorized into six mutually exclusive classes:
- `agricultural_burning`
- `industrial_fire_or_abnormal_event`
- `mining_or_other_industrial_activity`
- `persistent_industrial_source`
- `unknown_requires_verification`
- `wildfire_or_forest_fire`

### 2. Selected Development Model (**`M4-B`**)
- **Architecture**: `HistGradientBoostingClassifier` trained with inverse class sample weights (`compute_sample_weight('balanced', y_train)`).
- **Selection Rationale**: Retains all $N=1,120$ original training records without discarding data, achieving top weak-label validation performance (Active-Class Macro F1 = `1.0000`, 6-Class Macro F1 = `0.8333`, Balanced Accuracy = `1.0000`).
- **Checkpoint**: [`ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib)

### 3. Empirical Human Ground-Truth Benchmark Results
Evaluated M4-B against canonical empirical human ground truth (`human_ground_truth_30.json`, $N=30$, derived from 100% dual-human agreement, Cohen's $\kappa = 1.0000$):
- **Accuracy**: **`70.00%`** ($21 / 30$ correct)
- **Balanced Accuracy**: **`0.6333`**
- **6-Class Macro F1**: **`0.5879`**
- **Error Concentration**: $77.8\%$ of errors ($7 / 9$) are `persistent_industrial_source` events misclassified as `mining_or_other_industrial_activity`.

### 4. Evaluation Regimes Separation
- **Weak-Label Validation ($N=280$)**: Active Macro F1 = `1.0000`, 6-Class Macro F1 = `0.8333`.
- **Simulated Pilot V2 ($N=100$)**: Macro F1 = `0.5877` (**SIMULATED / NOT EMPIRICAL HUMAN EVIDENCE**).
- **Empirical Human Ground Truth ($N=30$)**: Accuracy = **`70.00%`**, Macro F1 = **`0.5879`** (**PRIMARY EMPIRICAL HUMAN BENCHMARK**).

---

## 4. Repository Directory Structure

```
.
├── data/                           # Data storage & layer documentation
├── data_pipeline/                  # FIRMS, M3 events, OSM, WorldPop, WDPA, WorldCover ETLs
├── ml/                             # Machine Learning subsystem (Member 2)
│   ├── configs/                    # Model hyperparameter configs
│   ├── data/                       # Weak labels & double-blind human reliability packets
│   ├── models/                     # Model joblib checkpoints (M4-A..M4-F, best_m4_class_balance_variant.joblib)
│   ├── reports/                    # Benchmark reports, diagnostics, & human reliability analysis
│   ├── src/                        # Inference adapters, features, explainability, models, splits
│   ├── tools/                      # Benchmark, class-balance, validation, & adjudication CLI tools
│   └── tests/                      # 127 automated unit, integration, and integrity tests
├── reports/                        # Handoff, feature, & QA reports
└── tests/                          # Automated data pipeline tests (74 tests)
```

---

## 5. Quickstart & Verification Guide

### 1. Run Complete ML & Pipeline Test Suite (127 Passing Tests)
```bash
$env:PYTHONPATH="ml"
python -m pytest ml/tests -q
```

### 2. Verify Frozen Reliability Packet Blinding & SHA-256 Checksums
```bash
python ml/tools/validate_human_reliability_annotations.py
```

### 3. Re-run Empirical Human Reliability Analysis & M4-B Benchmark
```bash
python ml/evaluation/reliability_analysis.py
python ml/tools/evaluate_m4_on_human_ground_truth.py
```

### 4. Re-run Model Benchmark & Class-Balance Experiment Suite
```bash
python ml/tools/run_model_benchmark.py
python ml/tools/run_m4_class_balance_suite.py
python ml/tools/run_m4_diagnostics.py
```

---

## 6. Handoff Notes & Next Actions

- **Machine Learning (Member 2):** Human reliability protocol, adjudication tooling, and M4-B empirical evaluation complete. Model calibration and human ground-truth expansion are ready for post-pilot training.
- **Frontend UI & Dashboards (Member 4):** Prediction schema (`PredictionStatus`, `VerificationState`, `ExplanationType`) and inference adapters in `ml/src/classification/inference.py` are ready for API integration.
