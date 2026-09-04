# Pilot 001 Human Review Preparation

## Objective
To strictly implement the data handoff for human reviewers by enforcing the evidence audit boundaries. Synthetic, heuristic, and identifying fields have been completely scrubbed from the worksheets.

## Created Artifacts
- `ml/data/pilot_001_REVIEWER_1_EVIDENCE.csv`
- `ml/data/pilot_001_REVIEWER_2_EVIDENCE.csv`

## Integrity Verification
- **Exactly 40 rows per file**: Verified (40 rows)
- **Exactly the same 40 event IDs**: Verified
- **Zero duplicates**: Verified
- **Zero missing IDs**: Verified
- **Reviewer IDs correct**: Verified (`REVIEWER_1`, `REVIEWER_2`)
- **No writable label fields are pre-populated**: Verified (0 pre-populated labels)
- **Independent files**: Verified (Reviewer 1 contains no Reviewer 2 decisions, and vice versa)

## Field Formatting
- Directly valid factual fields (e.g. `centroid_lat`, `near_power_plant`) retain their original names.
- Allowed but deterministically derived fields (e.g. `forest_fraction_1km`) are prefixed with `DERIVED_CONTEXT_`.
- Allowed post-event aggregate fields (e.g. `duration_hours`, `max_frp_mw`) are prefixed with `POST_EVENT_FEATURE_`.

## Taxonomy Constraints
Reviewers are restricted to the following exact classes:
1. `persistent_industrial_source`
2. `industrial_fire_or_abnormal_event`
3. `wildfire_or_forest_fire`
4. `agricultural_burning`
5. `mining_or_other_industrial_activity`
6. `unknown_requires_verification`

## Critical Reviewer Instructions Enforced
Reviewers have been explicitly instructed **NOT** to infer the semantic label merely from context hints like `nearest_facility_type` or `landcover_class`. These are contextual clues, not definitive ground truth. Reviewers must independently establish and summarize evidence.

Unreviewed events must have `label` left blank and `review_complete` left `FALSE`. The label `unknown_requires_verification` is strictly reserved for events that have been fully investigated but lack sufficient evidence.

---

**READY_FOR_HUMAN_LABELING**
