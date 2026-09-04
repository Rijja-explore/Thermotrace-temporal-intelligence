# ThermoTrace ML Subsystem: Supervised Classification & Temporal Intelligence

**Repository:** [ThermoTrace Temporal Intelligence](https://github.com/Rijja-explore/Thermotrace-temporal-intelligence)  
**Branch:** `member2-ai-ml`  
**Lead Author:** Member 2 (Machine Learning & Classifier System Lead)  
**Status:** Multi-Model Benchmark, Class-Balance Suite, Feature Diagnostics, Independent Human Reliability Protocol, and Empirical Human Ground-Truth Evaluation Complete (100% Verified, 127 Passing Unit Tests)

---

## 1. System Overview & Architecture

The ThermoTrace Machine Learning subsystem classifies spatio-temporally clustered satellite thermal events (`event_id`) into a canonical six-class domain taxonomy. It processes 47 approved, leak-free geospatial and temporal features extracted from satellite radiometers (VIIRS/MODIS), high-resolution land cover (ESA WorldCover 10m), infrastructure vectors (OpenStreetMap India), population rasters (WorldPop 100m), and protected area boundaries (UNEP-WCMC WDPA).

```
LAYER-2 FEATURE MATRIX (event_features_v2.parquet, 47 Approved Features)
                                   │
                                   ▼
CHRONOLOGICAL SPLIT ENGINE (80% Train N=1,120 / 20% Val N=280)
                                   │
                                   ▼
MULTI-MODEL TRAINING SUITE (7 Model Families Trained & Evaluated)
 ├── M1: DummyClassifier (Stratified Baseline)
 ├── M2: LogisticRegression (L2 Penalized)
 ├── M3: RandomForestClassifier (100 Trees)
 ├── M4: HistGradientBoostingClassifier (Top Weak-Label Performer)
 ├── M5: MLPClassifier (2-Layer Neural Network)
 ├── M6: XGBoost (XGBClassifier)
 └── M7: LightGBM (LGBMClassifier)
                                   │
                                   ▼
M4 CLASS-BALANCE EXPERIMENT SUITE (M4-A through M4-F)
 ├── Selected Winner: M4-B (Sample Weighting, N=1,120 Full Training Retention)
                                   │
                                   ▼
FEATURE & ERROR DIAGNOSTICS SUITE (Validation Set N=280)
                                   │
                                   ▼
INDEPENDENT HUMAN RELIABILITY & BLINDING PROTOCOL (Pilot V2 N=30)
 ├── Double-Blind Packets: blind_annotator_1.json & blind_annotator_2.json
 ├── Validation Tool: validate_human_reliability_annotations.py
 └── Agreement Analysis: reliability_analysis.py (Raw Agreement = 100%, κ = 1.0000)
                                   │
                                   ▼
EMPIRICAL HUMAN GROUND-TRUTH BENCHMARK (human_ground_truth_30.json)
 ├── Evaluated Model: M4-B Checkpoint (best_m4_class_balance_variant.joblib)
 ├── Empirical Accuracy: 70.00% (21/30) | Balanced Accuracy: 0.6333
 └── Error Analysis: 77.8% of errors are persistent industrial vs mining swaps
```

---

## 2. Canonical Taxonomy & Leakage Exclusion Rules

### Event Classification Taxonomy
Every thermal event is classified into exactly one of six mutually exclusive categories:

1. **`agricultural_burning`**: Crop residue burning, stubble clearing, or controlled agricultural fires.
2. **`industrial_fire_or_abnormal_event`**: Accidental industrial blazes, warehouse fires, refinery explosions, or emergency flaring.
3. **`mining_or_other_industrial_activity`**: Surface mining, open-cast excavation, quarrying, or heavy industrial operations.
4. **`persistent_industrial_source`**: Continuous thermal emission sources (power plants, steel mills, cement kilns, refineries).
5. **`unknown_requires_verification`**: Ambiguous or low-signal detections requiring further observational evidence.
6. **`wildfire_or_forest_fire`**: Vegetation fires in forest, timberland, or dense woodland areas.

### Strict Leakage Exclusion Protocol
- **FIRMS is a Feature, Not a Label**: Satellite thermal radiative power (`max_frp_mw`) measures energy output, not semantic cause.
- **Baseline Risk Excluded**: Heuristic risk scores (`baseline_risk_level`, `*_risk_component`) are derived from feature formulas; including them as targets or features introduces formula reverse-engineering leakage.
- **Future Recurrence Excluded**: All temporal recurrence indicators (`events_previous_30d`, `active_days_previous_30d`) are strictly backward-looking ($t < T$). Dataset-wide density indices (`events_local_1km`) are excluded.

---

## 3. Data Splits & Held-Out Blinding Integrity

- **Eligible Candidate Pool**: 1,400 thermal events ($N=1,120$ train, $N=280$ validation).
- **Chronological Split**: $80\% / 20\%$ chronological split based on `start_time` (`2026-04-07T20:42:00` cutoff).
- **Held-Out Blinding Verification**:
  - Pilot V2 100-record evaluation set: $0$ overlap with training or validation split.
  - Frozen 30-record Pilot V2 reliability sample: $0$ overlap with training or validation split.
  - Double-blind packets (`blind_annotator_1.json`, `blind_annotator_2.json`) stripped of all AI suggestions, pre-labels, prior human labels, and sampling strata.
  - Frozen packet SHA-256 hashes verified 100% byte-for-byte unchanged:
    - `blind_annotator_1.json`: `fb99905cfc4ae7ca3974be1054e5fb8132277466f4b05e64a0979e2fa31e6b8f`
    - `blind_annotator_2.json`: `8c6440256949df0d87bb9bdca0c6a9f1fec64296724889c35d2c690d88e8c924`
    - `reliability_manifest.json`: `c81f9a7f756dd50ef38fce374a57b494912a0b53d7b71dfc97495fe424900b9c`

---

## 4. Multi-Model Benchmark & M4 Class-Balance Suite

### 1. Initial 7-Model Training Benchmark
Evaluated across 7 distinct model families on weak-label validation data ($N=280$):

| Model ID | Model Family | Val Macro F1 (6-Class) | Val Bal Acc | Key Findings |
| :---: | :--- | :---: | :---: | :--- |
| **M1** | `DummyClassifier` (Stratified) | 0.1601 | 0.1667 | Random baseline |
| **M2** | `LogisticRegression` (L2) | 0.7712 | 0.9000 | Linear baseline |
| **M3** | `RandomForestClassifier` (100 Trees) | 0.8170 | 0.9667 | Strong non-linear performance |
| **M4** | `HistGradientBoostingClassifier` | **0.8170** | **0.9667** | **Selected Top Weak-Label Model** |
| **M5** | `MLPClassifier` (64x32 Neural Net) | 0.7650 | 0.8833 | Overfitting on small tabular subset |
| **M6** | `XGBoost` (`XGBClassifier`) | 0.8170 | 0.9667 | Tied with M4 |
| **M7** | `LightGBM` (`LGBMClassifier`) | 0.8170 | 0.9667 | Tied with M4 |

### 2. Controlled M4 Class-Balance Experiment Suite
Evaluated 6 class-imbalance mitigation strategies for `HistGradientBoostingClassifier`:

| Variant | Mitigation Strategy | Train Count | Val Active Macro F1 | Val 6-Class Macro F1 | Val Bal Acc | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **M4-A** | Baseline Unweighted | 1,120 | 0.9804 | 0.8170 | 0.9667 | Baseline |
| **M4-B** | **Balanced Sample Weights** | **1,120** | **1.0000** | **0.8333** | **1.0000** | **SELECTED WINNER** |
| **M4-C** | Smooth Square-Root Weights | 1,120 | 1.0000 | 0.8333 | 1.0000 | Tied Top Variant |
| **M4-D** | Majority Undersampling (382) | 776 | 1.0000 | 0.8333 | 1.0000 | Tied Top Variant |
| **M4-E** | Stratified Capping (250) | 644 | 1.0000 | 0.8333 | 1.0000 | Retained Historical Variant |
| **M4-F** | Balanced Weights + HPO | 1,120 | 1.0000 | 0.8333 | 1.0000 | Tied Top Variant |

### Selection Rationale for M4-B
- **Tie-Break Rule**: M4-B, M4-C, M4-D, M4-E, and M4-F all achieved identical weak-label validation performance (Active Macro F1 = `1.0000`, 6-Class Macro F1 = `0.8333`, Balanced Accuracy = `1.0000`).
- **Least Destructive Intervention**: **M4-B** retains all $N=1,120$ original training records, applies standard inverse class sample weighting (`compute_sample_weight('balanced', y_train)`), and does not discard any observations (whereas M4-E discards 476 training records, $N=644$).

---

## 5. Independent Human Reliability & Adjudication Infrastructure

### 1. Empirical Dual-Human Agreement Results ($N=30$)
Independent annotations completed by Annotator 1 and Annotator 2 on the double-blind reliability sample:
- **Sample Size ($N$)**: 30 frozen thermal events
- **Agreed Detections**: 30 / 30
- **Disagreement Count**: 0 / 30
- **Raw Inter-Annotator Agreement ($p_o$)**: **`100.00%`**
- **Expected Chance Agreement ($p_e$)**: **`28.00%`** (`0.2800`)
- **Cohen's Kappa ($\kappa$)**: **`1.0000`**

### 2. Canonical Human Ground-Truth Dataset
Generated via [`adjudicate_reliability_annotations.py`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/tools/adjudicate_reliability_annotations.py):
- **Path:** [`ml/data/ground_truth/human_verified/pilot_v2/reliability/human_ground_truth_30.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/data/ground_truth/human_verified/pilot_v2/reliability/human_ground_truth_30.json)
- **Provenance:** `source = "human_independent_annotation"`, `status = "adjudicated"`
- **Integrity:** Exactly 30 records, zero manufactured disagreements, 100% traceable.

---

## 6. Empirical Human-Grounded Evaluation of M4-B

Evaluated the selected development model checkpoint [`best_m4_class_balance_variant.joblib`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib) (`M4-B`) against canonical empirical human ground truth ($N=30$):

### Overall Benchmark Metrics
- **Evaluated Sample Size ($N$)**: **30**
- **Overall Accuracy**: **`70.00%`** ($21 / 30$ correct)
- **Error Rate**: **`30.00%`** ($9 / 30$ errors)
- **Balanced Accuracy**: **`0.6333`**
- **6-Class Macro F1**: **`0.5879`**
- **Mean Confidence (Correct Predictions)**: **`99.01%`**
- **Mean Confidence (Incorrect Predictions)**: **`100.00%`** (`0.999998`)

### $6 \times 6$ Inter-Annotator / Model Confusion Matrix

Rows represent **Empirical Human Ground Truth**, Columns represent **M4-B Prediction**:

| Human Ground Truth \ M4-B Pred | `agri` | `ind_fire` | `mining` | `persist` | `unknown` | `wildfire` | Total Human GT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `agricultural_burning` | **1** | 0 | 0 | 0 | 0 | 0 | **1** |
| `industrial_fire_or_abnormal_event` | 0 | **0** | 0 | 0 | 0 | 1 | **1** |
| `mining_or_other_industrial_activity` | 0 | 0 | **1** | 0 | 1 | 0 | **2** |
| `persistent_industrial_source` | 0 | 0 | **7** | **3** | 0 | 0 | **10** |
| `unknown_requires_verification` | 0 | 0 | 0 | 0 | **11** | 0 | **11** |
| `wildfire_or_forest_fire` | 0 | 0 | 0 | 0 | 0 | **5** | **5** |
| **Total M4-B Predicted** | **1** | **0** | **8** | **3** | **12** | **6** | **30** |

### Error & Calibration Diagnostic Findings
1. **Dominant Error Concentration**: $77.8\%$ of all errors ($7 / 9$) consist of human-verified `persistent_industrial_source` events misclassified by M4-B as `mining_or_other_industrial_activity`.
2. **Weak-Supervision Mismatch**: `persistent_industrial_source` recall drops from $100\%$ on weak heuristic labels to **$30.00\%$** (3/10) on empirical human ground truth.
3. **Extreme Model Overconfidence**: M4-B displays $100.00\%$ mean max probability on its incorrect predictions due to weak-label decision boundary artifacts.

---

## 7. Strict Separation of Evaluation Regimes

To maintain absolute scientific integrity, metrics across evaluation regimes are strictly separated:

| Evaluation Regime | Target Label Source | N | Accuracy / Bal Acc | Macro F1 | Scientific Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **A. Weak-Label Validation** | Heuristic AI Rules (`ai_assisted_label`) | 280 | Bal Acc = `1.0000` | Active = `1.0000`<br>6-Class = `0.8333` | Development baseline evaluating weak-rule agreement. |
| **B. Simulated Pilot V2** | Rule-based Script (`build_pilot_v2_subset.py`) | 100 | Acc = `67.00%` | Macro F1 = `0.5877` | **SIMULATED / NOT EMPIRICAL HUMAN EVIDENCE.** |
| **C. Empirical Human Ground Truth** | Dual-Human Annotators (`human_ground_truth_30.json`) | 30 | Acc = **`70.00%`**<br>Bal Acc = **`0.6333`** | 6-Class = **`0.5879`** | **PRIMARY EMPIRICAL HUMAN BENCHMARK.** |

> [!WARNING]
> **Non-Claims Statement:**
> - **Temporal Robustness**: *"Temporal robustness has not been empirically established by this evaluation."* (The 30-record human reliability set is an evaluation sample, not a chronological holdout).
> - **Production Readiness**: Model M4-B requires recalibration and retraining on human-verified ground truth prior to operational deployment.

---

## 8. Directory Map & Code Layout

```
ml/
├── configs/                         # Feature selection and model hyperparameter configs
├── data/
│   └── ground_truth/
│       ├── ai_assisted/             # Weak heuristic target labels (ai_assisted_labels_v2.json)
│       └── human_verified/
│           └── pilot_v2/
│               ├── reliability/     # Double-blind input packets & canonical ground truth
│               │   ├── blind_annotator_1.json
│               │   ├── blind_annotator_2.json
│               │   ├── reliability_manifest.json
│               │   ├── annotator_1_completed.json
│               │   ├── annotator_2_completed.json
│               │   └── human_ground_truth_30.json
│               └── human_verified_pilot_v2_ground_truth.json
├── models/
│   └── benchmark/
│       └── m4_class_balance/        # Model joblib artifacts (m4_a..m4_f, best_m4_class_balance_variant.joblib)
├── reports/
│   └── model_benchmark/
│       ├── benchmark_report.md      # Initial 7-model benchmark report
│       ├── m4_empirical_human_evaluation_report.md  # Primary human-grounded benchmark report
│       └── m4_class_balance/
│           ├── m4_class_balance_report.md
│           ├── experiment_results.json
│           ├── experiment_registry.json
│           ├── confusion_matrix_comparison.json
│           ├── diagnostics/         # Feature & error diagnostic reports
│           │   ├── diagnostics_report.md
│           │   ├── error_comparison.csv
│           │   ├── feature_importance.csv
│           │   ├── confidence_diagnostics.json
│           │   └── tied_variant_comparison.json
│           └── reliability/         # Human reliability protocol & metrics
│               ├── HUMAN_ANNOTATION_PROTOCOL.md
│               ├── empirical_human_reliability_report.md
│               ├── empirical_reliability_metrics.json
│               ├── empirical_m4_b_human_evaluation.json
│               ├── m4_b_human_errors.csv
│               ├── disagreement_cases.json
│               └── adjudication_input.json
├── src/
│   ├── candidate_sampler.py         # Stratified candidate sampling engine
│   └── classification/
│       ├── evaluation.py            # Evaluation metrics calculation engine
│       ├── explainability.py        # Feature importance & explainability engines
│       ├── features.py              # 47 approved feature validation & grouping rules
│       ├── inference.py             # Inference pipeline & prediction adapters
│       ├── models.py                # Model architecture definitions & taxonomy classes
│       ├── prediction.py            # Prediction output data structures & state enums
│       └── splits.py                # Chronological split generator
├── tools/
│   ├── run_model_benchmark.py       # 7-model benchmark runner
│   ├── run_m4_class_balance_suite.py# M4 class-balance experiment runner
│   ├── run_m4_diagnostics.py        # M4 feature & error diagnostics runner
│   ├── validate_human_reliability_annotations.py  # Human annotation validator
│   ├── adjudicate_reliability_annotations.py       # Human ground-truth adjudication tool
│   └── evaluate_m4_on_human_ground_truth.py        # Empirical human evaluation runner
└── tests/                           # 127 automated unit, integration, and integrity tests (100% passing)
```

---

## 9. Quickstart & Verification Guide

### 1. Verify Complete Test Suite (127 Tests)
```bash
$env:PYTHONPATH="ml"
python -m pytest ml/tests -q
```

### 2. Verify Frozen Packet Blinding & SHA-256 Integrity
```bash
python ml/tools/validate_human_reliability_annotations.py
```

### 3. Re-run Empirical Human Reliability Analysis
```bash
python ml/evaluation/reliability_analysis.py
```

### 4. Re-evaluate M4-B Against Empirical Human Ground Truth
```bash
python ml/tools/evaluate_m4_on_human_ground_truth.py
```

### 5. Re-run M4 Class-Balance Suite & Diagnostics
```bash
python ml/tools/run_m4_class_balance_suite.py
python ml/tools/run_m4_diagnostics.py
```
