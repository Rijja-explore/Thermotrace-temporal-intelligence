# Person 2 -> Person 4 Integration Handoff

## Current Status
**INFERENCE_BOUNDARY_SECURE**

## 1. Canonical JSON Schema & Field Definitions

### Event Identity/Context
* `event_id`: Unique string identifying the temporal cluster.

### Prediction State
* `prediction_status`: Enum representing the model status (e.g., `MODEL_NOT_TRAINED_NO_VERIFIED_LABELS`).
* `predicted_label`: Semantic class prediction. Defaults to `unknown_requires_verification` until a trained model operates.
* `verification_state`: Enum detailing workflow requirements (`MODEL_NOT_AVAILABLE`, `MODEL_PREDICTION_REQUIRES_VERIFICATION`, `INSUFFICIENT_EVIDENCE`, `VERIFIED`).
* `model_version`: String (`UNTRAINED` or future version hash).
* `prediction_timestamp`: String ISO time.

### Confidence Separation (CRITICAL)
**DO NOT collapse these into a single generic "confidence" frontend field!**
* `model_confidence` (Float or Null): Probability confidence generated ONLY by a trained, validated ML model.
* `evidence_confidence` (Float or Null): Human/Reviewer reliability score appended to independent evidence.
* `data_quality` (Enum): Objective quality of the underlying FIRMS satellite telemetry (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`).

### Class Probabilities
* `class_probabilities` (Dictionary): Probability mapping for all semantic classes. Currently defaults to `{}`. Do NOT fabricate 0.0 values when untrained.

### Explainability: Observations vs Semantic Evidence
* `explanations` (Array of `ExplanationRecord`): Strict, deterministic factual observations derived from operational metadata (e.g., `Maximum observed FRP was 42.7 MW`). They are strictly categorized as `ExplanationType.OBSERVATION` and contain **NO causal language**.
* `evidence` (Array of `EvidenceRecord`): Independently validated external claims (e.g., News articles, High-Res satellite confirmation). Currently defaults to `[]`. FIRMS recurrence/land cover data **does not belong here**.

## 2. Frontend & Backend Rendering Guidance (EXPLICIT "DO NOT" RULES)
- **DO NOT** interpret `data_quality` as model prediction confidence.
- **DO NOT** interpret `evidence_confidence` as classifier confidence.
- **DO NOT** display observations (like FRP or OSM proximity) as semantic "proof" or causal conclusions.
- **DO NOT** assume `class_probabilities` always exist; handle empty sets gracefully.
- **DO NOT** convert `MODEL_NOT_AVAILABLE` into a generic `UNKNOWN` without preserving the distinction that the system literally lacks a model.
- **DO NOT** assume a prediction label always exists (handle `unknown_requires_verification`).
- **DO NOT** treat an empty `evidence` array as evidence of absence.
- **DO NOT** display synthetic `baseline_risk_*` values as classification evidence (they are strictly blocked by the ML pipeline).
- **DO NOT** assume a FIRMS detection itself is a semantic fire label (it is only a thermal anomaly).

## 3. Current System State (Example Payload)
When the backend calls `adapt_inference_event(event_dict)`, the serialized output is strictly factual and lacks fabricated confidences:
```json
{
  "event_id": "TT-EVT-00141704",
  "prediction_status": "MODEL_NOT_TRAINED_NO_VERIFIED_LABELS",
  "predicted_label": "unknown_requires_verification",
  "model_confidence": null,
  "evidence_confidence": null,
  "data_quality": "UNKNOWN",
  "class_probabilities": {},
  "evidence": [],
  "explanations": [
    {
      "explanation_type": "OBSERVATION",
      "feature_name": "max_frp_mw",
      "feature_value": 81.3,
      "unit": "MW",
      "direction": null,
      "importance": null,
      "source": "FIRMS/OSM derived feature",
      "description": "Maximum observed FRP was 81.3 MW."
    }
  ],
  "model_version": "UNTRAINED",
  "prediction_timestamp": "N/A",
  "verification_state": "MODEL_NOT_AVAILABLE"
}
```

## 4. Future API Response (Trained State Schema)
*(ILLUSTRATIVE ONLY. NOT REAL PROJECT OUTPUT. NO TRAINED MODEL EXISTS.)*
```json
{
  "event_id": "TT-EVT-00141704",
  "prediction_status": "PREDICTION_AVAILABLE",
  "predicted_label": "persistent_industrial_source",
  "model_confidence": 0.89,
  "evidence_confidence": 0.95,
  "data_quality": "HIGH",
  "class_probabilities": {
    "persistent_industrial_source": 0.89,
    "unknown_requires_verification": 0.11
  },
  "evidence": [
    {
      "source_type": "independent_imagery",
      "source_url": "https://example.com/stac",
      "source_name": "Sentinel-2 L2A",
      "event_time": "2025-12-08T00:00:00",
      "independently_verified": true
    }
  ],
  "explanations": [
    {
      "explanation_type": "MODEL_EXPLANATION",
      "feature_name": "events_previous_90d",
      "feature_value": 4,
      "importance": 0.34,
      "source": "SHAP_TreeExplainer",
      "description": "High historical recurrence strongly influenced prediction."
    }
  ],
  "model_version": "v1.0.0-rf-thermal-temporal",
  "prediction_timestamp": "2026-09-03T12:00:00Z",
  "verification_state": "MODEL_PREDICTION_REQUIRES_VERIFICATION"
}
```
