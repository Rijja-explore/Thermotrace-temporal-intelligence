# Ground-Truth Sampling Plan Report — Person 2 AI/ML

## 1. Population & Candidate Sampling Strategy
- **Total Population**: 996,891 thermal events.
- **Initial Candidate Pool**: 1,000 deterministically sampled candidates (`ml/data/ground_truth/candidate_pool_v1.json`).

---

## 2. Target Annotation Size & Statistical Justification
- **Recommended Initial Target**: **1,500 human-verified events** across the Indian subcontinent.
- **Class Balance Targets**:
  - `persistent_industrial_source`: ~300 verified events
  - `industrial_fire_or_abnormal_event`: ~200 verified events
  - `wildfire_or_forest_fire`: ~350 verified events
  - `agricultural_burning`: ~400 verified events
  - `mining_or_other_industrial_activity`: ~250 verified events
