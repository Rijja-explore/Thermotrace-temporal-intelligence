import json
import os
import pytest
import joblib
import pandas as pd
import numpy as np

from src.classification.features import APPROVED_FEATURES, validate_features
from src.classification.splits import chronological_split

DATASET_PATH = "data/processed/features/event_features_v2.parquet"
CANDIDATES_LABELS_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
PILOT_V2_GT_PATH = "ml/data/ground_truth/human_verified/pilot_v2/human_verified_pilot_v2_ground_truth.json"
BLIND_RELIABILITY_PATH = "ml/data/ground_truth/human_verified/pilot_v2/reliability/blind_annotator_1.json"

M4_A_PATH = "ml/models/benchmark/m4_class_balance/m4_a.joblib"
M4_B_PATH = "ml/models/benchmark/m4_class_balance/m4_b.joblib"
M4_E_PATH = "ml/models/benchmark/m4_class_balance/m4_e.joblib"
BEST_M4_PATH = "ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib"
ERROR_CSV_PATH = "ml/reports/model_benchmark/m4_class_balance/diagnostics/error_comparison.csv"

def get_val_df():
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
    return val_df

def test_same_validation_ids_and_count():
    val_df = get_val_df()
    assert len(val_df) == 280
    assert val_df['event_id'].nunique() == 280

def test_no_pilot_v2_or_blind_reliability_overlap():
    val_df = get_val_df()
    val_ids = set(val_df['event_id'])

    with open(PILOT_V2_GT_PATH, "r") as f:
        pilot_v2_gt = json.load(f)
    pilot_v2_ids = set(r['event_id'] for r in pilot_v2_gt)

    with open(BLIND_RELIABILITY_PATH, "r") as f:
        blind_reliability = json.load(f)
    blind_ids = set(r['event_id'] for r in blind_reliability)

    assert len(val_ids.intersection(pilot_v2_ids)) == 0, "Leakage: Validation set contains Pilot V2 IDs!"
    assert len(val_ids.intersection(blind_ids)) == 0, "Leakage: Validation set contains blind reliability IDs!"

def test_approved_feature_set_consistency():
    val_df = get_val_df()
    feature_cols = validate_features([col for col in val_df.columns if col in APPROVED_FEATURES])
    assert len(feature_cols) == len(APPROVED_FEATURES)

def test_deterministic_predictions_for_m4_a_b_and_e():
    if not os.path.exists(M4_A_PATH) or not os.path.exists(M4_B_PATH) or not os.path.exists(M4_E_PATH) or not os.path.exists(BEST_M4_PATH):
        pytest.skip("Model checkpoints not available")
        
    val_df = get_val_df()
    feature_cols = validate_features([col for col in val_df.columns if col in APPROVED_FEATURES])
    X_val = val_df[feature_cols].fillna(0)

    m4_a = joblib.load(M4_A_PATH)
    m4_b = joblib.load(M4_B_PATH)
    m4_e = joblib.load(M4_E_PATH)
    best_m4 = joblib.load(BEST_M4_PATH)

    preds_a1 = list(m4_a.predict(X_val))
    preds_a2 = list(m4_a.predict(X_val))
    assert preds_a1 == preds_a2, "M4-A predictions must be deterministic"

    preds_b1 = list(m4_b.predict(X_val))
    preds_b2 = list(m4_b.predict(X_val))
    assert preds_b1 == preds_b2, "M4-B predictions must be deterministic"

    preds_e1 = list(m4_e.predict(X_val))
    preds_e2 = list(m4_e.predict(X_val))
    assert preds_e1 == preds_e2, "M4-E predictions must be deterministic"

    preds_best = list(best_m4.predict(X_val))
    assert preds_best == preds_b1, "Best checkpoint predictions must match M4-B"

def test_error_comparison_correctness():
    if not os.path.exists(ERROR_CSV_PATH):
        pytest.skip("error_comparison.csv not generated yet")

    df_err = pd.read_csv(ERROR_CSV_PATH)
    assert len(df_err) == 280
    assert list(df_err.columns) == [
        "event_id", "start_time", "true_weak_label", "m4_a_pred", "m4_b_pred", "m4_e_pred",
        "m4_a_correct", "m4_b_correct", "m4_e_correct",
        "m4_b_fixed_error", "m4_b_introduced_error",
        "m4_e_fixed_error", "m4_e_introduced_error"
    ]

    for _, r in df_err.iterrows():
        assert r['m4_a_correct'] == (r['true_weak_label'] == r['m4_a_pred'])
        assert r['m4_b_correct'] == (r['true_weak_label'] == r['m4_b_pred'])
        assert r['m4_e_correct'] == (r['true_weak_label'] == r['m4_e_pred'])
        assert r['m4_b_fixed_error'] == ((not r['m4_a_correct']) and r['m4_b_correct'])
        assert r['m4_b_introduced_error'] == (r['m4_a_correct'] and (not r['m4_b_correct']))
