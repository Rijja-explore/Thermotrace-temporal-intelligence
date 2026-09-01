# ThermoTrace Temporal Intelligence – ML Feature Contract

**For Person 2: ML Classification Model**

Version: v1 | Engine: temporal-v1

---

## Overview

This document defines the stable feature interface that the Temporal Intelligence Engine (Person 3) exposes for use by Person 2's ML classifier.

Features are extracted by calling:

```python
from thermotrace_temporal.evidence import get_temporal_features

features = get_temporal_features(
    temporal_features=...,   # TemporalFeatures object
    anomaly_result=...,      # AnomalyResult object
    industrial_likelihood=..., # IndustrialLikelihood object
    baseline=...,            # Baseline object
    facility_distance_km=..., # float | None
    landcover_class=...,     # str | None
)
# Returns: dict[str, float | None]
```

All features are `float` or `None`. `None` indicates the feature is unavailable for this observation/event. Person 2's model should handle `None` values (e.g., via imputation or masking).

---

## Feature Definitions

### Persistence Features

| Feature Name | Type | Description |
|---|---|---|
| `persistence_ratio_7d` | float [0,1] | Fraction of last 7 monitored days with ≥1 detection |
| `persistence_ratio_30d` | float [0,1] | Fraction of last 30 monitored days with ≥1 detection |
| `persistence_ratio_90d` | float [0,1] | Fraction of last 90 monitored days with ≥1 detection |
| `active_days_7d` | int | Count of unique active days in last 7 days |
| `active_days_30d` | int | Count of unique active days in last 30 days |
| `active_days_90d` | int | Count of unique active days in last 90 days |

**Interpretation**: Industrial continuous sources typically show high persistence ratios (0.6+). Episodic natural fires typically show low persistence. A single event shows 0 after it ends.

---

### Duration Features

| Feature Name | Type | Description |
|---|---|---|
| `duration_hours_7d` | float | Total span (start to end) of detections in 7d window (hours) |
| `duration_hours_30d` | float | Total span in 30d window (hours) |
| `duration_hours_90d` | float | Total span in 90d window (hours) |

---

### FRP Statistics (Fire Radiative Power, MW)

Primary window: 30 days. Additional means for cross-window comparison.

| Feature Name | Type | Description |
|---|---|---|
| `frp_mean_7d` | float | Mean FRP in 7d window (MW) |
| `frp_mean_30d` | float | Mean FRP in 30d window (MW) |
| `frp_mean_90d` | float | Mean FRP in 90d window (MW) |
| `frp_median_30d` | float | Median FRP in 30d window (MW) |
| `frp_max_30d` | float | Maximum FRP in 30d window (MW) |
| `frp_min_30d` | float | Minimum FRP in 30d window (MW) |
| `frp_std_30d` | float | Standard deviation of FRP in 30d window |
| `frp_p90_30d` | float | 90th percentile FRP in 30d window (MW) |
| `frp_p95_30d` | float | 95th percentile FRP in 30d window (MW) |

**Note**: FRP = None if the satellite sensor did not report power for this detection. Do not treat None as zero.

---

### Spatial Stability Features

| Feature Name | Type | Description |
|---|---|---|
| `spatial_extent_km_30d` | float | Max pairwise distance between detections in 30d window (km) |
| `spatial_stability_score_30d` | float [0,100] | Normalised spatial stability; 100 = perfectly stationary; 0 = highly mobile |

**Interpretation**: Industrial point sources (e.g. flare stacks) tend to be spatially stable (score > 80). Moving or spreading fires score low (<30).

---

### Detection Frequency Features

| Feature Name | Type | Description |
|---|---|---|
| `detection_frequency_7d` | float | Detections per day in 7d window |
| `detection_frequency_30d` | float | Detections per day in 30d window |
| `detection_frequency_90d` | float | Detections per day in 90d window |
| `days_since_last_detection` | float | Days elapsed between analysis_end and most recent detection |

---

### Baseline Deviation Features

| Feature Name | Type | Description |
|---|---|---|
| `baseline_frp_mean` | float | Historical FRP mean (MW) from pre-period baseline |
| `baseline_frp_std` | float | Historical FRP standard deviation |
| `baseline_detection_frequency` | float | Historical detections per day |
| `baseline_available` | float [0,1] | 1.0 if baseline exists; 0.0 if insufficient history |

---

### Anomaly Features

| Feature Name | Type | Description |
|---|---|---|
| `anomaly_score` | float [0,100] | Composite anomaly score; 0 = normal, 100 = extreme anomaly |
| `anomaly_level_encoded` | float | Ordinal: normal=0, watch=1, abnormal=2, severe=3, unknown=-1 |

---

### Industrial Likelihood Component Features

These are the component sub-scores from the evidence engine, useful as individual ML features:

| Feature Name | Type | Description |
|---|---|---|
| `industrial_likelihood_score` | float [0,100] | Overall evidence-weighted industrial likelihood |
| `il_facility_proximity_score` | float [0,100] | Proximity to known industrial facility |
| `il_persistence_score` | float [0,100] | Recurrence/persistence component |
| `il_landcover_score` | float [0,100] | Land-cover context component |
| `il_spatial_stability_score` | float [0,100] | Spatial stability component |
| `il_temporal_score` | float [0,100] | Temporal pattern component |
| `il_sensor_agreement_score` | float [0,100] | Multi-sensor corroboration |

---

### Facility Proximity Features

| Feature Name | Type | Description |
|---|---|---|
| `facility_distance_km` | float | Distance from nearest known industrial facility (km) |

---

### Land Cover Features

| Feature Name | Type | Description |
|---|---|---|
| `landcover_class_encoded` | float [0,1] | 1.0 = industrial; 0.0 = natural; 0.5 = ambiguous/unknown; None = missing |

---

### Day/Night Distribution

| Feature Name | Type | Description |
|---|---|---|
| `day_detection_ratio_30d` | float [0,1] | Fraction of 30d detections occurring during daytime (06–18 UTC) |
| `night_detection_ratio_30d` | float [0,1] | Fraction occurring during night |
| `weekend_detection_ratio_30d` | float [0,1] | Fraction on weekends (Sat/Sun) |

---

## Important Caveats for Person 2

1. **These features do NOT constitute ground truth.** They are statistical summaries of satellite detections that must be combined with Person 2's own training data and validation methodology.

2. **`industrial_likelihood_score` is NOT a classification output.** It is an evidence accumulation score from transparent rules. Person 2 should treat it as one input feature, not as a label.

3. **Baseline features may be None** when historical data is insufficient. Person 2's model must handle this gracefully (e.g., separate imputation branch or missingness indicator feature).

4. **FRP values may be None** for low-quality or missing satellite observations. Never impute FRP as zero.

5. **Feature stability**: Feature names in this contract are stable in v1. Any additions will be backward-compatible (new keys only). Removals will be versioned.

---

## Example Feature Dictionary

```python
{
    "persistence_ratio_7d": 0.2857,
    "persistence_ratio_30d": 0.2333,
    "persistence_ratio_90d": 0.0778,
    "active_days_7d": 2,
    "active_days_30d": 7,
    "active_days_90d": 7,
    "frp_mean_30d": 41.66,
    "frp_median_30d": 41.2,
    "frp_max_30d": 45.1,
    "frp_std_30d": 2.3,
    "frp_p90_30d": 44.3,
    "spatial_stability_score_30d": 99.9,
    "spatial_extent_km_30d": 0.21,
    "anomaly_score": 0.0,
    "anomaly_level_encoded": 0.0,
    "industrial_likelihood_score": 78.5,
    "il_facility_proximity_score": 100.0,
    "il_persistence_score": 72.1,
    "il_landcover_score": 100.0,
    "facility_distance_km": 0.42,
    "landcover_class_encoded": 1.0,
    "baseline_available": 1.0,
    "baseline_frp_mean": 41.0
}
```
