# Reviewer Instructions (Pilot 001 V2)

## Goal
Establish semantic ground truth for thermal anomalies independently.

## Reviewer Procedure
1. **Open Event**: Filter the worksheet (`pilot_001_reviewer_worksheet_v2.csv`) by your `reviewer_id`. Locate the `event_id` to review.
2. **Inspect Context Columns**: Read the provided context columns (FRP, duration, facility distance, land cover) directly in the worksheet. *Note: These are supporting evidence, not proof.*
3. **External Evidence**: Use the provided latitude/longitude/date to inspect external sources (e.g., optical satellite imagery, OSM, news reports, FIRMS historical map). 
4. **Determine Class**: 
   - Decide if the evidence supports one of the five substantive classes.
   - Do NOT infer cause solely from proximity, FRP magnitude, persistence, or land cover.
5. **Record Evidence**: Paste URLs and summarize the visual/external evidence in `evidence_urls` and `evidence_summary`.
6. **Unknown**: If evidence remains insufficient or conflicting after a reasonable investigation, use `unknown_requires_verification`. 
7. **Complete Review**: Mark `review_complete` as `TRUE` ONLY after finishing.

## Taxonomy Definitions & Ambiguity Handling
- **`persistent_industrial_source`**: Evidence confirms established industrial thermal sources (e.g., flares, smelters).
- **`industrial_fire_or_abnormal_event`**: Evidence confirms a non-routine accident or fire at an industrial site.
  - *Ambiguity vs Persistent*: Look for single, localized extreme spikes not matched by historical persistence.
- **`wildfire_or_forest_fire`**: Evidence confirms vegetation fire.
- **`agricultural_burning`**: Evidence confirms agricultural residue burning.
  - *Ambiguity vs Wildfire*: Examine field boundaries in imagery vs. wildland spread.
- **`mining_or_other_industrial_activity`**: Active mining/quarrying not producing persistent flare signatures.
- **`unknown_requires_verification`**: Missing, ambiguous, or conflicting evidence. This is distinct from an incomplete review. Do not use this just to skip an event; use it when investigation yields no confident answer.

## Semantic Unknown vs Incomplete
- **`FALSE` in `review_complete`** = You have not finished reviewing.
- **`unknown_requires_verification` in `label`** = You finished reviewing, but evidence was insufficient.
These must NEVER be conflated.
