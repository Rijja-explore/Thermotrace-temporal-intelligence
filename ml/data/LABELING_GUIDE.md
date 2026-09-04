# ThermoTrace Labeling Guide

## Class Definitions

### persistent_industrial_source
Recurring/persistent thermal activity consistent with a normal or established industrial thermal source. Examples may include legitimate industrial heat/process sources. Do not label solely from facility proximity.

### industrial_fire_or_abnormal_event
Evidence supports an industrial fire, abnormal thermal event, accident, or other non-routine industrial thermal event.

### wildfire_or_forest_fire
Evidence supports vegetation/forest wildfire.

### agricultural_burning
Evidence supports agricultural residue burning or agricultural fire activity.

### mining_or_other_industrial_activity
Evidence supports mining, quarrying, extraction, or other industrial activity that does not fit the persistent industrial source or industrial fire category.

### unknown_requires_verification
Evidence is insufficient, conflicting, or unavailable. This class is VALID and MUST NOT be treated as a failure.

---

## Evidence Requirements

### Primary Evidence
Strong independent evidence that directly supports the semantic interpretation (e.g., optical satellite imagery, confirmed news articles).

### Secondary Evidence
Contextual evidence that increases/decreases plausibility but does not prove the class.

### Insufficient Evidence
FIRMS detection alone, proximity alone, FRP magnitude alone, persistence alone, or model/risk score alone. **Do not permit the feature table itself to become circular ground truth.**

---

## Reviewer Protocol

1. Reviewer 1 independently investigates the candidate.
2. Reviewer 2 independently investigates the candidate.
3. Each assigns class, evidence, confidence, notes.
4. Disagreements are preserved.
5. Final consensus label is assigned separately.
6. If consensus cannot be reached, use `unknown_requires_verification`.
**Do not silently resolve disagreement.**

## Evidence Provenance
For every non-unknown label, require evidence provenance. Do not invent URLs or fabricate evidence.
