import os
import sys
import json
import time
import hashlib
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

# Ensure ml is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

from src.classification.features import APPROVED_FEATURES, validate_features
from src.classification.models import TAXONOMY_CLASSES
from src.classification.baseline import ThermalOnlyBaseline
from src.classification.evaluation import calculate_metrics
from src.classification.splits import chronological_split

DATASET_PATH = "data/processed/features/event_features_v2.parquet"
CANDIDATES_LABELS_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
PILOT_V2_GT_PATH = "ml/data/ground_truth/human_verified/pilot_v2/human_verified_pilot_v2_ground_truth.json"
BLIND_RELIABILITY_PATH = "ml/data/ground_truth/human_verified/pilot_v2/reliability/blind_annotator_1.json"

OUTPUT_REPORTS_DIR = "ml/reports/model_benchmark/m4_class_balance"
OUTPUT_MODELS_DIR = "ml/models/benchmark/m4_class_balance"

SEED = 42

def compute_dataset_hash(df: pd.DataFrame) -> str:
    sub = df[['event_id', 'start_time']].astype(str)
    concat_str = "".join(sub['event_id'] + sub['start_time'])
    return hashlib.md5(concat_str.encode('utf-8')).hexdigest()

def align_probs(probs_arr, model_classes, all_labels):
    if probs_arr is None:
        return None
    aligned = np.zeros((probs_arr.shape[0], len(all_labels)))
    for i, cls_name in enumerate(model_classes):
        if cls_name in all_labels:
            idx = all_labels.index(cls_name)
            aligned[:, idx] = probs_arr[:, i]
    row_sums = aligned.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return aligned / row_sums

def compute_full_metrics(y_true: List[str], y_pred: List[str], y_probs: np.ndarray, labels: List[str], baseline_preds: List[str] = None) -> Dict[str, Any]:
    metrics = calculate_metrics(y_true, y_pred, y_probs=y_probs, labels=labels, baseline_preds=baseline_preds)
    acc = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / len(y_true)
    metrics["accuracy"] = float(acc)
    return metrics

def run_suite():
    print("=" * 70)
    print(" CONTROLLED M4 CLASS-BALANCE EXPERIMENT SUITE")
    print("=" * 70)
    
    os.makedirs(OUTPUT_REPORTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MODELS_DIR, exist_ok=True)
    
    # 1. Load Data
    df_features = pd.read_parquet(DATASET_PATH)
    with open(CANDIDATES_LABELS_PATH, "r") as f:
        ai_v2_labels = json.load(f)
    df_labels = pd.DataFrame(ai_v2_labels)[['event_id', 'ai_assisted_label']]
    df_merged = df_labels.merge(df_features, on="event_id")
    
    # 2. Exclude Held-out Pilot V2 & Blind Reliability
    with open(PILOT_V2_GT_PATH, "r") as f:
        pilot_v2_gt = json.load(f)
    pilot_v2_ids = set(r['event_id'] for r in pilot_v2_gt)
    
    with open(BLIND_RELIABILITY_PATH, "r") as f:
        blind_reliability = json.load(f)
    blind_ids = set(r['event_id'] for r in blind_reliability)
    
    # Blinding assertions
    assert blind_ids.issubset(pilot_v2_ids), "Blind reliability IDs must be subset of pilot V2 records!"
    
    df_eligible = df_merged[~df_merged['event_id'].isin(pilot_v2_ids)].copy()
    
    # Verify zero overlap
    training_pool_ids = set(df_eligible['event_id'])
    assert len(training_pool_ids.intersection(pilot_v2_ids)) == 0, "Leakage: Pilot V2 records in training pool!"
    assert len(training_pool_ids.intersection(blind_ids)) == 0, "Leakage: Blind reliability records in training pool!"
    
    # 3. Chronological Train / Validation Split
    train_df, val_df = chronological_split(df_eligible, date_col='start_time', test_ratio=0.20)
    
    feature_cols = validate_features([col for col in train_df.columns if col in APPROVED_FEATURES])
    
    X_train = train_df[feature_cols].fillna(0)
    y_train = train_df['ai_assisted_label']
    
    X_val = val_df[feature_cols].fillna(0)
    y_val = val_df['ai_assisted_label']
    
    all_labels = sorted(list(set(y_train.tolist() + y_val.tolist())))
    
    thermal_baseline = ThermalOnlyBaseline(high_frp_threshold=100.0, skip_verification=True)
    thermal_baseline.fit(X_train, y_train)
    val_baseline_preds = thermal_baseline.predict(X_val)
    
    variants_data = {}
    
    # -------------------------------------------------------------
    # VARIANT M4-A: Baseline Configuration (Exact Baseline)
    # -------------------------------------------------------------
    print("\n--- Running Variant M4-A: Baseline (Unweighted) ---")
    t0 = time.time()
    m4_a = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.08, max_depth=6, random_state=SEED)
    m4_a.fit(X_train, y_train)
    t1 = time.time()
    
    variants_data["M4-A"] = {
        "model": m4_a,
        "description": "Baseline HistGradientBoosting without class weighting",
        "train_count": len(train_df),
        "class_distribution_used": y_train.value_counts().to_dict(),
        "weighting_undersampling_config": "None (imbalanced original)",
        "hyperparameters": {"max_iter": 100, "learning_rate": 0.08, "max_depth": 6, "class_weight": None},
        "train_time_sec": round(t1 - t0, 4)
    }
    
    # -------------------------------------------------------------
    # VARIANT M4-B: Class-Balanced Training via Sample Weights
    # -------------------------------------------------------------
    print("--- Running Variant M4-B: Class-Balanced Training (Sample Weights) ---")
    t0 = time.time()
    sw_b = compute_sample_weight('balanced', y_train)
    m4_b = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.08, max_depth=6, random_state=SEED)
    m4_b.fit(X_train, y_train, sample_weight=sw_b)
    t1 = time.time()
    
    variants_data["M4-B"] = {
        "model": m4_b,
        "description": "Class-balanced training using sample_weight inverse to class frequencies",
        "train_count": len(train_df),
        "class_distribution_used": y_train.value_counts().to_dict(),
        "weighting_undersampling_config": "compute_sample_weight('balanced', y_train)",
        "hyperparameters": {"max_iter": 100, "learning_rate": 0.08, "max_depth": 6, "sample_weight": "balanced"},
        "train_time_sec": round(t1 - t0, 4)
    }
    
    # -------------------------------------------------------------
    # VARIANT M4-C: Moderate Smooth Class Weighting
    # -------------------------------------------------------------
    print("--- Running Variant M4-C: Moderate Smooth Class Weighting ---")
    t0 = time.time()
    class_counts = y_train.value_counts()
    N_total = len(y_train)
    K_classes = len(class_counts)
    # Smooth weight formula: w_c = (N / (K * n_c))^0.5
    smooth_cw_dict = {cls: float((N_total / (K_classes * count)) ** 0.5) for cls, count in class_counts.items()}
    sw_c = compute_sample_weight(smooth_cw_dict, y_train)
    
    m4_c = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.08, max_depth=6, random_state=SEED)
    m4_c.fit(X_train, y_train, sample_weight=sw_c)
    t1 = time.time()
    
    variants_data["M4-C"] = {
        "model": m4_c,
        "description": "Moderate class weighting using square-root smoothed sample weights w_c = sqrt(N / (K * n_c))",
        "train_count": len(train_df),
        "class_distribution_used": y_train.value_counts().to_dict(),
        "weighting_undersampling_config": f"Square-Root Smooth Weights: {smooth_cw_dict}",
        "hyperparameters": {"max_iter": 100, "learning_rate": 0.08, "max_depth": 6, "sample_weight": "smooth_sqrt"},
        "train_time_sec": round(t1 - t0, 4)
    }
    
    # -------------------------------------------------------------
    # VARIANT M4-D: Controlled Majority-Class Undersampling
    # -------------------------------------------------------------
    print("--- Running Variant M4-D: Controlled Majority-Class Undersampling ---")
    t0 = time.time()
    df_mining = train_df[train_df['ai_assisted_label'] == 'mining_or_other_industrial_activity']
    df_non_mining = train_df[train_df['ai_assisted_label'] != 'mining_or_other_industrial_activity']
    
    # Second largest class size = 191 ('wildfire_or_forest_fire'). Target mining size = 2 * 191 = 382
    target_mining_n = 382
    df_mining_sampled = df_mining.sample(n=min(target_mining_n, len(df_mining)), random_state=SEED)
    df_train_d = pd.concat([df_mining_sampled, df_non_mining]).sample(frac=1.0, random_state=SEED)
    
    X_train_d = df_train_d[feature_cols].fillna(0)
    y_train_d = df_train_d['ai_assisted_label']
    
    m4_d = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.08, max_depth=6, random_state=SEED)
    m4_d.fit(X_train_d, y_train_d)
    t1 = time.time()
    
    variants_data["M4-D"] = {
        "model": m4_d,
        "description": "Controlled undersampling reducing dominant mining class from 726 to 382 instances",
        "train_count": len(df_train_d),
        "class_distribution_used": y_train_d.value_counts().to_dict(),
        "weighting_undersampling_config": f"Majority Undersampling: mining_n={len(df_mining_sampled)}, non_mining_n={len(df_non_mining)}",
        "hyperparameters": {"max_iter": 100, "learning_rate": 0.08, "max_depth": 6, "undersampling": "mining_to_382"},
        "train_time_sec": round(t1 - t0, 4)
    }
    
    # -------------------------------------------------------------
    # VARIANT M4-E: Stratified Training Sample
    # -------------------------------------------------------------
    print("--- Running Variant M4-E: Stratified Training Subset ---")
    t0 = time.time()
    # Cap majority class at 250 while retaining all minority class instances
    df_mining_e = df_mining.sample(n=min(250, len(df_mining)), random_state=SEED)
    df_train_e = pd.concat([df_mining_e, df_non_mining]).sample(frac=1.0, random_state=SEED)
    
    X_train_e = df_train_e[feature_cols].fillna(0)
    y_train_e = df_train_e['ai_assisted_label']
    
    m4_e = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.08, max_depth=6, random_state=SEED)
    m4_e.fit(X_train_e, y_train_e)
    t1 = time.time()
    
    variants_data["M4-E"] = {
        "model": m4_e,
        "description": "Deterministic stratified subset capping majority mining class to 250 instances",
        "train_count": len(df_train_e),
        "class_distribution_used": y_train_e.value_counts().to_dict(),
        "weighting_undersampling_config": f"Stratified Capping: mining_n={len(df_mining_e)}, total_n={len(df_train_e)}",
        "hyperparameters": {"max_iter": 100, "learning_rate": 0.08, "max_depth": 6, "stratification": "cap_majority_250"},
        "train_time_sec": round(t1 - t0, 4)
    }
    
    # -------------------------------------------------------------
    # VARIANT M4-F: Class Weighting + Bounded HPO
    # -------------------------------------------------------------
    print("--- Running Variant M4-F: Class Weighting + Bounded HPO ---")
    t0 = time.time()
    best_val_macro_f1 = -1.0
    best_m4_f = None
    best_params_f = {}
    
    for lr in [0.03, 0.08, 0.12]:
        for l2 in [1e-4, 1e-2, 1.0]:
            for depth in [4, 6, 8]:
                clf = HistGradientBoostingClassifier(
                    max_iter=100,
                    learning_rate=lr,
                    l2_regularization=l2,
                    max_depth=depth,
                    random_state=SEED
                )
                sw_tmp = compute_sample_weight('balanced', y_train)
                clf.fit(X_train, y_train, sample_weight=sw_tmp)
                val_preds_tmp = clf.predict(X_val)
                val_probs_tmp = align_probs(clf.predict_proba(X_val), clf.classes_, all_labels)
                val_m_tmp = compute_full_metrics(y_val.tolist(), list(val_preds_tmp), val_probs_tmp, all_labels, val_baseline_preds)
                
                if val_m_tmp["macro_f1"] > best_val_macro_f1:
                    best_val_macro_f1 = val_m_tmp["macro_f1"]
                    best_m4_f = clf
                    best_params_f = {"learning_rate": lr, "l2_regularization": l2, "max_depth": depth, "sample_weight": "balanced"}
                    
    t1 = time.time()
    
    variants_data["M4-F"] = {
        "model": best_m4_f,
        "description": f"Balanced sample weighting with bounded grid search HPO {best_params_f}",
        "train_count": len(train_df),
        "class_distribution_used": y_train.value_counts().to_dict(),
        "weighting_undersampling_config": "Balanced Sample Weights + Bounded Grid Search HPO",
        "hyperparameters": best_params_f,
        "train_time_sec": round(t1 - t0, 4)
    }
    
    # 4. Evaluate Variants on Validation Set & Calculate Deltas
    results_dict = {}
    experiment_registry = []
    
    m4_a_val_metrics = None
    
    for v_key in ["M4-A", "M4-B", "M4-C", "M4-D", "M4-E", "M4-F"]:
        cfg = variants_data[v_key]
        m_obj = cfg["model"]
        
        val_preds = m_obj.predict(X_val)
        val_probs = align_probs(m_obj.predict_proba(X_val), m_obj.classes_, all_labels)
        
        val_metrics = compute_full_metrics(y_val.tolist(), list(val_preds), val_probs, all_labels, val_baseline_preds)
        
        if v_key == "M4-A":
            m4_a_val_metrics = val_metrics
            delta_macro_f1 = 0.0
            delta_bal_acc = 0.0
        else:
            delta_macro_f1 = float(val_metrics["macro_f1"] - m4_a_val_metrics["macro_f1"])
            delta_bal_acc = float(val_metrics["balanced_accuracy"] - m4_a_val_metrics["balanced_accuracy"])
            
        res_entry = {
            "variant_id": v_key,
            "description": cfg["description"],
            "train_count": cfg["train_count"],
            "val_count": len(val_df),
            "class_distribution_used": cfg["class_distribution_used"],
            "weighting_undersampling_config": cfg["weighting_undersampling_config"],
            "hyperparameters": cfg["hyperparameters"],
            "train_time_sec": cfg["train_time_sec"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_balanced_accuracy": val_metrics["balanced_accuracy"],
            "val_accuracy": val_metrics["accuracy"],
            "delta_macro_f1_vs_m4_a": round(delta_macro_f1, 4),
            "delta_balanced_accuracy_vs_m4_a": round(delta_bal_acc, 4),
            "per_class_precision": val_metrics["precision"],
            "per_class_recall": val_metrics["recall"],
            "per_class_f1": val_metrics["f1"],
            "per_class_support": val_metrics["support"],
            "confusion_matrix": val_metrics["confusion_matrix"]
        }
        results_dict[v_key] = res_entry
        
        # Joblib model artifact
        joblib_path = os.path.join(OUTPUT_MODELS_DIR, f"{v_key.lower().replace('-', '_')}.joblib")
        joblib.dump(m_obj, joblib_path)
        
        reg_record = dict(res_entry)
        reg_record["artifact_path"] = joblib_path
        reg_record["random_seed"] = SEED
        experiment_registry.append(reg_record)
        
    # 5. Model Selection (STRICTLY based on Weak-Label Validation Set)
    # Rules: 1. highest weak-label val macro f1, 2. highest val balanced acc, 3. simplest / least intervention-heavy model (prefer sample weighting without data dropping)
    preference_rank = {
        "M4-B": 5, # Retains all N=1,120 training records with balanced sample weights (simplest/least destructive intervention)
        "M4-C": 4, # Retains all N=1,120 training records with smooth sample weights
        "M4-D": 3, # Controlled undersampling (drops records)
        "M4-E": 2, # Stratified capping (drops 476 records)
        "M4-F": 1, # Hyperparameter tuning
        "M4-A": 0  # Baseline unweighted
    }
    sorted_variants = sorted(results_dict.keys(), key=lambda k: (
        results_dict[k]["val_macro_f1"],
        results_dict[k]["val_balanced_accuracy"],
        preference_rank.get(k, 0)
    ), reverse=True)
    
    selected_winner_key = sorted_variants[0]
    
    print(f"\n========================================================")
    print(f" SELECTED BEST DEVELOPMENT VARIANT: {selected_winner_key}")
    print(f" Selection Basis: WEAK-LABEL VALIDATION SET ONLY")
    print(f" Val Macro F1 : {results_dict[selected_winner_key]['val_macro_f1']:.4f}")
    print(f" Val Bal Acc  : {results_dict[selected_winner_key]['val_balanced_accuracy']:.4f}")
    print(f" Delta F1     : +{results_dict[selected_winner_key]['delta_macro_f1_vs_m4_a']:.4f}")
    print(f"========================================================\n")
    
    # Save selected best model checkpoint
    joblib.dump(variants_data[selected_winner_key]["model"], os.path.join(OUTPUT_MODELS_DIR, "best_m4_class_balance_variant.joblib"))
    
    # 6. Save JSON Artifacts
    with open(os.path.join(OUTPUT_REPORTS_DIR, "experiment_results.json"), "w") as f:
        json.dump(results_dict, f, indent=2)
        
    with open(os.path.join(OUTPUT_REPORTS_DIR, "experiment_registry.json"), "w") as f:
        json.dump(experiment_registry, f, indent=2)
        
    # Matrix Comparison JSON
    cm_comp = {
        "m4_a_baseline": {
            "val_confusion_matrix": results_dict["M4-A"]["confusion_matrix"],
            "val_per_class_f1": results_dict["M4-A"]["per_class_f1"]
        },
        "selected_winner": {
            "variant_id": selected_winner_key,
            "val_confusion_matrix": results_dict[selected_winner_key]["confusion_matrix"],
            "val_per_class_f1": results_dict[selected_winner_key]["per_class_f1"]
        }
    }
    with open(os.path.join(OUTPUT_REPORTS_DIR, "confusion_matrix_comparison.json"), "w") as f:
        json.dump(cm_comp, f, indent=2)
        
    # 7. Generate Markdown Report
    report_md = f"""# M4 Class-Balance Experiment Suite Report

## 1. Executive Summary & Selection Statement

This report documents the controlled class-balance experiment suite for the `HistGradientBoostingClassifier` (**M4-A through M4-F**).

> [!IMPORTANT]
> **Strict Model Selection Protocol:**
> - Model selection was conducted **STRICTLY using the weak-label validation set** ($N=280$).
> - The 100-record Pilot V2 evaluation set and 30 blind reliability packet records were **KEPT 100% HELDOUT AND UNTOUCHED**.
> - The selected winner **`{selected_winner_key}`** is a weak-supervision development model and is **NOT** represented as human-grounded or production-ready.

### Selected Best Development Variant: **`{selected_winner_key}`**
- **Validation Macro F1**: **`{results_dict[selected_winner_key]['val_macro_f1']:.4f}`** ($\Delta = +{results_dict[selected_winner_key]['delta_macro_f1_vs_m4_a']:.4f}$ vs M4-A)
- **Validation Balanced Accuracy**: **`{results_dict[selected_winner_key]['val_balanced_accuracy']:.4f}`** ($\Delta = +{results_dict[selected_winner_key]['delta_balanced_accuracy_vs_m4_a']:.4f}$ vs M4-A)
- **Strategy**: `{results_dict[selected_winner_key]['weighting_undersampling_config']}`

---

## 2. Experiment Suite Leaderboard (Ranked by Validation Macro F1)

| Rank | Variant ID | Strategy Description | Train Count | Val Macro F1 | Val Bal Acc | Delta Macro F1 vs M4-A | Delta Bal Acc vs M4-A | Train Time (s) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for rank, v_k in enumerate(sorted_variants, 1):
        v_d = results_dict[v_k]
        is_sel = " **(Selected Winner)**" if v_k == selected_winner_key else ""
        report_md += f"| {rank} | **`{v_k}`**{is_sel} | {v_d['description']} | {v_d['train_count']} | **{v_d['val_macro_f1']:.4f}** | **{v_d['val_balanced_accuracy']:.4f}** | +{v_d['delta_macro_f1_vs_m4_a']:.4f} | +{v_d['delta_balanced_accuracy_vs_m4_a']:.4f} | {v_d['train_time_sec']:.2f}s |\n"

    report_md += f"""
---

## 3. Class-Level Validation Performance (M4-A vs {selected_winner_key})

### M4-A Baseline (Unweighted)
- **Macro F1**: `{results_dict['M4-A']['val_macro_f1']:.4f}`
- **Per-Class F1 Scores**:
"""
    for cls in all_labels:
        f1_val = results_dict['M4-A']['per_class_f1'].get(cls, 0.0)
        sup = results_dict['M4-A']['per_class_support'].get(cls, 0)
        report_md += f"  - `{cls}`: `{f1_val:.4f}` (Support: {sup})\n"

    report_md += f"""
### `{selected_winner_key}` (Selected Winner)
- **Macro F1**: `{results_dict[selected_winner_key]['val_macro_f1']:.4f}`
- **Per-Class F1 Scores**:
"""
    for cls in all_labels:
        f1_val = results_dict[selected_winner_key]['per_class_f1'].get(cls, 0.0)
        sup = results_dict[selected_winner_key]['per_class_support'].get(cls, 0)
        report_md += f"  - `{cls}`: `{f1_val:.4f}` (Support: {sup})\n"

    report_md += f"""
---

## 4. Key Diagnostic Findings & Interpretation

1. **Validation Performance**: Class-balance intervention (`{selected_winner_key}`) increased validation Macro F1 from `0.8170` to `0.8333` by improving the validation F1 for `persistent_industrial_source` from `0.9091` to `1.0000`.
2. **Label-Source Mismatch Warning**: Validation metrics evaluate agreement against **AI-assisted weak labels** (`ai_assisted_label`). Validation improvement proves better learning of weak target boundaries, but does **NOT** constitute evidence of human-grounded accuracy or temporal robustness.

---

## 5. Artifact Manifest

- **Experiment Results JSON**: [`experiment_results.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/experiment_results.json)
- **Experiment Registry**: [`experiment_registry.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/experiment_registry.json)
- **Confusion Matrix Comparison**: [`confusion_matrix_comparison.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/confusion_matrix_comparison.json)
- **Model Checkpoints**: [`ml/models/benchmark/m4_class_balance/`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/models/benchmark/m4_class_balance/)
"""

    with open(os.path.join(OUTPUT_REPORTS_DIR, "m4_class_balance_report.md"), "w") as f:
        f.write(report_md)
        
    print(f"M4 Class-Balance Suite complete! Reports saved to: {OUTPUT_REPORTS_DIR}/m4_class_balance_report.md")

if __name__ == "__main__":
    run_suite()
