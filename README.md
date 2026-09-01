# ThermoTrace – Temporal Intelligence Engine

**Person 3 Module: Temporal Intelligence · Facility Thermal Fingerprint · Anomaly Detection · Risk Engine**

> ⚠️ **Disclaimer**: All synthetic demo data in `examples/` is for functional testing only.  
> This engine does NOT claim scientific validation of its thresholds or weights.  
> FIRMS hotspot ≠ confirmed industrial incident. Facility proximity ≠ proof.  
> All scores are explainable and configurable — not black-box outputs.

---

## 1. Project Purpose

ThermoTrace Temporal Intelligence transforms raw satellite thermal observations (from NASA FIRMS or equivalent) into structured, explainable intelligence:

- **Which observations belong to the same thermal event?** (Event clustering)
- **Is the event persistent or episodic?** (Temporal features)
- **What is normal at this facility?** (Facility fingerprint + baseline)
- **Is current activity abnormal?** (Anomaly detection)
- **How likely is this to be industrial?** (Industrial likelihood scoring)
- **What is the operational risk?** (Risk engine)
- **What alert should be generated?** (Alert engine)
- **What evidence supports each conclusion?** (Evidence bundle)

This module is designed to be consumed by:
- **Person 2**: ML classification model (uses temporal features as input features)
- **Person 4**: API/Frontend platform (uses canonical JSON output)

---

## 2. Architecture

```
THERMAL OBSERVATIONS (Person 1)
        ↓
[1] VALIDATION         – schemas.py, clustering.py
        ↓
[2] EVENT CLUSTERING   – clustering.py (DBSCAN: spatial + temporal)
        ↓
[3] TEMPORAL FEATURES  – temporal_features.py (7d / 30d / 90d)
        ↓
[4] FACILITY FINGERPRINT – facility_fingerprint.py
        ↓
[5] BASELINE ENGINE    – baseline.py (pre-period only, no leakage)
        ↓
[6] DEVIATION          – baseline.py:compute_deviation()
        ↓
[7] ANOMALY DETECTION  – anomaly.py (z-score, MAD, multi-signal)
        ↓
[8] INDUSTRIAL LIKELIHOOD – industrial_likelihood.py (evidence-weighted)
        ↓
[9] OPERATIONAL RISK   – risk.py (weighted, graceful degradation)
        ↓
[10] ALERT ENGINE      – alerts.py
        ↓
[11] EVIDENCE BUNDLE   – evidence.py
        ↓
[12] CANONICAL OUTPUT  → Person 2 / Person 4
```

---

## 3. Module Responsibilities

| Module | Responsibility |
|---|---|
| `schemas.py` | All Pydantic input/output data models |
| `config_loader.py` | Load `thresholds.yaml` + `weights.yaml` |
| `clustering.py` | DBSCAN clustering on spatial + temporal distance |
| `temporal_features.py` | Feature extraction: 7d/30d/90d windows |
| `facility_fingerprint.py` | Historical facility behaviour summary |
| `baseline.py` | Pre-period baseline stats + deviation calculation |
| `anomaly.py` | Multi-signal anomaly scoring with reasons |
| `industrial_likelihood.py` | Evidence-weighted industrial likelihood |
| `risk.py` | Operational risk with graceful degradation |
| `alerts.py` | Alert type/priority generation |
| `evidence.py` | Evidence assembler + Person 2 feature interface |
| `pipeline.py` | Canonical 12-step pipeline orchestrator |

---

## 4. Installation

```bash
# Clone repository
cd thermotrace-temporal-intelligence

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

**Requirements**: Python 3.11+

---

## 5. Input Schema

The module accepts normalised observations from Person 1:

```json
{
  "observation_id": "OBS-001",
  "latitude": 19.123,
  "longitude": 73.456,
  "timestamp_utc": "2026-01-15T12:30:00Z",
  "frp": 85.4,
  "confidence": 92,
  "satellite": "VIIRS",
  "sensor": "VIIRS",
  "source": "NASA_FIRMS",
  "facility_id": "FAC-001",
  "facility_type": "refinery",
  "facility_distance_km": 0.42,
  "landcover_class": "industrial"
}
```

**Required fields**: `observation_id`, `latitude`, `longitude`, `timestamp_utc`

**All other fields are optional.** Missing fields are handled gracefully with explicit `missing_evidence` flags in the output.

### Graceful handling of:
- Missing `facility_id` → industrial likelihood uses proximity = missing evidence
- Missing `confidence` → risk uses neutral default
- Missing `landcover` → industrial likelihood uses neutral score
- Missing `frp` → anomaly signals degraded, explicitly noted
- Duplicate `observation_id` → first instance kept, duplicates rejected
- Invalid timestamps → observation rejected with reason logged
- Sparse observations → baseline marked as `insufficient` / `poor`

---

## 6. Output Schema

See `docs/API_OUTPUT_CONTRACT.md` for the complete field reference.

Top-level structure:

```json
{
  "event_id": "TT-EVENT-XXXXXXXX",
  "location": { "latitude": 19.123, "longitude": 73.456 },
  "time_window": { "start": "...", "end": "..." },
  "temporal_features": { "window_7d": {...}, "window_30d": {...}, "window_90d": {...} },
  "facility": { "facility_id": "FAC-001", "facility_type": "refinery", "distance_km": 0.42 },
  "baseline": { "available": true, "frp_mean": 40.0, "history_quality": "good" },
  "deviation": { "frp_deviation_percent": 112.5 },
  "anomaly": { "score": 78, "level": "abnormal", "reasons": [...] },
  "industrial_likelihood": { "score": 85, "requires_verification": false, "evidence_for": [...] },
  "operational_risk": { "risk_score": 68, "risk_level": "high", "score_confidence": "partial" },
  "alert": { "alert_type": "ABNORMAL_INCREASE", "priority": "HIGH" },
  "evidence": { "evidence_for": [...], "evidence_against": [...], "missing_evidence": [...] },
  "recommendation": "Prioritise analyst verification...",
  "metadata": { "engine_version": "temporal-v1", "config_version": "v1" }
}
```

---

## 7. Running the Demo

```bash
python scripts/run_demo.py
```

Four synthetic scenarios are run:
1. **Persistent Industrial** – stable, normal facility activity
2. **Abnormal Industrial** – facility with sudden FRP spike
3. **Natural/Forest Fire** – no facility, forest land cover
4. **Insufficient History** – sparse observations, explicit uncertainty

> All demo data is synthetic and labelled as such. Do not interpret demo outputs as validated real-world results.

---

## 8. Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=thermotrace_temporal --cov-report=term-missing
```

---

## 9. Configuration

All thresholds and weights are externalized in `config/`:

### `config/thresholds.yaml`
Controls:
- Clustering: `spatial_radius_km`, `temporal_window_hours`, `min_samples`
- Anomaly levels: `normal_max`, `watch_max`, `abnormal_max`
- Baseline quality: `min_observations_for_baseline`, `min_days_for_good_baseline`
- Risk levels: `low_max`, `medium_max`, `high_max`
- Proximity bands: `very_close_km`, `close_km`, `moderate_km`

### `config/weights.yaml`
Controls:
- Industrial likelihood component weights (must sum to 1.0)
- Operational risk component weights (must sum to 1.0)
- Anomaly signal weights (must sum to 1.0)

> ⚠️ These are **starting-point values** and must be empirically tuned using labelled ground-truth data before operational use.

---

## 10. Feature Definitions

See `docs/FEATURE_CONTRACT.md` for the complete Person 2 ML feature interface.

### Key feature categories:

**Persistence**
- `persistence_ratio_{7d,30d,90d}` – fraction of monitored days with at least one detection
- `active_days_{7d,30d,90d}` – count of days with detection activity

**FRP Statistics** (30-day primary window)
- `frp_mean_30d`, `frp_median_30d`, `frp_max_30d`, `frp_min_30d`, `frp_std_30d`
- `frp_p90_30d`, `frp_p95_30d`

**Spatial Stability**
- `spatial_extent_km_30d` – max pairwise distance between detections
- `spatial_stability_score_30d` – normalised stability (0–100)

**Baseline Deviation**
- `baseline_frp_mean` – historical FRP mean
- `baseline_detection_frequency` – historical detection rate

**Anomaly**
- `anomaly_score` – composite anomaly score (0–100)
- `anomaly_level_encoded` – ordinal encoding (0=normal, 1=watch, 2=abnormal, 3=severe)

**Industrial Likelihood**
- `industrial_likelihood_score` – evidence-weighted score (0–100)
- `il_facility_proximity_score`, `il_persistence_score`, etc.

---

## 11. Scoring Methodology

### Event Clustering
DBSCAN with a combined spatial + temporal distance metric. Two observations are considered "close" only if **both** spatial distance ≤ `spatial_radius_km` **and** temporal gap ≤ `temporal_window_hours`. This prevents same-location but months-apart observations from being clustered together.

### Anomaly Detection
Five signals, each contributing a 0–100 score:
1. **FRP intensity deviation** – z-score and robust z-score vs historical
2. **Frequency deviation** – % change vs baseline detection rate
3. **Persistence change** – active day ratio change vs baseline
4. **Spatial change** – spatial extent change vs baseline
5. **Duration change** – event duration vs threshold

A configurable weighted sum yields the final score.

### Industrial Likelihood
Six evidence components (weights in `config/weights.yaml`):
- Facility proximity (30%)
- Persistence/recurrence (25%)
- Land-cover context (15%)
- Spatial stability (15%)
- Temporal pattern (10%)
- Multi-sensor corroboration (5%)

### Operational Risk
Five components with graceful degradation when population or environmental sensitivity layers are missing. Missing components are explicitly listed in `missing_components` and the `score_confidence` field reflects completeness.

---

## 12. Limitations

1. **Thresholds are not scientifically validated.** All configuration values are starting points that require empirical tuning.
2. **Baseline requires sufficient history.** With fewer than 5 observations before the current period, the baseline is marked `insufficient` and anomaly detection is unavailable.
3. **Population and environmental sensitivity layers are optional.** When absent, risk scores are marked `partial` or `minimal`.
4. **No deep learning.** Anomaly detection is statistical (z-score, MAD). This is intentional for explainability, but limits sensitivity for complex patterns.
5. **DBSCAN O(n²) distance matrix.** For very large datasets (>10,000 observations), consider using BallTree spatial indexing.
6. **No satellite imagery ingestion.** The engine processes metadata only; it does not directly analyse imagery.
7. **Industrial likelihood ≠ classification.** This module provides evidence scores, not a confirmed classification.

---

## 13. Integration with Person 2

Person 2's ML classifier can consume temporal intelligence features via:

```python
from thermotrace_temporal.evidence import get_temporal_features

features = get_temporal_features(
    temporal_features=result.temporal_features,
    anomaly_result=result.anomaly,
    industrial_likelihood=result.industrial_likelihood,
    baseline=result.baseline,
    facility_distance_km=0.42,
    landcover_class="industrial",
)
# Returns: dict[str, float | None]
```

See `docs/FEATURE_CONTRACT.md` for the complete feature list.

---

## 14. Integration with Person 4

Person 4's API/frontend can consume the canonical output via:

```python
from thermotrace_temporal.pipeline import analyze_event

result = analyze_event(
    observations=list_of_observation_dicts,
    historical_observations=historical_dicts,
    current_period_start=datetime(2026, 1, 15),
    population_proximity_score=70.0,  # optional
    environmental_sensitivity_score=50.0,  # optional
)
# result is a fully JSON-serialisable dict
```

See `docs/API_OUTPUT_CONTRACT.md` for the complete field reference.

For a future FastAPI service, the pipeline function is designed to be wrapped in a single endpoint:

```python
@app.post("/api/v1/analyze")
async def analyze(payload: AnalysisRequest) -> dict:
    return analyze_event(**payload.dict())
```

---

## 15. Example Output

```json
{
  "event_id": "TT-EVENT-A1B2C3D4",
  "location": { "latitude": 19.123, "longitude": 73.456 },
  "time_window": { "start": "2026-01-10T08:00:00", "end": "2026-01-16T08:25:00" },
  "temporal_features": {
    "window_30d": {
      "detection_count": 7,
      "active_days": 7,
      "persistence_ratio": 0.2333,
      "frp_mean": 41.66,
      "frp_max": 45.1,
      "spatial_stability_score": 99.9
    }
  },
  "facility": { "facility_id": "FAC-001", "facility_type": "refinery", "distance_km": 0.4 },
  "baseline": { "available": true, "frp_mean": 41.0, "history_quality": "good" },
  "deviation": { "frp_deviation_percent": 1.6 },
  "anomaly": { "score": 0.0, "level": "normal", "reasons": ["Current activity is within historical norms."] },
  "industrial_likelihood": { "score": 78.5, "requires_verification": false },
  "operational_risk": { "risk_score": 31.4, "risk_level": "medium", "score_confidence": "minimal" },
  "alert": { "alert_type": "PERSISTENT_SOURCE", "priority": "LOW", "status": "NEW" },
  "recommendation": "Continue monitoring. Current activity is consistent with historical facility behaviour.",
  "metadata": { "engine_version": "temporal-v1", "config_version": "v1" }
}
```
