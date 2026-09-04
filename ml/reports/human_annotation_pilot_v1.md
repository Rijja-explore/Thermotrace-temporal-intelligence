# Human Annotation Pilot Report (v1.0) — Person 2 AI/ML

## 1. Pilot Dataset Summary
- **Total Pilot Size**: 150 events (`ml/data/ground_truth/human_verified/pilot/pilot_records_150.json`)
- **Double-Annotation Subset**: **100 events** (Assigned independently to Annotator 1 and Annotator 2)
- **Single-Annotation Subset**: **50 events** (Assigned to Annotator 1)
- **Sampling Method**: Deterministic stratified sampling from `candidate_pool_v1.json` using random seed 42.

---

## 2. Evidence Fields Provided to Annotators
Each assigned event exposes standard evidence across 4 structured categories:
- **EVENT IDENTIFICATION**: `event_id`, `centroid_lat`, `centroid_lon`, `start_time`
- **THERMAL**: `max_frp_mw`, `mean_frp_mw`, `sum_frp_mw`, `spatial_extent_km`, `duration_hours`, `detection_count`
- **TEMPORAL**: `events_previous_7d`, `events_previous_30d`, `events_previous_90d`, `active_days_previous_30d`, `time_since_previous_event_hours`
- **LAND COVER**: `forest_fraction_1km`, `cropland_fraction_1km`, `builtup_fraction_1km`, `grassland_fraction_1km`, `natural_land_fraction`
- **INFRASTRUCTURE**: `distance_to_facility_km`, `distance_to_power_line_km`, `near_refinery`, `near_factory`, `near_mine`, `near_quarry`

*(Note: Zero model predictions, rule labels, or pre-populated classes are exposed in the annotator interface).*

---

## 3. Human Annotation Protocols & Unknown Policy

### Taxonomy (6 Classes)
1. `persistent_industrial_source`
2. `industrial_fire_or_abnormal_event`
3. `wildfire_or_forest_fire`
4. `agricultural_burning`
5. `mining_or_other_industrial_activity`
6. `unknown_requires_verification`

### Confidence Scale
- **`HIGH`**: Multiple independent evidence categories support the same class without contradiction.
- **`MEDIUM`**: Evidence strongly favors one class, but minor ambiguity remains.
- **`LOW`**: Weak, sparse, or conflicting evidence.

### Prominent Unknown Policy
Annotators are instructed to assign `unknown_requires_verification` whenever evidence is sparse, contradictory, or insufficient to prove a semantic class. Annotators are never pressured to choose a semantic class.

---

## 4. Current Status Declaration
**Human annotation has not yet been completed.**

*(No fabricated agreement, Cohen's kappa, class counts, or accuracy numbers are reported prior to human review completion).*
