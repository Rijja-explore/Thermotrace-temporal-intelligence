import json
import os
import pandas as pd
import numpy as np

CANDIDATES_PATH = "ml/data/ground_truth/candidate_pool_v1.json"
V2_LABELS_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
FEATURES_PATH = "data/processed/features/event_features_v2.parquet"

OUTPUT_DIR = "ml/data/ground_truth/human_verified/pilot_v2"
PILOT_RECORDS_PATH = os.path.join(OUTPUT_DIR, "pilot_v2_records_100.json")
ANNOTATOR_1_PATH = os.path.join(OUTPUT_DIR, "annotator_1_assignments.json")
ANNOTATOR_2_PATH = os.path.join(OUTPUT_DIR, "annotator_2_assignments.json")
REPORT_PATH = "ml/reports/human_verification_pilot_v2_sampling_report.md"

SEED = 42

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("ml/reports", exist_ok=True)
    
    # 1. Load data
    with open(CANDIDATES_PATH, "r") as f:
        pool_raw = json.load(f)
    pool_df = pd.DataFrame(pool_raw)
    
    with open(V2_LABELS_PATH, "r") as f:
        v2_raw = json.load(f)
    v2_df = pd.DataFrame(v2_raw)
    
    feat_df = pd.read_parquet(FEATURES_PATH)
    
    # Merge pool, v2 labels, and features
    merged = pool_df.merge(
        v2_df[['event_id', 'ai_assisted_label', 'ai_confidence', 'evidence_used', 'reasoning_summary', 'requires_human_review']],
        on='event_id'
    )
    df = merged.merge(feat_df, on='event_id', suffixes=('', '_feat'))
    
    # Ensure event_id sorting for determinism
    df = df.sort_values('event_id').reset_index(drop=True)
    
    rng = np.random.RandomState(SEED)
    
    # Define Strata:
    # We want 100 events total:
    # 1. Persistent industrial: target 15
    # 2. Mining/industrial activity: target 25
    # 3. Wildfire/forest fire: target 18
    # 4. Agricultural burning: target 15
    # 5. Unknown / requires verification: target 20
    # 6. Industrial fire / abnormal event candidates (high FRP industrial/infrastructure context): target 7
    # Total = 15 + 25 + 18 + 15 + 20 + 7 = 100 events
    
    selected_indices = set()
    sample_records = []
    
    # Strata 6: Industrial fire / abnormal event candidates
    # Events with highest FRP near facility / factory / refinery / builtup context
    ind_fire_mask = (
        ((df['distance_to_facility_km'] <= 10.0) | (df['builtup_fraction_1km'] >= 0.05) | df['near_factory'] | df['near_refinery']) &
        (~df.index.isin(selected_indices))
    )
    ind_fire_candidates = df[ind_fire_mask].sort_values('max_frp_mw', ascending=False).index.tolist()
    # Take top FRP candidates among industrial context
    chosen_ind_fire = ind_fire_candidates[:7]
    for idx in chosen_ind_fire:
        selected_indices.add(idx)
        df.loc[idx, 'sampling_stratum'] = 'industrial_fire_candidate'
        
    # Strata 1: Persistent industrial source
    pers_mask = (df['ai_assisted_label'] == 'persistent_industrial_source') & (~df.index.isin(selected_indices))
    pers_indices = df[pers_mask].index.tolist()
    rng.shuffle(pers_indices)
    chosen_pers = pers_indices[:15]
    for idx in chosen_pers:
        selected_indices.add(idx)
        df.loc[idx, 'sampling_stratum'] = 'persistent_industrial_source'
        
    # Strata 4: Agricultural burning
    agri_mask = (df['ai_assisted_label'] == 'agricultural_burning') & (~df.index.isin(selected_indices))
    agri_indices = df[agri_mask].index.tolist()
    rng.shuffle(agri_indices)
    chosen_agri = agri_indices[:15]
    for idx in chosen_agri:
        selected_indices.add(idx)
        df.loc[idx, 'sampling_stratum'] = 'agricultural_burning'
        
    # Strata 5: Unknown / LOW confidence
    unk_mask = (df['ai_assisted_label'] == 'unknown_requires_verification') & (~df.index.isin(selected_indices))
    unk_indices = df[unk_mask].index.tolist()
    rng.shuffle(unk_indices)
    chosen_unk = unk_indices[:20]
    for idx in chosen_unk:
        selected_indices.add(idx)
        df.loc[idx, 'sampling_stratum'] = 'unknown_requires_verification'

    # Strata 3: Wildfire / Forest Fire
    wild_mask = (df['ai_assisted_label'] == 'wildfire_or_forest_fire') & (~df.index.isin(selected_indices))
    wild_indices = df[wild_mask].index.tolist()
    rng.shuffle(wild_indices)
    chosen_wild = wild_indices[:18]
    for idx in chosen_wild:
        selected_indices.add(idx)
        df.loc[idx, 'sampling_stratum'] = 'wildfire_or_forest_fire'
        
    # Strata 2: Mining / Other Industrial Activity
    mine_mask = (df['ai_assisted_label'] == 'mining_or_other_industrial_activity') & (~df.index.isin(selected_indices))
    mine_indices = df[mine_mask].index.tolist()
    rng.shuffle(mine_indices)
    chosen_mine = mine_indices[:25]
    for idx in chosen_mine:
        selected_indices.add(idx)
        df.loc[idx, 'sampling_stratum'] = 'mining_or_other_industrial_activity'

    # If any remaining slots needed to reach 100
    if len(selected_indices) < 100:
        rem_needed = 100 - len(selected_indices)
        rem_all = df[~df.index.isin(selected_indices)].index.tolist()
        rng.shuffle(rem_all)
        for idx in rem_all[:rem_needed]:
            selected_indices.add(idx)
            df.loc[idx, 'sampling_stratum'] = df.loc[idx, 'ai_assisted_label']

    pilot_df = df.loc[list(selected_indices)].copy()
    pilot_df = pilot_df.sort_values('event_id').reset_index(drop=True)
    
    # 2. Select Double-Annotation Subset (exactly 30 events)
    # Stratified toward:
    # - Unknown / LOW confidence (~10)
    # - Industrial fire candidates (~5)
    # - Land cover ambiguity (wildfire vs agri or forest vs crop) (~5)
    # - Industrial/mining ambiguity (~5)
    # - Persistent industrial with medium confidence (~5)
    
    double_annot_indices = set()
    
    # Unknown / LOW confidence
    unk_pilot = pilot_df[pilot_df['ai_confidence'] == 'LOW'].index.tolist()
    rng.shuffle(unk_pilot)
    for idx in unk_pilot[:10]:
        double_annot_indices.add(idx)
        
    # Industrial fire candidates
    ind_pilot = pilot_df[pilot_df['sampling_stratum'] == 'industrial_fire_candidate'].index.tolist()
    rng.shuffle(ind_pilot)
    for idx in ind_pilot[:5]:
        double_annot_indices.add(idx)
        
    # Land cover ambiguity (forest_frac between 0.2 and 0.5, or cropland_frac between 0.2 and 0.5)
    lc_ambig = pilot_df[
        (~pilot_df.index.isin(double_annot_indices)) & 
        (((pilot_df['forest_fraction_1km'] >= 0.2) & (pilot_df['forest_fraction_1km'] <= 0.5)) |
         ((pilot_df['cropland_fraction_1km'] >= 0.2) & (pilot_df['cropland_fraction_1km'] <= 0.5)))
    ].index.tolist()
    rng.shuffle(lc_ambig)
    for idx in lc_ambig[:5]:
        double_annot_indices.add(idx)
        
    # Industrial/mining ambiguity (near mine/quarry or distance <= 3km)
    ind_ambig = pilot_df[
        (~pilot_df.index.isin(double_annot_indices)) & 
        (pilot_df['sampling_stratum'].isin(['persistent_industrial_source', 'mining_or_other_industrial_activity'])) &
        (pilot_df['ai_confidence'] == 'MEDIUM')
    ].index.tolist()
    rng.shuffle(ind_ambig)
    for idx in ind_ambig[:5]:
        double_annot_indices.add(idx)

    # Fill remaining up to 30 from remaining pilot records with priority to MEDIUM confidence / requires review
    rem_candidates = pilot_df[~pilot_df.index.isin(double_annot_indices)].index.tolist()
    rng.shuffle(rem_candidates)
    needed = 30 - len(double_annot_indices)
    for idx in rem_candidates[:needed]:
        double_annot_indices.add(idx)
        
    pilot_df['is_double_annotation_target'] = pilot_df.index.isin(double_annot_indices)

    # 3. Format pilot_v2_records_100.json records
    records = []
    for _, row in pilot_df.iterrows():
        rec = {
            "event_id": str(row['event_id']),
            "latitude": float(row['centroid_lat']),
            "longitude": float(row['centroid_lon']),
            "timestamp": str(row['start_time']),
            "source_features": {
                "max_frp_mw": float(row['max_frp_mw']),
                "duration_hours": float(row.get('duration_hours', 0.0) or 0.0),
                "active_days_previous_30d": float(row.get('active_days_previous_30d', 0.0) or 0.0),
                "events_previous_30d": float(row.get('events_previous_30d', 0.0) or 0.0),
                "forest_fraction_1km": float(row.get('forest_fraction_1km', 0.0) or 0.0),
                "cropland_fraction_1km": float(row.get('cropland_fraction_1km', 0.0) or 0.0),
                "builtup_fraction_1km": float(row.get('builtup_fraction_1km', 0.0) or 0.0),
                "distance_to_facility_km": float(row.get('distance_to_facility_km', 999.0) if row.get('distance_to_facility_km') is not None else 999.0),
                "near_refinery": bool(row.get('near_refinery', False)),
                "near_factory": bool(row.get('near_factory', False)),
                "near_mine": bool(row.get('near_mine', False)),
                "near_quarry": bool(row.get('near_quarry', False))
            },
            "ai_assisted_v2_label": str(row['ai_assisted_label']),
            "ai_assisted_confidence": str(row['ai_confidence']),
            "ai_assisted_reasoning": str(row['reasoning_summary']),
            "human_verified_label": None,
            "annotator_1_label": None,
            "annotator_2_label": None,
            "adjudicated_label": None,
            "annotator_1_confidence": None,
            "annotator_2_confidence": None,
            "adjudicated_confidence": None,
            "annotator_1_notes": None,
            "annotator_2_notes": None,
            "adjudicated_notes": None,
            "verification_status": "unverified",
            "provenance": {
                "source_candidate_pool": "ml/data/ground_truth/candidate_pool_v1.json",
                "total_candidate_population": 1500,
                "pilot_size": 100,
                "sampling_method": "deterministic_stratified_seed_42",
                "random_seed": SEED,
                "sampling_stratum": str(row['sampling_stratum']),
                "is_double_annotation_target": bool(row['is_double_annotation_target'])
            }
        }
        records.append(rec)
        
    with open(PILOT_RECORDS_PATH, "w") as f:
        json.dump(records, f, indent=2)
        
    print(f"Saved 100 pilot records to {PILOT_RECORDS_PATH}")
    
    # 4. Create annotator_1_assignments.json (100 events)
    annotator_1 = []
    for rec in records:
        a1_rec = {
            "event_id": rec["event_id"],
            "latitude": rec["latitude"],
            "longitude": rec["longitude"],
            "timestamp": rec["timestamp"],
            "source_features": rec["source_features"],
            "ai_assisted_suggestion": rec["ai_assisted_v2_label"],
            "ai_assisted_confidence": rec["ai_assisted_confidence"],
            "annotator_id": "annotator_1",
            "is_double_annotation": rec["provenance"]["is_double_annotation_target"],
            "assigned_label": None,
            "annotator_confidence": None,
            "evidence_notes": None,
            "status": "pending"
        }
        annotator_1.append(a1_rec)
        
    with open(ANNOTATOR_1_PATH, "w") as f:
        json.dump(annotator_1, f, indent=2)
    print(f"Saved 100 assignments for Annotator 1 to {ANNOTATOR_1_PATH}")
    
    # 5. Create annotator_2_assignments.json (30 double-annotated events)
    # MUST NOT contain Annotator 1's label or notes!
    annotator_2 = []
    for rec in records:
        if rec["provenance"]["is_double_annotation_target"]:
            a2_rec = {
                "event_id": rec["event_id"],
                "latitude": rec["latitude"],
                "longitude": rec["longitude"],
                "timestamp": rec["timestamp"],
                "source_features": rec["source_features"],
                "ai_assisted_suggestion": rec["ai_assisted_v2_label"],
                "ai_assisted_confidence": rec["ai_assisted_confidence"],
                "annotator_id": "annotator_2",
                "is_double_annotation": True,
                "assigned_label": None,
                "annotator_confidence": None,
                "evidence_notes": None,
                "status": "pending"
            }
            annotator_2.append(a2_rec)
            
    with open(ANNOTATOR_2_PATH, "w") as f:
        json.dump(annotator_2, f, indent=2)
    print(f"Saved {len(annotator_2)} assignments for Annotator 2 to {ANNOTATOR_2_PATH}")

if __name__ == "__main__":
    main()
