import pandas as pd
import numpy as np
from pathlib import Path

# Load Batch 001 Candidates
batch_csv = pd.read_csv('ml/data/candidate_events_batch_001.csv')
batch_features = pd.read_parquet('ml/data/candidate_events_batch_001_features.parquet')

# We need exactly 40 events from the 350 candidates.
# 7 strata. 40 / 7 = 5.71
# So we select 6 from the first 5 strata, and 5 from the last 2 strata. (6*5 + 5*2 = 30 + 10 = 40)
strata_counts = {
    'high_frp_no_facility': 6,
    'low_frp_near_facility': 6,
    'recurrent_weak_context': 6,
    'forest_near_infra': 6,
    'cropland_near_infra': 6,
    'isolated_high_confidence': 5,
    'random_baseline': 5
}

seed = 123
np.random.seed(seed)

sampled_ids = []
for stratum, count in strata_counts.items():
    subset = batch_csv[batch_csv['sampling_stratum'] == stratum]
    sampled = subset.sample(n=count, random_state=seed)
    sampled_ids.extend(sampled['event_id'].tolist())

# Create pilot CSV
pilot_csv = batch_csv[batch_csv['event_id'].isin(sampled_ids)].copy()
pilot_csv.to_csv('ml/data/candidate_events_pilot_001.csv', index=False)

# Create pilot features
pilot_features = batch_features[batch_features['event_id'].isin(sampled_ids)].copy()
pilot_features.to_parquet('ml/data/candidate_events_pilot_001_features.parquet', index=False)

# Create reviewer worksheet
cols = [
    "event_id",
    "label",
    "reviewer_1", "reviewer_1_confidence", "reviewer_1_evidence_urls", "reviewer_1_evidence_type", "reviewer_1_notes", "reviewer_1_date",
    "reviewer_2", "reviewer_2_confidence", "reviewer_2_evidence_urls", "reviewer_2_evidence_type", "reviewer_2_notes", "reviewer_2_date",
    "final_label", "final_label_confidence", "consensus_status", "consensus_notes", "final_evidence_urls", "final_evidence_type", "label_date", "label_version"
]
ws = pd.DataFrame(columns=cols)
ws['event_id'] = pilot_csv['event_id'].values
ws.to_csv('ml/data/pilot_001_reviewer_worksheet.csv', index=False)

# Create review index
idx_cols = [
    "event_id", "sampling_stratum", "centroid_lat", "centroid_lon", "start_time", "end_time",
    "max_frp_mw", "duration_hours", "distance_to_facility_km"
]
# end_time and distance_to_facility_km are in features, not necessarily in csv. Let's merge if needed.
# For simplicity, we grab everything we can from features
idx_df = pilot_features.reset_index(drop=True)
idx_df.index.name = "pilot_index"
# Some columns might not exist, use get
out_idx = pd.DataFrame()
for c in idx_cols:
    if c in idx_df.columns:
        out_idx[c] = idx_df[c]
    elif c in pilot_csv.columns:
        out_idx[c] = pilot_csv.set_index('event_id').loc[idx_df['event_id'], c].values

out_idx.to_csv('ml/data/pilot_001_review_index.csv')

print(f"Generated pilot files. Total candidates: {len(pilot_csv)}")
print(pilot_csv['sampling_stratum'].value_counts())
