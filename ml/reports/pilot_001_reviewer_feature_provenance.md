# Pilot 001 Reviewer Feature Provenance Audit

## Objective
This report classifies every contextual feature exposed in the `pilot_001_reviewer_worksheet_v2.csv` to ensure human reviewers are not exposed to future leakage, synthetic heuristics, or circular labels.

## Current Exposed Contextual Features
The V2 worksheet exposes the following 11 contextual columns (plus `event_id`):

1. **`centroid_lat`**: Detection-time available. Required for reviewer geospatial investigation.
2. **`centroid_lon`**: Detection-time available. Required for reviewer geospatial investigation.
3. **`start_time`**: Detection-time available.
4. **`end_time`**: Post-event but valid for post-event classification.
5. **`max_frp_mw`**: Post-event but valid for post-event classification.
6. **`duration_hours`**: Post-event but valid for post-event classification.
7. **`detection_count`**: Post-event but valid for post-event classification.
8. **`distance_to_facility_km`**: Detection-time available.
9. **`events_previous_30d`**: Detection-time available (historical recurrence).
10. **`forest_fraction_1km`**: Detection-time available.
11. **`cropland_fraction_1km`**: Detection-time available.

*Note: Post-event features (`duration_hours`, `detection_count`, `max_frp_mw`, `end_time`) are legitimate and necessary for this post-event semantic classifier. However, if this model is later adapted for real-time/in-progress alerting, these features would be unavailable at the moment of initial detection and must be removed.*

## Audit of Prohibited Fields
The following fields were strictly audited and confirmed **EXCLUDED** from the reviewer worksheet:
- **`baseline_risk_score` / `baseline_risk_level`**: Excluded. Synthetic heuristic that could circularly bias the reviewer into assigning industrial classes based on legacy logic.
- **Risk components/reasons**: Excluded. Synthetic heuristics.
- **Future-leaky spatial density (e.g. `events_local_1km`)**: Excluded. Computed over the entire dataset lifespan; contains future information.
- **Admin identifiers / string metadata**: Excluded to prevent irrelevant bias.
- **Model predictions/pseudo-labels**: None exist.

## Summary
- **Total contextual columns exposed**: 11
- **Safe columns**: 11
- **Excluded columns**: All heuristic, risk, and leaky features
- **Questionable columns**: 0
- **Reason for exclusions**: To prevent circular logic, reviewer bias, and temporal leakage.

No fields need to be removed from V2. The worksheet is clean.
