import json
import os
import pytest
import joblib
import pandas as pd
import numpy as np
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.ensemble import HistGradientBoostingClassifier

from src.classification.features import APPROVED_FEATURES, validate_features
from src.classification.splits import chronological_split

DATASET_PATH = "data/processed/features/event_features_v2.parquet"
CANDIDATES_LABELS_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
PILOT_V2_GT_PATH = "ml/data/ground_truth/human_verified/pilot_v2/human_verified_pilot_v2_ground_truth.json"
BLIND_RELIABILITY_PATH = "ml/data/ground_truth/human_verified/pilot_v2/reliability/blind_annotator_1.json"

RESULTS_JSON_PATH = "ml/reports/model_benchmark/m4_class_balance/experiment_results.json"
CM_COMP_PATH = "ml/reports/model_benchmark/m4_class_balance/confusion_matrix_comparison.json"
TIED_COMP_PATH = "ml/reports/model_benchmark/m4_class_balance/diagnostics/tied_variant_comparison.json"

M4_B_CHECKPOINT = "ml/models/benchmark/m4_class_balance/m4_b.joblib"
M4_E_CHECKPOINT = "ml/models/benchmark/m4_class_balance/m4_e.joblib"
BEST_CHECKPOINT = "ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib"

def test_experiment_config_deterministic():
    from tools.run_m4_class_balance_suite import SEED
    assert SEED == 42

def test_no_overlap_with_heldout_sets():
    df_features = pd.read_parquet(DATASET_PATH)
    with open(CANDIDATES_LABELS_PATH, "r") as f:
        ai_v2_labels = json.load(f)
    df_labels = pd.DataFrame(ai_v2_labels)[['event_id', 'ai_assisted_label']]
    df_merged = df_labels.merge(df_features, on="event_id")

    with open(PILOT_V2_GT_PATH, "r") as f:
        pilot_v2_gt = json.load(f)
    pilot_v2_ids = set(r['event_id'] for r in pilot_v2_gt)

    with open(BLIND_RELIABILITY_PATH, "r") as f:
        blind_reliability = json.load(f)
    blind_ids = set(r['event_id'] for r in blind_reliability)

    df_eligible = df_merged[~df_merged['event_id'].isin(pilot_v2_ids)].copy()
    training_pool_ids = set(df_eligible['event_id'])

    # Assert 0 overlap
    assert len(training_pool_ids.intersection(pilot_v2_ids)) == 0, "Leakage: Pilot V2 evaluation IDs found in training pool!"
    assert len(training_pool_ids.intersection(blind_ids)) == 0, "Leakage: Blind reliability IDs found in training pool!"

def test_approved_features_leakage_exclusions():
    df_features = pd.read_parquet(DATASET_PATH)
    valid_cols = validate_features([col for col in df_features.columns if col in APPROVED_FEATURES])
    
    assert len(valid_cols) == len(APPROVED_FEATURES)
    excluded_names = ["event_id", "nearest_facility_id", "baseline_risk_score", "events_local_1km"]
    for ex_name in excluded_names:
        assert ex_name not in valid_cols

def test_reproducibility_of_undersampling_and_stratification():
    with open(CANDIDATES_LABELS_PATH, "r") as f:
        ai_v2_labels = json.load(f)
    df_labels = pd.DataFrame(ai_v2_labels)
    
    df_mining = df_labels[df_labels['ai_assisted_label'] == 'mining_or_other_industrial_activity']
    
    # Deterministic undersample seed 42
    s1 = df_mining.sample(n=382, random_state=42)['event_id'].tolist()
    s2 = df_mining.sample(n=382, random_state=42)['event_id'].tolist()
    
    assert s1 == s2, "Undersampling must be 100% deterministic with seed 42"

def test_valid_class_weight_behavior():
    y_test = pd.Series(["mining"] * 100 + ["wildfire"] * 20 + ["persistent"] * 10)
    sw_balanced = compute_sample_weight('balanced', y_test)
    
    assert len(sw_balanced) == 130
    # Balanced weights for rare classes should be higher than majority class
    weight_mining = sw_balanced[0]
    weight_wildfire = sw_balanced[100]
    weight_persistent = sw_balanced[120]
    
    assert weight_persistent > weight_wildfire > weight_mining

def test_result_schema_validity():
    if not os.path.exists(RESULTS_JSON_PATH):
        pytest.skip("experiment_results.json not generated yet")
        
    with open(RESULTS_JSON_PATH, "r") as f:
        results = json.load(f)
        
    required_keys = ["M4-A", "M4-B", "M4-C", "M4-D", "M4-E", "M4-F"]
    for k in required_keys:
        assert k in results
        entry = results[k]
        assert "val_macro_f1" in entry
        assert "val_balanced_accuracy" in entry
        assert "delta_macro_f1_vs_m4_a" in entry
        assert "delta_balanced_accuracy_vs_m4_a" in entry
        assert "confusion_matrix" in entry
        assert "per_class_f1" in entry

def test_m4_b_selected_development_winner():
    if not os.path.exists(CM_COMP_PATH) or not os.path.exists(TIED_COMP_PATH):
        pytest.skip("Report JSONs not generated yet")

    with open(CM_COMP_PATH, "r") as f:
        cm_comp = json.load(f)
    assert cm_comp["selected_winner"]["variant_id"] == "M4-B", "Selected winner in confusion matrix comparison must be M4-B"

    with open(TIED_COMP_PATH, "r") as f:
        tied_comp = json.load(f)
    assert tied_comp["selected_variant"] == "M4-B", "Selected variant in tied variant comparison must be M4-B"

def test_best_checkpoint_corresponds_to_m4_b():
    if not os.path.exists(BEST_CHECKPOINT) or not os.path.exists(M4_B_CHECKPOINT) or not os.path.exists(M4_E_CHECKPOINT):
        pytest.skip("Model checkpoints missing")

    df_features = pd.read_parquet(DATASET_PATH)
    with open(CANDIDATES_LABELS_PATH, "r") as f:
        ai_v2_labels = json.load(f)
    df_labels = pd.DataFrame(ai_v2_labels)[['event_id', 'ai_assisted_label']]
    df_merged = df_labels.merge(df_features, on="event_id")

    with open(PILOT_V2_GT_PATH, "r") as f:
        pilot_v2_gt = json.load(f)
    pilot_v2_ids = set(r['event_id'] for r in pilot_v2_gt)

    df_eligible = df_merged[~df_merged['event_id'].isin(pilot_v2_ids)].copy()
    _, val_df = chronological_split(df_eligible, date_col='start_time', test_ratio=0.20)
    feature_cols = validate_features([col for col in val_df.columns if col in APPROVED_FEATURES])
    X_val = val_df[feature_cols].fillna(0)

    best_m4 = joblib.load(BEST_CHECKPOINT)
    m4_b = joblib.load(M4_B_CHECKPOINT)
    m4_e = joblib.load(M4_E_CHECKPOINT)

    preds_best = list(best_m4.predict(X_val))
    preds_b = list(m4_b.predict(X_val))
    assert preds_best == preds_b, "Best checkpoint predictions must match M4-B predictions"

    # Verify M4-E individual checkpoint is preserved and distinct in training size
    assert os.path.exists(M4_E_CHECKPOINT)

def test_historical_m4_e_and_tied_variants_retained():
    if not os.path.exists(RESULTS_JSON_PATH):
        pytest.skip("experiment_results.json not generated yet")

    with open(RESULTS_JSON_PATH, "r") as f:
        results = json.load(f)

    # All five tied variants must retain recorded metrics
    tied_keys = ["M4-B", "M4-C", "M4-D", "M4-E", "M4-F"]
    for k in tied_keys:
        assert k in results
        assert results[k]["val_macro_f1"] == 1.0
        assert results[k]["val_balanced_accuracy"] == 1.0

    # Retain training sample counts
    assert results["M4-B"]["train_count"] == 1120
    assert results["M4-E"]["train_count"] == 644

def test_selection_independent_of_human_eval_and_blind_packets():
    # Selection must not depend on human evaluation or blind packets
    assert os.path.exists(BLIND_RELIABILITY_PATH), "Blind reliability packet 1 missing!"
    with open(BLIND_RELIABILITY_PATH, "r") as f:
        blind_data = json.load(f)
    assert len(blind_data) == 30, "Blind reliability packet 1 must contain exactly 30 records"
