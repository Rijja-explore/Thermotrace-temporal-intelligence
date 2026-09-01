# ThermoTrace Temporal Intelligence – API Output Contract

**For Person 4: Backend / FastAPI Platform & Frontend UI**

Version: v1 | Engine: temporal-v1

---

## 1. Overview

This document specifies the exact JSON response format produced by the Temporal Intelligence Engine (`pipeline.py`).

Person 4 can consume this contract directly in:
1. **FastAPI Endpoints**: Return `result` directly as a JSON response body.
2. **Frontend UI Components**: Map fields directly to UI cards (Fingerprint, Timeline, Anomaly, Risk, Evidence, Alert).

---

## 2. Canonical JSON Schema Reference

```json
{
  "event_id": "TT-EVENT-A1B2C3D4",

  "location": {
    "latitude": 19.123,
    "longitude": 73.456
  },

  "time_window": {
    "start": "2026-01-10T08:00:00",
    "end": "2026-01-16T08:25:00"
  },

  "temporal_features": {
    "window_7d": {
      "window_days": 7,
      "window_label": "7d",
      "start": "2026-01-09T08:25:00",
      "end": "2026-01-16T08:25:00",
      "detection_count": 7,
      "active_days": 7,
      "monitored_days": 7,
      "persistence_ratio": 1.0,
      "duration_hours_total": 144.17,
      "frp_mean": 41.66,
      "frp_median": 41.2,
      "frp_max": 45.1,
      "frp_min": 38.7,
      "frp_std": 2.27,
      "frp_p90": 44.22,
      "frp_p95": 44.66,
      "spatial_extent_km": 0.21,
      "spatial_stability_score": 99.9,
      "detection_frequency": 1.0,
      "days_since_last_detection": 0.0,
      "day_count": 7,
      "night_count": 0,
      "hour_distribution": {"7": 2, "8": 5},
      "weekday_count": 5,
      "weekend_count": 2,
      "sensor_distribution": {"VIIRS": 5, "MODIS": 2}
    },
    "window_30d": { "...": "Same schema as 7d" },
    "window_90d": { "...": "Same schema as 7d" }
  },

  "facility": {
    "facility_id": "FAC-001",
    "facility_type": "refinery",
    "distance_km": 0.42
  },

  "baseline": {
    "available": true,
    "facility_id": "FAC-001",
    "baseline_period_start": "2025-10-01T08:00:00",
    "baseline_period_end": "2026-01-09T08:00:00",
    "frp_mean": 41.0,
    "frp_median": 40.8,
    "frp_std": 2.1,
    "frp_upper_quantile": 44.5,
    "frp_lower_quantile": 38.0,
    "detection_frequency": 0.45,
    "active_days_ratio": 0.45,
    "history_count": 45,
    "history_quality": "good",
    "notes": []
  },

  "deviation": {
    "frp_deviation": 0.66,
    "frp_deviation_percent": 1.61,
    "frequency_deviation": 0.55,
    "frequency_deviation_percent": 122.2,
    "active_day_deviation": 0.55,
    "spatial_deviation": 0.05,
    "notes": []
  },

  "anomaly": {
    "score": 0.0,
    "level": "normal",
    "reasons": [
      "Current activity is within historical norms."
    ],
    "component_scores": {
      "frp_deviation": 0.0,
      "frequency_deviation": 0.0,
      "persistence_change": 0.0,
      "spatial_change": 0.0,
      "duration_change": 0.0
    },
    "data_quality_notes": []
  },

  "industrial_likelihood": {
    "score": 78.5,
    "requires_verification": false,
    "component_scores": {
      "facility_proximity": 100.0,
      "persistence": 72.1,
      "landcover": 100.0,
      "spatial_stability": 99.9,
      "temporal": 65.0,
      "sensor_agreement": 100.0
    },
    "evidence_for": [
      "Detection is 0.42 km from a known industrial facility (type: refinery).",
      "Industrial land-cover context: 'industrial'.",
      "High spatial stability score (100/100)."
    ],
    "evidence_against": [],
    "missing_evidence": []
  },

  "operational_risk": {
    "risk_score": 31.4,
    "risk_level": "medium",
    "score_confidence": "minimal",
    "available_components": [
      "thermal_intensity",
      "anomaly_persistence",
      "classification_confidence"
    ],
    "missing_components": [
      "population_proximity",
      "environmental_sensitivity"
    ],
    "component_contributions": {
      "thermal_intensity": 35.0,
      "anomaly_persistence": 0.0,
      "population_proximity": 0.0,
      "environmental_sensitivity": 0.0,
      "classification_confidence": 88.0
    },
    "notes": [
      "Population proximity layer unavailable – score is partial."
    ]
  },

  "alert": {
    "alert_id": "TT-ALERT-9F8E7D6C",
    "alert_type": "PERSISTENT_SOURCE",
    "priority": "LOW",
    "reason": "Activity is within historical norms.",
    "status": "NEW"
  },

  "evidence": {
    "evidence_for": [
      "Detection is 0.42 km from a known industrial facility.",
      "7 thermal detections in the 30-day analysis window.",
      "Mean FRP = 41.7 MW in 30-day window."
    ],
    "evidence_against": [],
    "missing_evidence": [
      "[Risk] Population proximity layer unavailable – score is partial."
    ]
  },

  "recommendation": "Continue monitoring. Current activity is consistent with historical facility behaviour.",

  "metadata": {
    "engine_version": "temporal-v1",
    "config_version": "v1",
    "analysis_timestamp": "2026-09-01T22:30:00Z",
    "input_count": "7",
    "valid_count": "7",
    "rejected_count": "0",
    "cluster_count": "1"
  }
}
```

---

## 3. UI Component Mapping for Person 4

Below is how the UI components map to fields in the canonical output:

### 1. FACILITY THERMAL FINGERPRINT CARD
- **Current FRP**: `temporal_features.window_30d.frp_mean`
- **Historical FRP**: `baseline.frp_mean`
- **Baseline Range**: `baseline.frp_lower_quantile` to `baseline.frp_upper_quantile`
- **Deviation %**: `deviation.frp_deviation_percent`
- **History Quality**: `baseline.history_quality` (`good`, `moderate`, `poor`, `insufficient`)

### 2. TIMELINE COMPONENT
- Render using `temporal_features.window_30d` and `temporal_features.window_7d`
- **Detection Count**: `detection_count`
- **Active Days**: `active_days`
- **FRP Mean**: `frp_mean`
- **Baseline Mean**: `baseline.frp_mean`

### 3. ANOMALY CARD
- **Score**: `anomaly.score` (0–100)
- **Level**: `anomaly.level` (`normal`, `watch`, `abnormal`, `severe`, `unknown`)
- **Reasons**: `anomaly.reasons` (array of bullet points)

### 4. RISK & INDUSTRIAL LIKELIHOOD CARD
- **Industrial Likelihood Score**: `industrial_likelihood.score` (0–100)
- **Requires Verification Flag**: `industrial_likelihood.requires_verification` (boolean)
- **Operational Risk Score**: `operational_risk.risk_score` (0–100)
- **Risk Level**: `operational_risk.risk_level` (`low`, `medium`, `high`, `critical`)
- **Score Confidence**: `operational_risk.score_confidence` (`full`, `partial`, `minimal`)
- **Component Contributions**: `operational_risk.component_contributions`

### 5. EVIDENCE PANEL
- **Evidence For**: `evidence.evidence_for` (green checkmarks)
- **Evidence Against**: `evidence.evidence_against` (red X marks)
- **Missing Evidence**: `evidence.missing_evidence` (yellow question marks)

### 6. ALERT CARD
- **Type**: `alert.alert_type` (`NEW_INDUSTRIAL_EVENT`, `PERSISTENT_SOURCE`, `ABNORMAL_INCREASE`, `HIGH_OPERATIONAL_RISK`, `UNKNOWN_REQUIRES_VERIFICATION`, `NONE`)
- **Priority**: `alert.priority` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, `NONE`)
- **Reason**: `alert.reason`
- **Recommended Action**: `recommendation`

---

## 4. FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from thermotrace_temporal.pipeline import analyze_event

app = FastAPI(title="ThermoTrace Temporal Intelligence API")

class ObservationInput(BaseModel):
    observation_id: str
    latitude: float
    longitude: float
    timestamp_utc: str
    frp: Optional[float] = None
    confidence: Optional[float] = None
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    source: Optional[str] = None
    facility_id: Optional[str] = None
    facility_type: Optional[str] = None
    facility_distance_km: Optional[float] = None
    landcover_class: Optional[str] = None

class AnalysisRequest(BaseModel):
    observations: List[ObservationInput]
    historical_observations: Optional[List[ObservationInput]] = None
    population_proximity_score: Optional[float] = None
    environmental_sensitivity_score: Optional[float] = None

@app.post("/api/v1/temporal/analyze")
async def analyze_temporal_event(payload: AnalysisRequest):
    try:
        raw_obs = [obs.dict() for obs in payload.observations]
        raw_hist = [obs.dict() for obs in payload.historical_observations] if payload.historical_observations else None
        
        result = analyze_event(
            observations=raw_obs,
            historical_observations=raw_hist,
            population_proximity_score=payload.population_proximity_score,
            environmental_sensitivity_score=payload.environmental_sensitivity_score,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```
