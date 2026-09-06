# Classification Readiness Report

## 1. What is implemented
- **Strict feature governance**: `features.py` mathematically forces explicit approvals of features based on the V2 schema, actively filtering identifier strings and future-leaky properties.
- **Classification algorithms**: Complete interface wrappers for traditional algorithms (Random Forest, Logistic Regression) and baseline behaviors (thermal rules) configured in `models.py` and `baseline.py`.
- **Leakage-proof evaluation strategies**: Random, Chronological, and Unseen-Facility partitioning strategies defined in `splits.py` guaranteeing deterministic non-intersecting sets.
- **Precision validation architecture**: Mathematical validation mechanisms using `sklearn.metrics`, probability normalization checks, and multi-class Brier scoring implemented in `evaluation.py`.
- **Evidence semantics**: A robust semantic promotion framework in `evidence.py` ensuring textual reporting (or lack thereof) is correctly structured as an `OBSERVATION` or `UNVERIFIED_EXTERNAL_CLAIM` without being conflated with `SEMANTIC_EVIDENCE`.

## 2. What is software-tested
Through isolated deterministic testing on small synthetic structures (`synthetic_labels_for_software_test.csv`), the architecture verifies:
- Exception handling around illegal training actions.
- Validation checks rejecting synthetic risk, identifiers, and future spatial densities.
- Complete metric reporting and arithmetic calculations in `calculate_metrics()`.
- Facility split logic preventing intersection overlaps.

## 3. What is scientifically validated
- **Nothing**. The absence of independently verified semantic labels completely voids any attempt at true validation of prediction capabilities on ThermoTrace events. The pipeline strictly exists in scaffolding.

## 4. What remains blocked
- **Model Training**: Effectively disabled, failing closed if real unverified labels are supplied.
- **Semantic Performance Reporting**: F1, precision, and recall measurements over the true historical environment.
- **Probabilistic Calibration**: Isotonic and Platt routines explicitly reject action on missing/unverified target matrices.

## 5. Exact data required to unlock real training
Future training is rigidly gated behind the ingestion of a dataset representing true, externally verifiable conditions containing:
- `event_id`
- `label`
- `label_confidence`
- `evidence_urls`
- `evidence_summary`
- `reviewer_id`
- `review_complete`
This ground-truth validation can ONLY be compiled via independent visual/spectral remote sensing confirmation, or through fully identified external authoritative government/news reports that unambiguously link back to the specific event timeline. 

## 6. Leakage controls
Any algorithmic pipeline attempt to exploit:
- Model predictions containing internal contextual identifiers.
- Synthetic risk boundaries (e.g. `baseline_risk_score`, `industrial_proximity_score`).
- Local geographical densities occurring post-incident.
will trigger explicit failure through the `validate_features` runtime hook in `features.py`. Furthermore, model validation cannot intersect facility identifiers (`splits.py`).

## 7. Evaluation protocol
Once real inputs are integrated, algorithms must pass:
- Stratified and Chronological test splits across multiple models.
- Per-class evaluation (F1/Precision/Recall).
- Scored reliability assessments.
- Systematic testing across progressively cumulative ablations (A: Thermal only, B: +Temporal, C: +Land Cover, D: +Infrastructure Context).

## 8. Known limitations
- The reliance on pre-structured geographical variables severely truncates performance potential compared to dynamic spatial mapping.
- Model calibrations are placeholders dependent on unverified conditions.

---

**CLASSIFICATION_SCAFFOLD_READY_NO_GROUND_TRUTH**
