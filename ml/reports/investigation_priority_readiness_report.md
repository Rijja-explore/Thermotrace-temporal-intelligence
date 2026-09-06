# Investigation Prioritization Readiness Report

## Objective
The semantic ground truth in the current environment is insufficient for training a traditional supervised classifier. Therefore, the ML pipeline has been successfully re-architected to an unsupervised **Investigation Prioritization Model**.
This model determines the relative priority for independent human/analyst verification. It is strictly label-free. It does **not** predict causal probabilities, fire classifications, or semantic outcomes.

## Feature Policy & Anti-Bias Requirement
The model explicitly queries the `validate_features()` boundary.
- **Accepted**: Thermal metadata (FRP, counts, duration), temporal continuity (previous 30d events), contextual land cover, and generic distance to facilities.
- **Strictly Blocked**: `baseline_risk_score`, AI leakages, semantic heuristics.
- **Semantic Safeguard**: Proximity to a facility only increases *investigation priority* (warrants routing to an industrial analyst), it does not assert that the fire *is* industrial. 

## Model Architecture
- **Unsupervised Anomaly Method**: `sklearn.ensemble.IsolationForest` fitted on unlabeled historical V2 event features to measure statistical novelty.
- **Deterministic Baseline**: Transparent scaling formula prioritizing intense FRP, repeat behavior, and critical infrastructure proximity.
- **Hybrid Score**: The model blends the deterministic score with the Isolation Forest's anomaly score to produce a single `investigation_priority` metric.

## Ablation Results (`TT-EVT-00141704`)
An ablation study demonstrated how shifting the available features modifies the investigation ranking. 

| Ablation Group | Priority Score | Tier | Anomaly Score | Generated Factual Explanations |
| -------------- | -------------- | ---- | ------------- | ------------------------------ |
| **A** (Thermal) | 3.80 | LOW | -0.013 | 11 |
| **B** (+Temporal) | 20.74 | MEDIUM | -0.074 | 27 |
| **C** (+Env) | 21.26 | MEDIUM | -0.063 | 33 |
| **D** (+Infra) | 20.62 | MEDIUM | -0.076 | 47 |

*Note: The anomaly novelty scale shifts as dimensions are added, while the baseline score holds deterministic components. Group D yields the most comprehensive context.*

## Real-Event Example Payload (`TT-EVT-00141704`)
The pipeline runs on raw feature dictionaries and guarantees that no semantic or causal language escapes.

```json
{
  "event_id": "TT-EVT-00141704",
  "priority_score": 20.621930434174285,
  "priority_tier": "MEDIUM",
  "explanations": [
    {
      "explanation_type": "OBSERVATION",
      "feature_name": "max_frp_mw",
      "feature_value": 81.3,
      "description": "Maximum observed FRP was 81.3 MW."
    },
    {
      "explanation_type": "OBSERVATION",
      "feature_name": "events_previous_30d",
      "feature_value": 4,
      "description": "There were 4 prior thermal events in the preceding 30 days."
    }
  ],
  "diagnostics": {
    "baseline_score": 24.45,
    "anomaly_score": -0.076,
    "ablation_group": "D"
  }
}
```

## Limitations
- The Isolation Forest is fitted on a dynamically generated sample for demonstration. In production, the model would need to be fit continuously on historical rolling windows.
- **This is NOT a semantic classification.** The `priority_tier` merely dictates workflow routing.

## Final Status
**INVESTIGATION_PRIORITIZATION_READY**
