import json
import os
import pandas as pd
import numpy as np

CANDIDATES_PATH = "ml/data/ground_truth/candidate_pool_v1.json"
POPULATION_PATH = "data/processed/features/event_features_v2.parquet"
PILOT_OUTPUT_DIR = "ml/data/ground_truth/human_verified/pilot"

def build_pilot_subset(sample_size: int = 150, seed: int = 42):
    if not os.path.exists(CANDIDATES_PATH):
        raise FileNotFoundError(f"Candidates pool not found: {CANDIDATES_PATH}")
        
    with open(CANDIDATES_PATH, "r") as f:
        candidates = json.load(f)
        
    df_cand = pd.DataFrame(candidates)
    df_pop = pd.read_parquet(POPULATION_PATH)
    
    # Merge candidates with full features
    merged = df_cand[['event_id', 'acquisition_stratum']].merge(df_pop, on="event_id")
    
    # Deterministic pilot sampling using seed 42
    np.random.seed(seed)
    
    # Stratified sampling across acquisition strata to preserve diversity
    pilot_dfs = []
    strata = merged['acquisition_stratum'].unique()
    per_stratum = sample_size // len(strata)
    
    for st in strata:
        sub = merged[merged['acquisition_stratum'] == st]
        sampled = sub.sample(n=min(per_stratum, len(sub)), random_state=seed)
        pilot_dfs.append(sampled)
        
    pilot_df = pd.concat(pilot_dfs).head(sample_size)
    
    # Fill remaining if rounding left short
    if len(pilot_df) < sample_size:
        rem = merged[~merged['event_id'].isin(pilot_df['event_id'])]
        add_cnt = sample_size - len(pilot_df)
        pilot_df = pd.concat([pilot_df, rem.sample(n=add_cnt, random_state=seed)])
        
    # Split into 100 double-annotated and 50 single-annotated
    shuffled = pilot_df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    double_df = shuffled.iloc[:100]
    single_df = shuffled.iloc[100:150]
    
    # Select evidence columns for annotator view (NO PRE-POPULATED LABELS / PREDICTIONS)
    evidence_cols = [
        "event_id", "centroid_lat", "centroid_lon", "start_time",
        # THERMAL
        "max_frp_mw", "mean_frp_mw", "sum_frp_mw", "spatial_extent_km", "duration_hours", "detection_count",
        # TEMPORAL
        "events_previous_7d", "events_previous_30d", "events_previous_90d", "active_days_previous_30d", "time_since_previous_event_hours",
        # LAND COVER
        "forest_fraction_1km", "cropland_fraction_1km", "builtup_fraction_1km", "grassland_fraction_1km", "natural_land_fraction",
        # INFRASTRUCTURE
        "distance_to_facility_km", "distance_to_power_line_km", "near_refinery", "near_factory", "near_mine", "near_quarry"
    ]
    
    double_records = double_df[evidence_cols].to_dict(orient="records")
    single_records = single_df[evidence_cols].to_dict(orient="records")
    
    os.makedirs(PILOT_OUTPUT_DIR, exist_ok=True)
    
    # Save pilot candidate records
    with open(os.path.join(PILOT_OUTPUT_DIR, "pilot_records_150.json"), "w") as f:
        json.dump(shuffled[evidence_cols].to_dict(orient="records"), f, indent=2)
        
    # Save Annotator 1 assignments (100 double + 50 single = 150 total)
    annotator_1_assignments = double_records + single_records
    for r in annotator_1_assignments:
        r["assigned_class"] = None
        r["confidence"] = None
        r["evidence_used"] = {"thermal": [], "temporal": [], "land_cover": [], "infrastructure": []}
        r["annotation_notes"] = None
        r["annotator_id"] = "ANNOTATOR_1"
        r["timestamp"] = None
        r["review_status"] = "pending"
        
    with open(os.path.join(PILOT_OUTPUT_DIR, "annotator_1_assignments.json"), "w") as f:
        json.dump(annotator_1_assignments, f, indent=2)

    # Save Annotator 2 assignments (100 double-annotated ONLY)
    annotator_2_assignments = json.loads(json.dumps(double_records))
    for r in annotator_2_assignments:
        r["assigned_class"] = None
        r["confidence"] = None
        r["evidence_used"] = {"thermal": [], "temporal": [], "land_cover": [], "infrastructure": []}
        r["annotation_notes"] = None
        r["annotator_id"] = "ANNOTATOR_2"
        r["timestamp"] = None
        r["review_status"] = "pending"
        
    with open(os.path.join(PILOT_OUTPUT_DIR, "annotator_2_assignments.json"), "w") as f:
        json.dump(annotator_2_assignments, f, indent=2)
        
    print(f"Pilot subset built successfully! Total: {len(shuffled)}, Double: {len(double_records)}, Single: {len(single_records)}")

if __name__ == "__main__":
    build_pilot_subset()
