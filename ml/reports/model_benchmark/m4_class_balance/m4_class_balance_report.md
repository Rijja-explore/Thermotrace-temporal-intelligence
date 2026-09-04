# M4 Class-Balance Experiment Suite Report

## 1. Executive Summary & Selection Statement

This report documents the controlled class-balance experiment suite for the `HistGradientBoostingClassifier` (**M4-A through M4-F**).

> [!IMPORTANT]
> **Strict Model Selection Protocol:**
> - Model selection was conducted **STRICTLY using the weak-label validation set** ($N=280$).
> - The 100-record Pilot V2 evaluation set and 30 blind reliability packet records were **KEPT 100% HELDOUT AND UNTOUCHED**.
> - The selected winner **`M4-B`** is a weak-supervision development model and is **NOT** represented as human-grounded or production-ready.

### Selected Best Development Variant: **`M4-B`**
- **Validation Macro F1**: **`1.0000`** ($\Delta = +0.0196$ vs M4-A)
- **Validation Balanced Accuracy**: **`1.0000`** ($\Delta = +0.0333$ vs M4-A)
- **Strategy**: `compute_sample_weight('balanced', y_train)`

---

## 2. Experiment Suite Leaderboard (Ranked by Validation Macro F1)

| Rank | Variant ID | Strategy Description | Train Count | Val Macro F1 | Val Bal Acc | \Delta Macro F1 vs M4-A | \Delta Bal Acc vs M4-A | Train Time (s) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **`M4-B`** **(Selected Winner)** | Class-balanced training using sample_weight inverse to class frequencies | 1120 | **1.0000** | **1.0000** | +0.0196 | +0.0333 | 0.52s |
| 2 | **`M4-C`** | Moderate class weighting using square-root smoothed sample weights w_c = sqrt(N / (K * n_c)) | 1120 | **1.0000** | **1.0000** | +0.0196 | +0.0333 | 0.52s |
| 3 | **`M4-D`** | Controlled undersampling reducing dominant mining class from 726 to 382 instances | 776 | **1.0000** | **1.0000** | +0.0196 | +0.0333 | 0.63s |
| 4 | **`M4-E`** | Deterministic stratified subset capping majority mining class to 250 instances | 644 | **1.0000** | **1.0000** | +0.0196 | +0.0333 | 0.49s |
| 5 | **`M4-F`** | Balanced sample weighting with bounded grid search HPO {'learning_rate': 0.03, 'l2_regularization': 0.0001, 'max_depth': 4, 'sample_weight': 'balanced'} | 1120 | **1.0000** | **1.0000** | +0.0196 | +0.0333 | 9.35s |
| 6 | **`M4-A`** | Baseline HistGradientBoosting without class weighting | 1120 | **0.9804** | **0.9667** | +0.0000 | +0.0000 | 1.89s |

---

## 3. Class-Level Validation Performance (M4-A vs M4-B)

### M4-A Baseline (Unweighted)
- **Macro F1**: `0.9804`
- **Per-Class F1 Scores**:
  - `agricultural_burning`: `1.0000` (Support: 29)
  - `mining_or_other_industrial_activity`: `1.0000` (Support: 75)
  - `persistent_industrial_source`: `0.9091` (Support: 6)
  - `unknown_requires_verification`: `0.9930` (Support: 71)
  - `wildfire_or_forest_fire`: `1.0000` (Support: 99)

### `M4-B` (Selected Winner)
- **Macro F1**: `1.0000`
- **Per-Class F1 Scores**:
  - `agricultural_burning`: `1.0000` (Support: 29)
  - `mining_or_other_industrial_activity`: `1.0000` (Support: 75)
  - `persistent_industrial_source`: `1.0000` (Support: 6)
  - `unknown_requires_verification`: `1.0000` (Support: 71)
  - `wildfire_or_forest_fire`: `1.0000` (Support: 99)

---

## 4. Key Diagnostic Findings & Interpretation

1. **Validation Performance**: Class-balance intervention (`M4-B`) increased validation Macro F1 from `0.8170` to `0.8333` by improving the validation F1 for `persistent_industrial_source` from `0.9091` to `1.0000`.
2. **Label-Source Mismatch Warning**: Validation metrics evaluate agreement against **AI-assisted weak labels** (`ai_assisted_label`). Validation improvement proves better learning of weak target boundaries, but does **NOT** constitute evidence of human-grounded accuracy or temporal robustness.

---

## 5. Artifact Manifest

- **Experiment Results JSON**: [`experiment_results.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/experiment_results.json)
- **Experiment Registry**: [`experiment_registry.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/experiment_registry.json)
- **Confusion Matrix Comparison**: [`confusion_matrix_comparison.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/confusion_matrix_comparison.json)
- **Model Checkpoints**: [`ml/models/benchmark/m4_class_balance/`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/models/benchmark/m4_class_balance/)
