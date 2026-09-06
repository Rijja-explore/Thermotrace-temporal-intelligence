# Pilot 001 Pre-Label Audit

## Overview
This report audits the **40-event pilot** drawn from Candidate Batch 001. The purpose of this pilot is to test the human labeling protocol across diverse regimes without exhausting reviewer resources.

## Selection Integrity
- **Selected Candidates**: 40
- **Source Batch**: `candidate_events_batch_001.csv` (350 candidates)
- **Random Seed**: 123
- All structural constraints and invariants are preserved (unique IDs, no missing required fields).
- Semantic labels intentionally blank.

## Stratum Representation
The 40 events were deterministically selected to cover all seven predefined strata, ensuring the reviewers are exposed to a representative distribution of regimes:
- `high_frp_no_facility`: 6
- `low_frp_near_facility`: 6
- `recurrent_weak_context`: 6
- `forest_near_infra`: 6
- `cropland_near_infra`: 6
- `isolated_high_confidence`: 5
- `random_baseline`: 5

## Expected Review Characteristics
By drawing evenly across these strata, the pilot guarantees that reviewers will encounter:
1. **Facility-Ambiguous Cases**: Events with extreme FRP values isolated from known infrastructure.
2. **Context-Ambiguous Cases**: Agricultural and forested land intersecting infrastructure bounds.
3. **Behavioral Diversity**: Recurrent smoldering events vs. isolated high-intensity flashes.

## Geographic Diversity
The random sampling across the previously capped 1x1 degree bins resulted in a robust geographic distribution representing a variety of regions across the source matrix. Spatial proximity tests confirmed that events are well-separated, minimizing redundant evaluations of the same local fire complex.

## Next Steps
The pilot is validated and structural invariants are confirmed by the test suite (28/28 tests passing). The worksheets are prepared for dual independent review.
