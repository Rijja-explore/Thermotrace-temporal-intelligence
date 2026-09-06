# Investigation Prioritization Model Audit

## 1. Mathematical Objective
The mathematical objective is to calculate an `investigation_priority` score and map it to a categorical tier (`HIGH`, `MEDIUM`, `LOW`). The score is computed as:

`priority_score = baseline_score + (anomaly_score * 50)`

- `anomaly_score`: The negated output of the Isolation Forest's `decision_function` (higher = more anomalous).
- `baseline_score`: A deterministic sum of observation characteristics and context:
  `max_frp_mw * 0.1 + detection_count * 1.0 + events_previous_30d * 5.0 + (20.0 if distance_to_facility_km < 2.0 else 0.0)`
- `priority_tier`: Thresholded at > 50 (`HIGH`), > 20 (`MEDIUM`), else `LOW`.

## 2. Baseline Audit
The deterministic baseline does **not** reproduce synthetic risk scores. It strictly utilizes physical scalars (FRP, detection counts), historical frequency (events in previous 30 days), and proximity thresholds.
The facility proximity score (`+20.0` for `< 2.0` km) acts explicitly as an investigation relevance booster (e.g., routing a thermal anomaly near a refinery to an industrial analyst). It mathematically contains no semantic or class-label inference (it does not output "industrial fire probability").

## 3. Isolation Forest Audit
- **Configuration**: `IsolationForest(contamination=0.1, random_state=42)`
- **Preprocessing**: `StandardScaler()` with `fillna(0)` for missing values.
- **Training Data**: Unlabeled feature vectors strictly filtered to `APPROVED_FEATURES` and the selected ablation group.
- **Leakage**: Prevented via the `validate_features()` boundary inside the `fit()` method.
- **Limitations**: The current smoke test uses 100 random events, which is insufficient for a global anomaly model on ~1M events. Furthermore, `fit()` does not enforce a temporal holdout, meaning a live event could theoretically exist in its own training set. This is acceptable for a ranking prototype, but must be addressed in production.

## 4. Data Leakage and Circularity
The implementation successfully averts circularity. The `validate_features()` function explicitly crashes the pipeline if `baseline_risk_score`, `baseline_risk_level`, or heuristic fields like `events_local_7d` are presented. The model natively outputs only an `investigation_priority` without claiming semantic conclusions. Historical temporal features (`events_previous_30d`) are properly verified to remain historically backwards-looking.

## 5. Feature Dominance Audit
While specific Shapley values are not natively exported by this prototype implementation, algebraic inspection indicates that extreme values of `max_frp_mw` (e.g., > 500 MW) can easily dominate the `priority_score` (yielding +50 or more to the baseline). This behaves as expected for an investigation ranking (massive fires demand investigation), but deeper feature-dominance analysis tools remain a limitation.

## 6. Ablation Audit
The ablation logic accurately applies feature-mask boundaries using the `ABLATION_GROUPS` definitions from `features.py`. The permutations correctly alter the ranking behavior:
- A (Thermal)
- B (+Temporal)
- C (+Environmental)
- D (+Infrastructure)
The readiness report rightfully describes this as "ranking behavior / prioritization sensitivity diagnostics", making no claim of classification performance.

## 7. Real Event Audit (`TT-EVT-00141704`)
The event was extracted and run. The JSON payload successfully serialized, verifying:
- Score is reproducible (`20.62` for Group D).
- Tier behaves deterministically (`MEDIUM`).
- The `explanations` array maps cleanly to factual metadata (e.g., "Maximum observed FRP was 81.3 MW").
- **No semantic probabilities**, causal logic, or fabricated evidence exist in the output.

## 8. Evaluation Claims Audit
The `investigation_priority_readiness_report.md` correctly abstains from reporting F1, ROC-AUC, or accuracy metrics. The evaluation relies strictly on ranking outputs and ablation behavior, conforming precisely to the label-free constraint.

## 9. Test Quality Audit
The `test_investigation_priority.py` suite effectively checks for missing values, serialization, and leakage rejection. 
- **Defect found**: The original tests lacked an exact arithmetic regression check for the `_deterministic_baseline` scoring formula.
- **Fix made**: I added `test_baseline_exact_arithmetic` to verify the precise algebraic combination of FRP, counts, and proximity.

## 10. Final Verdict
The software implementation of the label-free investigation prioritization system is thoroughly robust and strictly adheres to semantic separation rules. While the model effectiveness as a triage tool is promising, its operational hit rate remains scientifically unvalidated until ground truth is eventually obtained.

**INVESTIGATION_PRIORITIZATION_AUDIT_PASS**
