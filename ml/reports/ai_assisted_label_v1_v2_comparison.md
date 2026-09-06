# AI-Assisted Provisional Label Comparison: V1 vs V2 (N=1,500)

> **EXPLICIT SCIENTIFIC DISCLAIMER**:
> Both V1 and V2 are AI-assisted weak/provisional labels and are **NOT human-verified ground truth**.
> V2 corrects rule precedence behavior (evaluating mining and acute industrial fire conditions before routine persistent source rules).
> **V2 is NOT described as more accurate simply because it is more balanced**.

---

## 1. Class Distribution Comparison

| Taxonomy Class | V1 Count | V1 % | V2 Count | V2 % | Change |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `agricultural_burning` | 83 | 5.53% | 83 | 5.53% | +0 |
| `mining_or_other_industrial_activity` | 36 | 2.40% | 826 | 55.07% | +790 |
| `persistent_industrial_source` | 867 | 57.80% | 77 | 5.13% | -790 |
| `unknown_requires_verification` | 200 | 13.33% | 200 | 13.33% | +0 |
| `wildfire_or_forest_fire` | 314 | 20.93% | 314 | 20.93% | +0 |

- **Total Candidates Evaluated**: 1500
- **Total Events Whose Label Changed**: **790 events** (52.67%)

---

## 2. Transition Matrix (V1 Label -> V2 Label)

```text
v2                                   agricultural_burning  mining_or_other_industrial_activity  persistent_industrial_source  unknown_requires_verification  wildfire_or_forest_fire   All
v1                                                                                                                                                                                        
agricultural_burning                                   83                                    0                             0                              0                        0    83
mining_or_other_industrial_activity                     0                                   36                             0                              0                        0    36
persistent_industrial_source                            0                                  790                            77                              0                        0   867
unknown_requires_verification                           0                                    0                             0                            200                        0   200
wildfire_or_forest_fire                                 0                                    0                             0                              0                      314   314
All                                                    83                                  826                            77                            200                      314  1500
```

---

## 3. Key Transition Analysis
1. **`persistent_industrial_source` -> `mining_or_other_industrial_activity`**:
   - **790 events** previously absorbed by `persistent_industrial_source` in V1 (due to Rule 1 running first) had explicit `near_mine` or `near_quarry` spatial context flags. In V2, evaluating mining conditions prior to routine persistence correctly allowed these 790 events to reach `mining_or_other_industrial_activity`.
2. **`industrial_fire_or_abnormal_event` Count in V2**:
   - **0 events**. In the 1,500 candidate pool, zero events satisfied the strict criteria of max_frp_mw >= 150.0 MW AND industrial context without meeting other conditions. The 150 MW threshold was strictly preserved per scientific directives.
