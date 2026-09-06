# Thermotrace M4-B Empirical Human-Grounded Evaluation Report

## 1. Executive Summary

This report presents the primary **empirical human-grounded evaluation** for the selected Thermotrace development model (**`M4-B`**, `HistGradientBoostingClassifier` with balanced sample weights).

Following the successful completion of independent double-blind annotations by real human annotators (Annotator 1 and Annotator 2) on the frozen 30-record reliability sample, canonical human ground truth was established (`human_ground_truth_30.json`). `M4-B` was evaluated strictly against this empirical human ground-truth dataset.

### Key Performance Summary ($N=30$ Empirical Human Ground Truth)
- **Overall Accuracy**: **`70.00%`** ($21 / 30$ correct)
- **Error Rate**: **`30.00%`** ($9 / 30$ errors)
- **Balanced Accuracy**: **`0.6333`**
- **6-Class Macro F1**: **`0.5879`**
- **Selected Model Checkpoint**: [`best_m4_class_balance_variant.joblib`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib) (`M4-B`)

> [!IMPORTANT]
> **Methodological Boundaries & Limitations:**
> - **Empirical Human Evidence**: The $N=30$ human ground truth represents **REAL DUAL-HUMAN ANNOTATIONS** ($100\%$ inter-annotator agreement, Cohen's $\kappa = 1.0000$).
> - **Weak-Label Mismatch**: Model performance drops from $100\%$ active Macro F1 on weak labels (`ai_assisted_label`) to $70.00\%$ accuracy ($0.5879$ 6-class Macro F1) on empirical human ground truth.
> - **Dominant Error Pattern**: $77.8\%$ of model errors ($7 / 9$) consist of human-verified `persistent_industrial_source` events misclassified by M4-B as `mining_or_other_industrial_activity`.
> - **Model Overconfidence**: M4-B exhibits $100.00\%$ mean predicted probability on its incorrect predictions.
> - **Temporal Robustness**: **"Temporal robustness has not been empirically established by this evaluation."**

---

## 2. Dataset, Blinding, & Provenance Specifications

- **Evaluation Dataset Path**: [`ml/data/ground_truth/human_verified/pilot_v2/reliability/human_ground_truth_30.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/data/ground_truth/human_verified/pilot_v2/reliability/human_ground_truth_30.json)
- **Canonical Provenance**: `source = "human_independent_annotation"`, `status = "adjudicated"`
- **Sample Size ($N$)**: Exactly 30 thermal events from Pilot V2.
- **Blinding & Leakage Controls**:
  - Both human annotators received stripped blind packets (`blind_annotator_1.json`, `blind_annotator_2.json`) containing 0 AI predictions, 0 pre-labels, 0 prior human labels, and 0 sampling strata.
  - Frozen blind input packets remained 100% byte-for-byte unchanged throughout the pipeline (verified by SHA-256 hashes).
  - 0 evaluation records were included in M4-B training or validation datasets.

---

## 3. Empirical Inter-Annotator Reliability Results

Prior to model evaluation, inter-annotator consistency between Annotator 1 and Annotator 2 was validated:

- **Sample Size ($N$)**: 30 frozen thermal events
- **Agreed Detections**: 30 / 30
- **Disagreement Count**: 0 / 30
- **Raw Inter-Annotator Agreement ($p_o$)**: **`100.00%`**
- **Expected Chance Agreement ($p_e$)**: **`28.00%`** (`0.2800`)
- **Cohen's Kappa ($\kappa$)**: **`1.0000`**

### Interpretation & Limitation
- **Inter-Annotator Consistency**: Perfect agreement ($\kappa = 1.0000$) establishes that the canonical six-class taxonomy definitions and feature presentation enabled consistent, reproducible human labeling across this 30-record sample.
- **Sample Limitation**: While $\kappa = 1.0000$ proves perfect agreement within this 30-record double-blind sample, it does **not** establish universal annotator reliability across the full multi-year event population or unseen geographical noise regimes.

---

## 4. M4-B Empirical Human-Grounded Evaluation Metrics

### Overall Performance Summary
| Metric | Value | Reference / Context |
| :--- | :---: | :--- |
| **Evaluated Sample Size ($N$)** | **30** | Canonical Human GT (`human_ground_truth_30.json`) |
| **Overall Accuracy** | **70.00%** | 21 correct predictions out of 30 records |
| **Error Rate** | **30.00%** | 9 incorrect predictions out of 30 records |
| **Balanced Accuracy** | **0.6333** | Unweighted average of per-class recalls |
| **6-Class Taxonomy Macro F1** | **0.5879** | Macro average across all 6 taxonomy classes |
| **Mean Confidence (Correct)** | **99.01%** | Average model probability for correct predictions |
| **Mean Confidence (Incorrect)** | **100.00%** | Average model probability for incorrect predictions |

### Per-Class Performance Breakdown ($N=30$)

| Taxonomy Class | Precision | Recall | F1 Score | Support | M4-B Predicted Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `agricultural_burning` | **1.0000** | **1.0000** | **1.0000** | 1 | 1 |
| `industrial_fire_or_abnormal_event` | **0.0000** | **0.0000** | **0.0000** | 1 | 0 |
| `mining_or_other_industrial_activity` | **0.1250** | **0.5000** | **0.2000** | 2 | 8 |
| `persistent_industrial_source` | **1.0000** | **0.3000** | **0.4615** | 10 | 3 |
| `unknown_requires_verification` | **0.9167** | **1.0000** | **0.9565** | 11 | 12 |
| `wildfire_or_forest_fire` | **0.8333** | **1.0000** | **0.9091** | 5 | 6 |

---

## 5. $6 \times 6$ Inter-Annotator Confusion Matrix

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

---

## 6. Error & Calibration Analysis

### Detailed Error Log (9 Records)
Out of 30 evaluated records, M4-B made exactly 9 errors:

| Event ID | Empirical Human GT Label | M4-B Predicted Label | Model Confidence | Error Category |
| :--- | :--- | :--- | :---: | :--- |
| `TT-EVT-00122510` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9998%` | Dominant Class Swap |
| `TT-EVT-00220961` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9997%` | Dominant Class Swap |
| `TT-EVT-00232464` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9998%` | Dominant Class Swap |
| `TT-EVT-00242637` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9998%` | Dominant Class Swap |
| `TT-EVT-00397634` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9998%` | Dominant Class Swap |
| `TT-EVT-00438668` | `industrial_fire_or_abnormal_event` | `wildfire_or_forest_fire` | `99.9998%` | Rare Abnormal Fire Swap |
| `TT-EVT-00480931` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9998%` | Dominant Class Swap |
| `TT-EVT-00612422` | `mining_or_other_industrial_activity` | `unknown_requires_verification` | `99.9996%` | Mining Boundary Swap |
| `TT-EVT-00782256` | `persistent_industrial_source` | `mining_or_other_industrial_activity` | `99.9998%` | Dominant Class Swap |

### Key Diagnostic Findings
1. **Dominant Error Concentration**:
   - $77.8\%$ of all errors ($7 / 9$) are `persistent_industrial_source` events misclassified as `mining_or_other_industrial_activity`.
   - `persistent_industrial_source` recall drops from $100\%$ on weak labels to **$30.00\%$** (3/10) on empirical human ground truth.
2. **Model Overconfidence & Calibration Defect**:
   - Mean predicted probability on correct predictions: `99.01%`.
   - Mean predicted probability on incorrect predictions: **`100.00%`** (`0.999998`).
   - The model is extreme in its overconfidence on errors because it was trained on heuristic weak labels where mining and persistent features were artificially separated by weak threshold rules.
3. **Mining Precision Inflation**:
   - M4-B predicts `mining_or_other_industrial_activity` for 8 events, but only 1 is true mining in human ground truth (Precision = **$12.50\%$**).

---

## 7. Comparison Across Evaluation Regimes

To maintain absolute methodological clarity, metrics from different evaluation regimes are explicitly separated:

| Regime / Evaluation Source | Target Label Source | N | Accuracy / Bal Acc | Macro F1 | Status & Description |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **A. Weak-Label Validation** | Heuristic AI Rules (`ai_assisted_label`) | 280 | Bal Acc = `1.0000` | Active = `1.0000`<br>6-Class = `0.8333` | Development baseline evaluating rule agreement. |
| **B. Simulated Pilot V2** | Rule-based Script (`build_pilot_v2_subset.py`) | 100 | Acc = `67.00%` | Macro F1 = `0.5877` | **SIMULATED / NOT EMPIRICAL HUMAN EVIDENCE.** |
| **C. Empirical Human Ground Truth** | Dual-Human Annotators (`human_ground_truth_30.json`) | 30 | Acc = **`70.00%`**<br>Bal Acc = **`0.6333`** | 6-Class = **`0.5879`** | **PRIMARY EMPIRICAL HUMAN EVIDENCE.** |

> [!CAUTION]
> Metrics from Regimes A, B, and C must **NEVER** be combined, averaged, or blurred. Regime C is the sole empirical human benchmark in the project to date.

---

## 8. Limitations & Non-Claims

1. **Temporal Robustness Non-Claim**:
   - **"Temporal robustness has not been empirically established by this evaluation."**
   - The 30-record human reliability sample is an evaluation sample drawn across Pilot V2 events, not a dedicated future chronological holdout.
2. **Production Readiness Non-Claim**:
   - M4-B cannot be deployed into production without retraining on verified human ground truth or recalibrating decision thresholds, due to its $30.00\%$ error rate and extreme overconfidence on persistent vs mining industrial classes.
3. **Causal Claims Exclusion**:
   - Feature importances (`active_days_previous_30d`, `near_quarry`) describe decision tree splits inside HistGradientBoostingClassifier, not physical causal mechanisms.
