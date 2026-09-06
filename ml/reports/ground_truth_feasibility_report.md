# AI/ML Ground-Truth Feasibility & Label Strategy Audit

## 1. Current Ground-Truth Dataset Status
Based on an audit of the `ml/data/` directory (specifically the `pilot_001_REVIEWER` worksheets and previous AI generation tasks), the repository holds exactly 0 verified ground-truth semantic labels.

| Category                                 | Count | Valid training ground truth? | Reason |
| ---------------------------------------- | ----: | ---------------------------- | ------ |
| Human consensus + independent evidence   | 0     | Yes                          | No labels have been entered by human reviewers; evidence access is blocked. |
| Human label without independent evidence | 0     | No                           | Policy dictates independent remote sensing/reports are required to verify semantic cause. |
| AI-assisted label                        | 17    | No                           | The 5-event (V2) and 12-event class diversity batches are either `unknown` or programmatically generated hypotheses (hallucinations of search access). |
| OSM/context-derived label                | 0     | No                           | Constitutes ML leakage/circular reasoning if used as ground truth for a model evaluating those same contexts. |
| FIRMS-derived label                      | 0     | No                           | FIRMS only detects thermal anomalies, not semantic causes. |
| Heuristic label                          | 0     | No                           | Rules are not ground truth. |
| Unreviewed                               | 40    | No                           | The current pilot queue contains 40 unreviewed candidates. |
| AI-assisted unresolved investigation outcomes — NOT ground truth   | 5     | No                           | Batch 001 v2 demonstrated 5 events lack retrievable evidence. |

## 2. Evidence Availability Audit
Previous audits firmly established the environment constraint: `NO_USABLE_INDEPENDENT_EVIDENCE_ACCESS`.
- **Sentinel-2 L2A / Landsat / Modis**: `UNAVAILABLE_IN_CURRENT_ENVIRONMENT` (Blocked by API/ConnectionReset constraints).
- **Independent Incident Reports / News**: `CONCEPTUALLY_POSSIBLE_BUT_NOT_AVAILABLE` (Dependent on web search capabilities which were previously proven to hallucinate non-existent records).
- **Government / Fire Service Records**: `UNAVAILABLE_IN_CURRENT_ENVIRONMENT`.

## 3. Defensible Labeling Policy
If evidence becomes accessible in the future, a valid training label must include:
- `semantic_class`: Selected from the V2 taxonomy.
- `evidence_source`: The exact platform/dataset (e.g., "Sentinel-2 L2A via Earth Search").
- `evidence_timestamp`: Acquisition time proving relation to the event.
- `evidence_url/reference`: Verifiable path to the artifact.
- `evidence_description`: Text summarizing what the evidence shows visually.
- `reviewer` & `reviewer_confidence`: Human metadata.
- `adjudication_status`: Consensus established by 2+ reviewers.

### What MUST NEVER be used as semantic ground truth:
- FIRMS detection, FRP magnitude, persistence, land cover, OSM proximity, population, synthetic risk scores, or AI inference lacking independent URL verification.

## 4. Minimum Dataset Requirements & Taxonomy Recommendation
Training a 5-class semantic classifier requires substantial class coverage. The current verified sample is insufficient for reliable stratified training, evaluation, calibration, and per-class metrics.
**Taxonomy Recommendation**: The `unknown_requires_verification` label should **not** be treated as a 6th semantic class. It represents an epistemic state (abstention), not a physical property of the fire. The classification framework should be `5 semantic classes + 1 abstention/verification state`.

## 5. Alternative ML Paths Evaluation

| Option | Requirements | Claims | Limitations | Suitability for SIH Demo |
|--------|--------------|--------|-------------|--------------------------|
| **A. Full Supervised Classifier** | Thousands of verified labels. | High accuracy semantic classification. | Blocked by 0 ground truth. | ❌ Impossible |
| **B. Small Supervised Pilot** | ~250 verified labels. | Proof-of-concept classification. | Blocked by 0 ground truth. | ❌ Impossible |
| **C. Weak Supervision** | Rules + Unlabeled data. | Bootstrapped pseudo-labels. | Cannot be validated without real ground truth; risks compounding heuristic bias. | ⚠️ Risky / Low rigor |
| **D. Anomaly Detection (Unsupervised)** | Unlabeled feature vectors. | Identifies statistically abnormal thermal events. | Cannot assign semantic meaning (e.g., "Industrial Fire"). | ✅ Highly suitable |
| **E. Verification Prioritization** | Unlabeled features + proximity. | Ranks events by their potential risk/impact to prompt human review. | Does not predict class, only priority. | ✅ Highly suitable |

## 6. Hard Decision
**GROUND_TRUTH_INSUFFICIENT**

### Recommended Next AI/ML Action
Do NOT attempt to train the supervised classification architecture.
Instead, pivot the ML engineering effort to **Path D (Unsupervised Anomaly/Novelty Detection)** or **Path E (Verification Prioritization Ranking)**. These approaches do not require semantic ground truth and directly serve the ThermoTrace objective of triaging large volumes of FIRMS data for human verification, perfectly aligning with the `VerificationState` architecture previously implemented.
