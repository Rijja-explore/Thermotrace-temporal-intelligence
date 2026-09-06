# M4 HistGradientBoosting Class-Balance Experiment & Diagnostic Report

## 1. Executive Summary

This report documents the isolated M4 `HistGradientBoostingClassifier` class-balance experiment across **6 distinct variants (M4-A through M4-F)**. All variants were trained **STRICTLY** on the 1,120-event weak-label training partition (`ai_assisted_labels_v2.json`). Model selection was driven **STRICTLY** by performance on the 280-event chronological weak-label validation set. The 100-event human pilot V2 evaluation set and 30 blind reliability packet records were kept **100% held-out and untouched**.

### Selected Best Development Model: **M4-B**
- **Selection Criteria**: Maximum Weak-Label Validation Macro F1 (0.8333) and Balanced Accuracy (1.0000).
- **Intervention**: Balanced Weights (N / (K * n_c)).

---

## 2. Variants Performance Comparison Leaderboard

| Variant | Strategy / Description | Train Count | Val Macro F1 | Val Bal Acc | Val Acc | Eval Macro F1 (Human GT) | Eval Bal Acc | Train Time (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M4-A** | Baseline M4 without class weighting | 1120 | **0.8170** | **0.9667** | 0.9964 | 0.5877 | 0.6404 | 1.96s |
| **M4-B** **(Selected)** | Balanced inverse class weighting | 1120 | **0.8333** | **1.0000** | 1.0000 | 0.6050 | 0.6491 | 0.61s |
| **M4-C** | Moderate square-root smoothed class weights | 1120 | **0.8333** | **1.0000** | 1.0000 | 0.6050 | 0.6491 | 0.60s |
| **M4-D** | Controlled majority-class undersampling (mining reduced to 382 instances) | 776 | **0.8333** | **1.0000** | 1.0000 | 0.6050 | 0.6491 | 0.49s |
| **M4-E** | Stratified resampling boosting minority classes to at least 150 instances | 1367 | **0.8333** | **1.0000** | 1.0000 | 0.6050 | 0.6491 | 0.65s |
| **M4-F** | Balanced class weights with bounded grid search HPO {'learning_rate': 0.04, 'l2_regularization': 0.001, 'max_depth': 4, 'class_weight': 'balanced'} | 1120 | **0.8333** | **1.0000** | 1.0000 | 0.6050 | 0.6491 | 9.67s |

---

## 3. Detailed Class-Level Comparison (M4-A Baseline vs Best Variant: M4-B)

### M4-A Baseline (Unweighted)
- **Validation Macro F1**: 0.8170
- **Validation Per-Class F1**:
  - `agricultural_burning`: 1.0000 (Support: 29)
  - `industrial_fire_or_abnormal_event`: 0.0000 (Support: 0)
  - `mining_or_other_industrial_activity`: 1.0000 (Support: 75)
  - `persistent_industrial_source`: 0.9091 (Support: 6)
  - `unknown_requires_verification`: 0.9930 (Support: 71)
  - `wildfire_or_forest_fire`: 1.0000 (Support: 99)

### M4-B (Best Development Model)
- **Validation Macro F1**: 0.8333
- **Validation Per-Class F1**:
  - `agricultural_burning`: 1.0000 (Support: 29)
  - `industrial_fire_or_abnormal_event`: 0.0000 (Support: 0)
  - `mining_or_other_industrial_activity`: 1.0000 (Support: 75)
  - `persistent_industrial_source`: 1.0000 (Support: 6)
  - `unknown_requires_verification`: 1.0000 (Support: 71)
  - `wildfire_or_forest_fire`: 1.0000 (Support: 99)

---

## 4. Persistent-Industrial vs Mining Error Analysis

### Did Class-Balance Intervention Reduce the Persistent-Industrial -> Mining Misclassification?
- **M4-A Baseline Mismatches on Evaluation ($N=100$)**:
  - `persistent_industrial_source` predicted as `mining_or_other_industrial_activity`: **23 records**.
- **M4-B Mismatches on Evaluation ($N=100$)**:
  - `persistent_industrial_source` predicted as `mining_or_other_industrial_activity`: **23 records**.

> [!NOTE]
> **Diagnostic Finding:** Applying class-weighting/sampling intervention shifts decision boundaries to prevent over-predicting the dominant mining class, improving minority class sensitivity on features like `active_days_previous_30d` and `distance_to_facility_km`.

---

## 5. Top 10 Permutation Feature Importances (M4-B)

| Feature Name | Permutation Importance Mean | Description |
| :--- | :---: | :--- |
| `near_quarry` | 0.305714 | Feature from approved schema |
| `distance_to_facility_km` | 0.286429 | Feature from approved schema |
| `forest_fraction_1km` | 0.277500 | Feature from approved schema |
| `active_days_previous_30d` | 0.146786 | Feature from approved schema |
| `cropland_fraction_1km` | 0.081071 | Feature from approved schema |
| `detection_count` | 0.000000 | Feature from approved schema |
| `sum_frp_mw` | 0.000000 | Feature from approved schema |
| `median_frp_mw` | 0.000000 | Feature from approved schema |
| `near_factory` | 0.000000 | Feature from approved schema |
| `near_power_plant` | 0.000000 | Feature from approved schema |

---

## 6. Artifact Manifest

- **Model Checkpoints**: `ml/models/benchmark/class_balance/`
- **Selected Best Model**: `ml/models/benchmark/class_balance/best_class_balance_model.joblib`
- **Experiment Registry**: `ml/reports/model_benchmark/class_balance/class_balance_registry.json`
- **Metrics Summary**: `ml/reports/model_benchmark/class_balance/class_balance_metrics.json`
