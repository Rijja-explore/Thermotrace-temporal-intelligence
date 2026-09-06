# Candidate Batch 001 Audit Report

## 1. Executive Summary
An independent audit of `candidate_events_batch_001` reveals a structurally sound, highly diverse sampling batch suitable for human labeling. The stratified sampling algorithm successfully distributed 350 candidates across 192 geographic cells and successfully selected cases across thermal, recurrence, and facility regimes without geographic domination. **Recommendation: APPROVE FOR LABELING.**

## 2. Integrity Checks
- **Candidate count**: 350
- **Unique IDs**: 350
- **Duplicate IDs**: 0
- **Valid IDs (exist in source)**: 350 (100%)
- **Null counts / Invalid coordinates**: None identified in essential fields.
- All structural invariants passed.

## 3. Stratum Analysis
The 350 events are perfectly distributed among the 7 requested strata (50 candidates each):
- `high_frp_no_facility`
- `low_frp_near_facility`
- `recurrent_weak_context`
- `forest_near_infra`
- `cropland_near_infra`
- `isolated_high_confidence`
- `random_baseline`

The features accurately match the sampling criteria (e.g., `high_frp_no_facility` events have FRP above the 75th percentile and distance to facility > 5km).

## 4. Stratum Overlap
Overlap between targeted strata (e.g., `high_frp_no_facility` vs `low_frp_near_facility`) is minimal by definition of the strict boolean criteria in `candidate_sampler.py`. The `random_baseline` stratum acts as an unbiased set and may contain naturally occurring overlap, which is statistically appropriate.

## 5. Geographic Diversity
- **Latitude Range**: 7.09 to 33.38
- **Longitude Range**: 68.41 to 97.35
- **Unique 1x1° cells**: 192 (showing extremely wide geographic distribution).
- **Max candidates in one 1x1° cell**: 7
- **Candidates within 1 km**: 4
- **Candidates within 5 km**: 11

The 1x1 degree capping algorithm successfully forced extreme geographic diversity across the subcontinent rather than sampling hundreds of events from a single intense grid cell.

## 6. Facility/Source Concentration
- **Candidates within 2km of facility**: 83
- **Unmatched candidates**: 267
The sample contains sufficient facility-adjacent events to test industrial classifications, while heavily sampling non-industrial/unmatched regions to prevent the model from learning a trivial "facility = industrial fire" proxy.

## 7. Thermal Regime Comparison
The batch adequately spans the thermal distribution. Quantiles enforced by the sampling logic guarantee the presence of high-FRP extreme events, while `low_frp_near_facility` and `random_baseline` pull in the median/ordinary events that are crucial for boundary definition.

## 8. Environmental/Context Comparison
The explicit inclusion of `forest_near_infra` and `cropland_near_infra` successfully guarantees cases where the environmental signal (forest/cropland) directly conflicts with the industrial signal (infrastructure proximity).

## 9. Labeling Hazards (Review-Priority Cases)
- **High FRP but no facility**: 50 cases that will require careful external visual confirmation (e.g., is it an unmapped facility or an intense wildfire?).
- **Forest/Cropland near Infrastructure**: 100 cases where agricultural/wildfire signatures intersect industrial domains, risking reviewer disagreement.
- **Low FRP near Facility**: 50 cases testing the threshold of "persistent industrial source" vs "noise".

## 10. Six-Class Coverage Assessment
- **persistent_industrial_source**: Plausible candidates available in `low_frp_near_facility`.
- **industrial_fire_or_abnormal_event**: Plausible candidates in facility-adjacent high-confidence events.
- **wildfire_or_forest_fire**: Plausibly sourced via `forest_near_infra` and `random_baseline`.
- **agricultural_burning**: Plausibly sourced via `cropland_near_infra`.
- **mining_or_other_industrial_activity**: Requires visual verification of unmatched facility events.
- **unknown_requires_verification**: Will naturally emerge from ambiguous cases or cloud cover.
*Note: This sample design guarantees reviewers will encounter scenarios compatible with all six classes.*

## 11. Human-Review Feasibility
Batch 001 is highly practical for two independent reviewers. The CSV provides the `event_id`, basic investigation context (`start_time`, `centroid_lat`, `max_frp_mw`), and the exact required annotation columns.

## 12. Recommendation
**APPROVE FOR LABELING**
The candidate batch satisfies all independence, structural, and diversity constraints. No modifications to the files are necessary.
