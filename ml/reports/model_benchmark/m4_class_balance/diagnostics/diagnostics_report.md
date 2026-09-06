# Thermotrace M4 Feature & Error Diagnostics Report

## 1. Executive Summary & Verification Statements

This report presents a thorough, zero-test-set-contamination diagnostic audit comparing **`M4-B`** (selected class-balanced development model) against **`M4-A`** (unweighted baseline) strictly on the $N=280$ weak-label validation set.

### Verification Assertions
- **Selected Development Model**: **`M4-B`** (retrieves top performance retaining all $N=1,120$ training records with balanced sample weights).
- **Validation Dataset**: Evaluated on exactly $N=280$ weak-label validation records (`2026-04-07T20:42:00` to `2026-08-22T20:27:00`).
- **Zero Test Contamination**: 0 Pilot V2 evaluation records and 0 blind reliability packet records were loaded or inspected.
- **Approved Feature Schema**: Generated strictly using the 47 approved features from [`features.py`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/src/classification/features.py).

---

## 2. Confusion Matrices & Row-Normalized Metrics ($N=280$ Validation Set)

### M4-A Baseline (Unweighted)
- **Validation Macro F1 (6-Class)**: `0.8170` \| **Balanced Accuracy**: `0.9667`
- **Per-Class Metrics**:
  - `agricultural_burning`: Precision = 1.0000, Recall = 1.0000, F1 = 1.0000 (Support: 29)
  - `mining_or_other_industrial_activity`: Precision = 1.0000, Recall = 1.0000, F1 = 1.0000 (Support: 75)
  - `persistent_industrial_source`: Precision = 1.0000, Recall = 0.8333, F1 = 0.9091 (Support: 6)
  - `unknown_requires_verification`: Precision = 0.9861, Recall = 1.0000, F1 = 0.9930 (Support: 71)
  - `wildfire_or_forest_fire`: Precision = 1.0000, Recall = 1.0000, F1 = 1.0000 (Support: 99)
  - `industrial_fire_or_abnormal_event`: Precision = 0.0000, Recall = 0.0000, F1 = 0.0000 (Support: 0)

### M4-B Class-Balanced (Selected Winner)
- **Validation Macro F1 (6-Class)**: **`0.8333`** ($\Delta = +0.0163$) \| **Balanced Accuracy**: **`1.0000`** ($\Delta = +0.0333$)
- **Per-Class Metrics**:
  - `agricultural_burning`: Precision = 1.0000, Recall = 1.0000, F1 = 1.0000 (Support: 29)
  - `mining_or_other_industrial_activity`: Precision = 1.0000, Recall = 1.0000, F1 = 1.0000 (Support: 75)
  - `persistent_industrial_source`: **Precision = 1.0000, Recall = 1.0000, F1 = 1.0000** (Support: 6)
  - `unknown_requires_verification`: **Precision = 1.0000, Recall = 1.0000, F1 = 1.0000** (Support: 71)
  - `wildfire_or_forest_fire`: Precision = 1.0000, Recall = 1.0000, F1 = 1.0000 (Support: 99)
  - `industrial_fire_or_abnormal_event`: Precision = 0.0000, Recall = 0.0000, F1 = 0.0000 (Support: 0)

---

## 3. Persistent Industrial Error Analysis

- **`persistent_industrial_source` Recall Change**: M4-A = **83.33%** (5/6) $	o$ M4-B = **100.00%** (6/6).
- **Persistent $	o$ Mining Misclassifications**:
  - **M4-A**: 0 records misclassified as mining.
  - **M4-B**: 0 records misclassified as mining.
- **Errors Fixed by M4-B**: Exactly **1 error fixed** on validation (`TT-EVT-00109968`, which M4-A misclassified as `unknown_requires_verification` due to weak decision boundaries).
- **New Errors Introduced by M4-B**: **0 new errors**.

---

## 4. Feature Importance & Contribution Analysis

Top 5 Permutation Feature Importances on $N=280$ Validation Set (M4-B):

| Rank | Feature Name | M4-A Importance | M4-B Importance | Importance Delta ($\Delta$) | Functional Feature Group |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | `near_quarry` | 0.3157 | **0.3057** | -0.0100 | Group D (Infrastructure) |
| **2** | `distance_to_facility_km` | 0.2912 | **0.2864** | -0.0048 | Group D (Infrastructure) |
| **3** | `forest_fraction_1km` | 0.2801 | **0.2775** | -0.0026 | Group C (Land Cover) |
| **4** | `active_days_previous_30d` | 0.1250 | **0.1468** | **+0.0218** | Group B (Temporal) |
| **5** | `cropland_fraction_1km` | 0.0821 | **0.0811** | -0.0010 | Group C (Land Cover) |

> [!NOTE]
> **Key Feature Finding:** M4-B increases reliance on `active_days_previous_30d` (+0.0218 importance delta), enabling the model to distinguish persistent thermal activity from transient anomalies.

---

## 5. Confidence & Calibration Diagnostics

- **M4-A Baseline**:
  - Overall Mean Confidence: `98.98%`
  - Correct Predictions Mean Confidence: `99.01%`
  - Incorrect Predictions Mean Confidence: `90.12%` (1 high-confidence error)
- **M4-B Class-Balanced**:
  - Overall Mean Confidence: `99.12%`
  - Correct Predictions Mean Confidence: `99.12%` (100% accurate on validation, 0 validation errors)
  - High-confidence Errors: **0 errors** on validation.

---

## 6. Tied-Variant Review & Selection Rationale

Variants **M4-B, M4-C, M4-D, M4-E, and M4-F** all achieved **1.0000 validation Macro F1 across active training classes** (`0.8333` across the 6-class taxonomy).

- **M4-B (Balanced Weights - Selected Development Model)**: Retains all 1,120 training records, does not discard observations, and applies standard balanced sample weighting (`compute_sample_weight('balanced', y_train)`).
- **M4-E (Stratified Capping)**: Caps majority mining class to 250 records (dropping 476 training records).
- **Selection Rationale**: **M4-B is the defensible development winner** because it represents the least destructive / simplest intervention among the tied top-performing variants while achieving identical weak-label validation performance.

---

## 7. Mandatory Diagnostic Conclusions

### A. What IS Demonstrated by Diagnostics:
1. **Weak-Label Validation Behavior**: M4-B resolves the single validation error (`TT-EVT-00109968`), achieving $100\%$ accuracy across active weak-label validation classes.
2. **Error Reduction**: Persistent industrial recall increases from $83.33\%$ to $100\%$ on weak labels.
3. **Feature Importance**: Temporal persistence (`active_days_previous_30d`) and infrastructure proximity (`distance_to_facility_km`, `near_quarry`) drive decision boundary logic.

### B. What is NOT Demonstrated:
1. **Human-Grounded Accuracy**: Validation perfection reflects agreement with weak heuristic rules (`ai_assisted_label`), **NOT** human ground truth.
2. **Empirical Human Reliability**: Unproved until real dual-human annotations are completed.
3. **Temporal Robustness against Human Labels**: Unproved until evaluated against future human-verified time periods.
4. **Production Readiness**: Model selection remains weak-supervision only.
