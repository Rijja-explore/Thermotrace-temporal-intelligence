# 🧠 ThermoTrace Machine Learning & Ground-Truth Architecture

> Operational GeoAI Classifier, Temporal Deep Learning Sequence Models, and Explainable AI (XAI) for Industrial Thermal Intelligence.

---

## 📊 1. Core Machine Learning Models

ThermoTrace utilizes a specialized ensemble of models designed specifically for satellite thermal anomaly classification and temporal trajectory modeling:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          THERMOTRACE CORE ML & XAI STACK                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. HistGradientBoosting (HGB) │ Contextual event classification (Industrial, Wildfire) │
│ 2. LSTM Neural Network        │ Sequential temporal trajectory & multi-pass momentum   │
│ 3. SHAP Feature Attribution   │ Local & global explainability ("Why this prediction?") │
│ 4. DiCE Counterfactual Engine │ "What-If" actionable counterfactual explanations       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. HistGradientBoosting Classifier (`services/classification/models.py`)
- **Champion Artifact**: `models/trained/m4_hgb_v1.26.0-Adaptive.joblib`
- **Trained Model**: Scikit-Learn `HistGradientBoostingClassifier`
- **6-Class Operational Taxonomy**:
  1. `persistent_industrial_source`: Permanent flare stacks, smelters, cement kilns, refinery heaters.
  2. `industrial_fire_or_abnormal_event`: Accidental industrial fires, runaway flaring, tank farm explosions.
  3. `wildfire_or_forest_fire`: Forest, brush, or wilderness canopy fires.
  4. `agricultural_burning`: Crop stubble burning in agricultural zones.
  5. `mining_or_other_industrial_activity`: Coal seam fires, slag heaps, open cast mining.
  6. `unknown_requires_verification`: Ambiguous thermal signals requiring analyst review.
- **Evaluation Performance**:
  - **Accuracy**: **95.65%**
  - **Weighted F1**: **0.9357**
  - **Macro F1**: **0.7400**
  - **Industrial Recall**: **75.00%**
  - **Agricultural & Wildfire Precision**: **100.00%**

---

### 2. Multi-Task PyTorch Recurrent LSTM (`services/classification/lstm_temporal.py`)
- **Class**: `ThermalLSTMModel(nn.Module)`
- **Input Topology**: 10-dimensional feature vector per satellite pass:
  1. FRP (Normalized MW)
  2. Brightness Temperature $T_4$ (K)
  3. Spectral Differential $\Delta T_{31} = T_4 - T_{11}$ (K)
  4. Velocity $\frac{d\text{FRP}}{dt}$ (MW/day)
  5. Acceleration $\frac{d^2\text{FRP}}{dt^2}$ ($\text{MW/day}^2$)
  6. 90-Day Persistence Recurrence Ratio
  7. Day/Night Pass Binary Flag ($0 = \text{Night}, 1 = \text{Day}$)
  8. Normalized Distance to Nearest Facility (km)
  9. Rolling Baseline $Z$-score
  10. Daily Satellite Pass Frequency
- **Dual Output Heads**:
  - **Classification Head**: 4-State Escalation State Machine (`STABLE`, `WATCH`, `ESCALATING`, `CRITICAL_ESCALATION`).
  - **Regression Head**: Autoregressive next-pass FRP predictions ($T+24\text{h}$ and $T+48\text{h}$ forecast in MW).

---

### 3. Explainable AI (XAI) with SHAP (`services/classification/explainability.py`)
- Computes TreeSHAP / KernelSHAP values for all contextual features.
- Enables analysts to inspect the exact contribution of each physical feature to the classification score.

---

### 4. Counterfactual Explanations with DiCE (`apps/frontend/src/pages/WhatIfSimulator.tsx`)
- Generates Diverse Counterfactual Explanations showing what operational changes (e.g. reducing flaring rate, increasing buffer distance) would transition an alert from **Critical Escalation** back to **Permitted Baseline**.

---

## 🔄 2. Closed-Loop Continuous Feedback & Retraining Gate

1. **Analyst Ground-Truth Ingestion**:
   - Every analyst verification in the web console is cryptographically signed and stored in `data/feedback/analyst_feedback.json`.
2. **Automated Validation Gate (`services/classification/retraining_gate.py`)**:
   - A candidate model is only promoted if $\text{Validation Macro-F1} \ge 0.82$ and industrial recall does not regress.
3. **Automated Rollback Engine**:
   - If a deployed model experiences production drift or regression, an automated rollback restores the previous champion artifact in $<100\text{ms}$.
