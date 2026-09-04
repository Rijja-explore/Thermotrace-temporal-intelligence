import pandas as pd
import numpy as np
import json
import dataclasses
from scipy.stats import spearmanr
from typing import List
import time

import sys
sys.path.append("ml")
from src.classification.investigation_priority import InvestigationPrioritizer

DATA_PATH = "data/processed/features/event_features_v2.parquet"
OUTPUT_JSON = "ml/reports/robustness_metrics.json"

def top_k_overlap(list1: List[str], list2: List[str], k: int) -> float:
    set1 = set(list1[:k])
    set2 = set(list2[:k])
    return len(set1.intersection(set2)) / k

def run_experiments():
    print("Loading data...")
    df = pd.read_parquet(DATA_PATH)
    print(f"Loaded {len(df)} rows.")

    results = {}
    
    # Base setup
    base_sample_100k = df.sample(100000, random_state=42)
    base_model = InvestigationPrioritizer(ablation_group="D")
    base_model.fit(base_sample_100k)
    
    print("Scoring all events with base model...")
    # To score 1M events efficiently, we map the _deterministic_baseline and model score
    # We can use the predict methodology in bulk instead of rank_event one by one.
    # To keep it exact to the pipeline, we need a bulk ranker. Let's write a quick vectorized version that mirrors rank_event exactly.
    # Or just use model.model.decision_function directly on valid_cols.
    valid_cols = base_model.train_cols
    X_all = df[valid_cols].fillna(0)
    X_scaled = base_model.scaler.transform(X_all)
    anomaly_scores = -base_model.model.decision_function(X_scaled)
    
    # baseline vectorized
    frp = df.get("max_frp_mw", 0).fillna(0) * 0.1
    cnt = df.get("detection_count", 0).fillna(0) * 1.0
    ev_30d = df.get("events_previous_30d", 0).fillna(0) * 5.0
    fac = (df.get("distance_to_facility_km", 999).fillna(999) < 2.0).astype(float) * 20.0
    baseline_scores = frp + cnt + ev_30d + fac
    
    final_scores = baseline_scores + (anomaly_scores * 50)
    df["priority_score"] = final_scores
    
    sorted_df = df.sort_values("priority_score", ascending=False)
    base_ranks = sorted_df["event_id"].tolist()
    
    # --- A. Random Seed Changes ---
    print("Running A. Random Seed Changes...")
    seeds = [100, 999]
    seed_overlaps = {}
    for seed in seeds:
        model_s = InvestigationPrioritizer(ablation_group="D")
        model_s.model.set_params(random_state=seed)
        model_s.fit(base_sample_100k)
        as_s = -model_s.model.decision_function(base_model.scaler.transform(X_all)) # same scaler just to test IF variance
        fs_s = baseline_scores + (as_s * 50)
        df_s = df.copy()
        df_s["ps"] = fs_s
        ranks_s = df_s.sort_values("ps", ascending=False)["event_id"].tolist()
        
        seed_overlaps[f"seed_{seed}"] = {
            "top_10": top_k_overlap(base_ranks, ranks_s, 10),
            "top_50": top_k_overlap(base_ranks, ranks_s, 50),
            "top_100": top_k_overlap(base_ranks, ranks_s, 100),
            "top_500": top_k_overlap(base_ranks, ranks_s, 500)
        }
    results["random_seed_changes"] = seed_overlaps
    
    # --- B. Sampling Changes ---
    print("Running B. Sampling Changes...")
    sample_alt = df.sample(100000, random_state=84)
    model_alt = InvestigationPrioritizer(ablation_group="D")
    model_alt.fit(sample_alt)
    as_alt = -model_alt.model.decision_function(model_alt.scaler.transform(X_all))
    fs_alt = baseline_scores + (as_alt * 50)
    df_alt = df.copy()
    df_alt["ps"] = fs_alt
    ranks_alt = df_alt.sort_values("ps", ascending=False)["event_id"].tolist()
    
    corr, _ = spearmanr(final_scores, fs_alt)
    results["sampling_changes"] = {
        "top_10": top_k_overlap(base_ranks, ranks_alt, 10),
        "top_100": top_k_overlap(base_ranks, ranks_alt, 100),
        "top_500": top_k_overlap(base_ranks, ranks_alt, 500),
        "rank_correlation": float(corr)
    }

    # --- C. Temporal Holdout ---
    print("Running C. Temporal Holdout...")
    df['start_time_dt'] = pd.to_datetime(df['start_time'])
    split_date = pd.to_datetime("2026-03-01T00:00:00")
    df_hist = df[df['start_time_dt'] < split_date]
    df_fut = df[df['start_time_dt'] >= split_date]
    
    if len(df_hist) > 100000:
        hist_sample = df_hist.sample(100000, random_state=42)
    else:
        hist_sample = df_hist
        
    model_temp = InvestigationPrioritizer(ablation_group="D")
    model_temp.fit(hist_sample)
    
    X_fut = df_fut[valid_cols].fillna(0)
    as_fut = -model_temp.model.decision_function(model_temp.scaler.transform(X_fut))
    
    # score fut with historical model
    fs_fut = baseline_scores[df_fut.index] + (as_fut * 50)
    
    # compared to scoring fut with global base_model
    fs_fut_base = final_scores[df_fut.index]
    
    corr_temp, _ = spearmanr(fs_fut_base, fs_fut)
    
    df_fut_mod = df_fut.copy()
    df_fut_mod["ps"] = fs_fut
    ranks_fut = df_fut_mod.sort_values("ps", ascending=False)["event_id"].tolist()
    
    df_fut_base = df_fut.copy()
    df_fut_base["ps"] = fs_fut_base
    ranks_fut_base = df_fut_base.sort_values("ps", ascending=False)["event_id"].tolist()

    results["temporal_holdout"] = {
        "hist_train_size": len(hist_sample),
        "future_eval_size": len(df_fut),
        "top_100_overlap": top_k_overlap(ranks_fut_base, ranks_fut, 100),
        "rank_correlation": float(corr_temp)
    }

    # --- D. Missingness Sensitivity ---
    print("Running D. Missingness Sensitivity...")
    df_miss = df.copy()
    df_miss["events_previous_30d"] = np.nan
    X_miss = df_miss[valid_cols].fillna(0)
    as_miss = -base_model.model.decision_function(base_model.scaler.transform(X_miss))
    fs_miss = frp + cnt + (0 * 5.0) + fac + (as_miss * 50)
    corr_miss, _ = spearmanr(final_scores, fs_miss)
    
    df_m = df.copy()
    df_m["ps"] = fs_miss
    ranks_miss = df_m.sort_values("ps", ascending=False)["event_id"].tolist()
    
    results["missingness_sensitivity"] = {
        "rank_correlation": float(corr_miss),
        "top_100_overlap": top_k_overlap(base_ranks, ranks_miss, 100)
    }

    # --- E. Ablations ---
    print("Running E. Ablations...")
    ablation_results = {}
    for grp in ['A', 'B', 'C', 'D']:
        m = InvestigationPrioritizer(ablation_group=grp)
        m.fit(base_sample_100k)
        valid = m.train_cols
        X_g = df[valid].fillna(0)
        as_g = -m.model.decision_function(m.scaler.transform(X_g))
        fs_g = baseline_scores + (as_g * 50) # use same baseline for consistency in testing anomaly drift, or we could just use full score
        
        df_g = df.copy()
        df_g["ps"] = fs_g
        r_g = df_g.sort_values("ps", ascending=False)["event_id"].tolist()
        
        ablation_results[grp] = {
            "feature_count": len(valid),
            "top_100_overlap_with_D": top_k_overlap(base_ranks, r_g, 100)
        }
    results["ablations"] = ablation_results

    # --- F. Geographic Concentration ---
    print("Running F. Geographic Concentration...")
    top_500 = sorted_df.head(500).copy()
    # 1-degree cells
    top_500["lat_bin"] = top_500["centroid_lat"].round(0)
    top_500["lon_bin"] = top_500["centroid_lon"].round(0)
    top_500["cell"] = top_500["lat_bin"].astype(str) + "_" + top_500["lon_bin"].astype(str)
    
    cell_counts = top_500["cell"].value_counts()
    
    results["geographic_concentration"] = {
        "unique_1deg_cells_in_top_500": int(len(cell_counts)),
        "max_events_in_single_cell": int(cell_counts.max()),
        "fraction_in_largest_cell": float(cell_counts.max() / 500.0)
    }

    # --- G. Objective-Stratum / Facility Proximity Audit ---
    print("Running G. Objective Stratum Audit...")
    matched = top_500["distance_to_facility_km"] < 2.0
    high_frp = top_500["max_frp_mw"] > 100.0
    
    results["facility_proximity"] = {
        "fraction_facility_matched_in_top_500": float(matched.mean()),
        "fraction_high_frp_no_facility_in_top_500": float((high_frp & ~matched).mean())
    }
    
    # --- J. Real Event Verification ---
    print("Running J. Real Event Verification...")
    from src.classification.features import EXCLUDED_FEATURES
    raw_event_dict = df[df["event_id"] == "TT-EVT-00141704"].iloc[0].to_dict()
    safe_event_dict = {k: v for k, v in raw_event_dict.items() if not (k in EXCLUDED_FEATURES and k != 'event_id')}
    
    res_real = base_model.rank_event("TT-EVT-00141704", safe_event_dict)
    results["real_event"] = {
        "priority_score": res_real.priority_score,
        "priority_tier": res_real.priority_tier,
        "baseline_score": res_real.diagnostics["baseline_score"],
        "anomaly_score": res_real.diagnostics["anomaly_score"],
        "explanation_count": len(res_real.explanations)
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Metrics saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    run_experiments()
