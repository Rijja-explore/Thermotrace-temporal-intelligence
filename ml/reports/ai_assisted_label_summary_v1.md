# AI-Assisted Provisional Label Summary Report (N=1,500)

> **IMPORTANT SCIENTIFIC DISCLAIMER**:
> These are AI-assisted weak/provisional labels and are NOT human-verified ground truth.
> They are strictly used to prioritize candidates for human review and MUST NOT be used as verified ground truth for model accuracy evaluation.

---

## 1. Summary Statistics & Counts (N=1500)

### Provisional Label Distribution
- **`persistent_industrial_source`**: 867 events (57.80%)
- **`wildfire_or_forest_fire`**: 314 events (20.93%)
- **`unknown_requires_verification`**: 200 events (13.33%)
- **`agricultural_burning`**: 83 events (5.53%)
- **`mining_or_other_industrial_activity`**: 36 events (2.40%)

### Confidence Level Distribution
- **`MEDIUM` Confidence**: 753 events (50.20%)
- **`HIGH` Confidence**: 547 events (36.47%)
- **`LOW` Confidence**: 200 events (13.33%)

### Human Review Requirement Breakdown
- **`requires_human_review = true`**: 953 events (63.53%)
- **`requires_human_review = false`**: 547 events (36.47%)
- **Provisional Unknowns (`unknown_requires_verification`)**: 200 events (13.33%)

---

## 2. Highest-Priority Human Review Ranking
Human domain annotators should prioritize review using `ml/data/ground_truth/ai_assisted/human_review_priority_v1.json`, which orders candidate review queue by:
1. `LOW` Confidence events
2. Provisional `unknown_requires_verification` cases
3. `requires_human_review = true` events
4. High FRP intensity spikes ($>100$ MW)
