# Reviewer Instructions for Batch 001

## Workflow

The dual-reviewer protocol is required for establishing semantic ground truth. 
1. **Reviewer 1** independently investigates each event and records their proposed label, confidence, evidence URLs, evidence type, and notes. Reviewer 1 must NOT see Reviewer 2's decision.
2. **Reviewer 2** independently performs the same investigation without seeing Reviewer 1's decision.
3. **Consensus**: Only after both independent reviews are complete should disagreement be examined. A disagreement must NOT be silently overwritten.

## Evidence Hierarchy
- **Strong evidence**: Independent, reliable records that directly establish the nature of the event/source (e.g. optical imagery, ground reports).
- **Supporting evidence**: Contextual information (e.g. facility proximity, land-cover context). These can support a decision but should not automatically establish it.
- **Insufficient evidence**: FIRMS detection alone, FRP magnitude, persistence, OSM facility presence, baseline risk score, or proximity to roads/power lines. Do NOT use the ML feature table as circular ground truth.

## The Unknown Class
The class `unknown_requires_verification` is a **VALID scientific label**.
Use it when:
- Evidence is unavailable or insufficient.
- Evidence conflicts.
- The distinction between classes cannot be established.
- The event cannot be reliably attributed.
Do NOT force a decision simply to improve class balance.

## Class-Specific Decision Guidance

- **persistent_industrial_source**: Evidence supports a recurring/established industrial thermal source (normal/persistent operation). Facility proximity alone is supporting evidence, not proof.
- **industrial_fire_or_abnormal_event**: Independent evidence supports an abnormal industrial thermal event, accident, or non-routine event. High FRP near a factory is NOT sufficient by itself.
- **wildfire_or_forest_fire**: Evidence supports vegetation/forest wildfire.
- **agricultural_burning**: Evidence supports agricultural residue burning or agricultural fire activity.
- **mining_or_other_industrial_activity**: Evidence supports mining/quarrying/extraction that does not fit persistent sources or fires.
- **unknown_requires_verification**: Evidence cannot establish the source type confidently.

## Evidence Provenance
For every non-Unknown final label, require `final_evidence_urls` and `final_evidence_type`. Do not fabricate evidence. If no independent evidence exists, use `unknown_requires_verification`.
