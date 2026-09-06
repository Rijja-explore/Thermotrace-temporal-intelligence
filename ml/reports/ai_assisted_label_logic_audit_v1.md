# AI-Assisted Provisional Labeling Logic Audit Report

## 1. Executive Summary & Core Verdict
- **Core Defect Identified**: **Precedence Absorption & Overly Strict Industrial-Fire Thresholds**.
- **Observation**: `industrial_fire_or_abnormal_event` had 0 assigned events out of 1,500 candidates.
- **Root Cause**:
  1. **Precedence Shadowing**: Rule 1 (`persistent_industrial_source`, checking `dist_fac <= 2.0` and `active_days >= 10.0`) was evaluated *before* Rule 2 (`industrial_fire_or_abnormal_event`). Events near facilities with high FRP ($>150$ MW) and high active days were absorbed by Rule 1 before Rule 2 was evaluated.
  2. **Threshold Reachability**: In the remaining candidates not absorbed by Rule 1, zero events simultaneously satisfied `max_frp_mw >= 150.0` AND (`near_refinery` / `near_factory` / `builtup_fraction >= 0.3`).

---

## 2. Quantitative Logic Breakdown (Observed Measurements)

### A. Industrial Fire Class Reachability
- **Total Candidates satisfying Industrial Fire criteria in raw data (`max_frp >= 150` & Industrial Context)**: **0 events**.
- **Industrial Fire Candidates Absorbed by Rule 1 (`persistent_industrial_source`)**: **0 events** (0.0% of potential industrial fires if any).
- **Candidates reaching Rule 2 and satisfying Industrial Fire criteria**: **0 events**.

### B. Persistent Industrial Overlap & Broadness Analysis (867 events)
- **Total Assigned `persistent_industrial_source`**: 867 events.
- **Persistent Industrial events with Mining/Quarry overlap**: 790 events (91.1%).
- **Persistent Industrial events with High FRP Spikes ($\ge 150$ MW)**: 0 events (0.0%).
- **Persistent Industrial events with Low Persistence ($<10$ active days)**: 0 events (0.0%).

---

## 3. Decision Flow & Rule Order Audit

### Current Decision Sequence in `generate_ai_assisted_labels.py`:
```text
Step 1: If dist_fac <= 2.0 and active_days >= 10.0 -> persistent_industrial_source
Step 2: Else If (near_refinery/factory or builtup >= 0.3) and max_frp >= 150 -> industrial_fire_or_abnormal_event
Step 3: Else If (near_mine/quarry) and (dist_fac <= 3.0 or builtup > 0.1) -> mining_or_other_industrial_activity
Step 4: Else If forest_frac >= 0.4 and dist_fac > 2.0 -> wildfire_or_forest_fire
Step 5: Else If crop_frac >= 0.4 and active_days < 5.0 and dist_fac > 2.0 -> agricultural_burning
Step 6: Else -> unknown_requires_verification
```

---

## 4. Inference & Potential Class-Collapse Mechanisms

* **Precedence Order Flaw**: High-intensity abnormal flare/fire spikes occurring at persistent facilities should be flagged as potential `industrial_fire_or_abnormal_event` or marked as requiring human review (`requires_human_review = True`), rather than silently categorized as routine operational flares (`persistent_industrial_source`).
* **Rule Broadness**: The threshold `active_days >= 10.0` combined with `dist_fac <= 2.0` captures 57.8% of the candidate pool because candidate acquisition specifically sampled 50% high-priority recurrent events.

---

## 5. Recommended Logic Corrections (For Future Review)

1. **Re-order Precedence**: Evaluate acute/abnormal industrial events (`industrial_fire_or_abnormal_event`) before routine persistent sources, or tag high-FRP spikes ($\ge 150$ MW) at persistent facilities as requiring human review (`requires_human_review = True`).
2. **Refine Thresholds**: Calibrate the FRP threshold for abnormal industrial events (e.g. $\ge 100$ MW) to capture high-heat transient flaring anomalies.
