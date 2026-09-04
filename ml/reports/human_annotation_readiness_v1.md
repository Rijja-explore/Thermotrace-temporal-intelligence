# Human Annotation Readiness Report (v1.0) — Person 2 AI/ML

## 1. Current Annotation Status
- **Human-Verified Ground Truth**: **0 events** (Human-verified ground truth currently contains 0 events).
- **Mock Ground Truth**: **100 events** (*The 100-event mock ground truth remains an engineering benchmark and must not be treated as human-verified truth*).
- **Candidate Pool**: **1,500 events** (`ml/data/ground_truth/candidate_pool_v1.json`).

---

## 2. Taxonomy & Evidence Categories
Annotators will evaluate events using the 6-class taxonomy:
1. `persistent_industrial_source`
2. `industrial_fire_or_abnormal_event`
3. `wildfire_or_forest_fire`
4. `agricultural_burning`
5. `mining_or_other_industrial_activity`
6. `unknown_requires_verification`

Evidence available to annotators spans 4 structured categories:
- **THERMAL**: `max_frp_mw`, `mean_frp_mw`, `sum_frp_mw`, `spatial_extent_km`, `duration_hours`, `detection_count`.
- **TEMPORAL**: `events_previous_7d`, `events_previous_30d`, `events_previous_90d`, `active_days_previous_30d`, `time_since_previous_event_hours`.
- **LAND COVER**: `forest_fraction_1km`, `cropland_fraction_1km`, `builtup_fraction_1km`, `grassland_fraction_1km`, `natural_land_fraction`.
- **INFRASTRUCTURE**: `distance_to_facility_km`, `distance_to_power_line_km`, `near_refinery`, `near_factory`, `near_mine`, `near_quarry`. *(Facility proximity is supporting evidence only and must never be treated as proof of class membership)*.

---

## 3. Annotation Workflow & Protocols

### Confidence Scale
- **`HIGH`**: Multiple independent evidence categories support the class without contradiction.
- **`MEDIUM`**: Evidence strongly favors one class, but minor ambiguity exists.
- **`LOW`**: Weak or sparse evidence. Annotators should strongly consider `unknown_requires_verification`.

### Double-Annotation Protocol
- **Initial Batch**: 150–300 candidates assigned independently to 2 annotators.
- **Metrics Calculated**: Raw agreement, Cohen's Kappa, inter-annotator confusion matrices via `ml/src/classification/annotation_quality.py`.

### Adjudication Protocol
- Disagreements trigger an immutable adjudication queue (`adjudication_required`), preserving Annotator A and B records separately while a senior reviewer assigns `adjudicated_label` and `adjudication_reason`.

### Leakage Controls
- Mock labels (`mock_remote_sensing_ground_truth.json`) and verified labels (`ml/data/ground_truth/human_verified/`) are kept strictly separated.

---

## 4. Recommended First Annotation Batch
- **Target Size**: **150 candidates** sampled proportionally across the 4 acquisition strata (`HIGH_PRIORITY`, `RANDOM_CONTROL`, `FACILITY_MATCHED_LOW_PRIORITY`, `HIGH_FRP_UNMATCHED`).
- **Template Location**: `ml/data/ground_truth/human_verified/annotation_template.json`.
