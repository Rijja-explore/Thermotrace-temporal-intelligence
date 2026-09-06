# ThermoTrace Integration Contract & Canonical Schemas

## Canonical Event Schema Contract

All five member workstreams communicate through the canonical schema defined in `schemas/Event.schema.json`.

```json
{
  "event_id": "string",
  "geometry": { "latitude": "number", "longitude": "number" },
  "time_window": { "start": "ISO-8601", "end": "ISO-8601" },
  "observations": [],
  "facility_context": {},
  "landcover_context": {},
  "satellite_context": {},
  "temporal_features": {},
  "classification": {
    "label": "string",
    "confidence": "number (0-1)",
    "probabilities": {},
    "top_evidence": [],
    "evidence_against": [],
    "model_version": "string"
  },
  "baseline": {},
  "deviation": {},
  "anomaly": { "anomaly_score": "number (0-100)", "is_abnormal": "boolean" },
  "industrial_likelihood": { "score": "number (0-100)" },
  "operational_risk": { "risk_score": "number (0-100)" },
  "evidence": { "evidence_for": [], "evidence_against": [], "missing_evidence": [] },
  "alert": { "should_alert": "boolean", "alert_type": "string", "priority": "string" },
  "analyst_review": { "reviewed": "boolean", "decision": "string", "notes": "string" },
  "status": "NEW | CONFIRMED | REJECTED | RECLASSIFIED",
  "data_version": "string",
  "model_version": "string",
  "engine_version": "string"
}
```

## Internal Module Interfaces

- **Member 1 (Data ETL):** Outputs `Event` objects with spatial geometries and landcover percentages.
- **Member 2 (AI Classification):** Receives 47-feature vector, returns `PredictionContract`.
- **Member 3 (Temporal Intelligence):** Receives observation sequence, returns `PipelineOutput`.
- **Member 4 (FastAPI Backend):** Serializes `PipelineOutput` & `PredictionContract` to React Frontend.
- **Member 5 (Historical Baselines):** Provides pre-computed facility baseline CSVs for offline lookup.
