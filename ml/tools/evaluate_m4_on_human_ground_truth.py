"""
evaluate_m4_on_human_ground_truth.py

Evaluation tool for testing the selected development model (M4-B) against the canonical empirical human ground-truth dataset (N=30).
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Ensure ml is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.classification.features import APPROVED_FEATURES, validate_features
from src.classification.models import TAXONOMY_CLASSES
from sklearn.metrics import confusion_matrix, accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score

M4_B_CHECKPOINT = "ml/models/benchmark/m4_class_balance/best_m4_class_balance_variant.joblib"
HUMAN_GT_PATH = "ml/data/ground_truth/human_verified/pilot_v2/reliability/human_ground_truth_30.json"
FEATURES_PATH = "data/processed/features/event_features_v2.parquet"
REPORTS_DIR = "ml/reports/model_benchmark/m4_class_balance/reliability"

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

def run_evaluation():
    print("=" * 70)
    print(" M4-B EVALUATION ON EMPIRICAL HUMAN GROUND TRUTH (N=30)")
    print("=" * 70)

    if not os.path.exists(M4_B_CHECKPOINT):
        raise FileNotFoundError(f"Selected M4-B checkpoint missing at {M4_B_CHECKPOINT}")
    if not os.path.exists(HUMAN_GT_PATH):
        raise FileNotFoundError(f"Canonical human ground-truth file missing at {HUMAN_GT_PATH}")

    m4_b = joblib.load(M4_B_CHECKPOINT)
    with open(HUMAN_GT_PATH, "r") as f:
        gt_records = json.load(f)

    df_gt = pd.DataFrame(gt_records)
    df_features = pd.read_parquet(FEATURES_PATH)
    merged = df_gt.merge(df_features, on="event_id")

    if len(merged) != 30:
        raise ValueError(f"Expected 30 merged records, found {len(merged)}")

    feature_cols = validate_features([col for col in merged.columns if col in APPROVED_FEATURES])
    X_eval = merged[feature_cols].fillna(0)
    y_true = merged["final_adjudicated_label"].tolist()

    preds = list(m4_b.predict(X_eval))
    probs_raw = m4_b.predict_proba(X_eval)
    all_labels = sorted(TAXONOMY_CLASSES)
    probs = align_probs(probs_raw, m4_b.classes_, all_labels)
    max_probs = np.max(probs, axis=1)

    acc = float(accuracy_score(y_true, preds))
    bal_acc = float(balanced_accuracy_score(y_true, preds))
    macro_f1 = float(f1_score(y_true, preds, labels=all_labels, average="macro", zero_division=0))

    precs = precision_score(y_true, preds, labels=all_labels, average=None, zero_division=0)
    recs = recall_score(y_true, preds, labels=all_labels, average=None, zero_division=0)
    f1s = f1_score(y_true, preds, labels=all_labels, average=None, zero_division=0)
    supports = [int(sum(1 for y in y_true if y == lbl)) for lbl in all_labels]

    cm = confusion_matrix(y_true, preds, labels=all_labels).tolist()

    pred_counts = pd.Series(preds).value_counts().to_dict()
    pred_dist = {lbl: int(pred_counts.get(lbl, 0)) for lbl in all_labels}

    # Error analysis
    error_list = []
    correct_mask = []
    for idx, (eid, t, p, conf) in enumerate(zip(merged["event_id"], y_true, preds, max_probs)):
        is_corr = (t == p)
        correct_mask.append(is_corr)
        if not is_corr:
            error_list.append({
                "event_id": str(eid),
                "human_ground_truth_label": t,
                "m4_b_prediction": p,
                "confidence": float(conf),
                "is_correct": False
            })

    correct_mask = np.array(correct_mask)
    mean_conf_overall = float(np.mean(max_probs))
    mean_conf_correct = float(np.mean(max_probs[correct_mask])) if sum(correct_mask) > 0 else 0.0
    mean_conf_incorrect = float(np.mean(max_probs[~correct_mask])) if sum(~correct_mask) > 0 else 0.0

    eval_results = {
        "model_id": "M4-B",
        "checkpoint_path": M4_B_CHECKPOINT,
        "human_ground_truth_path": HUMAN_GT_PATH,
        "evaluation_provenance": "canonical_human_ground_truth_30",
        "sample_size": len(merged),
        "overall_metrics": {
            "accuracy": round(acc, 4),
            "correct_count": int(sum(correct_mask)),
            "error_count": int(len(error_list)),
            "error_rate": round(1.0 - acc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "macro_f1_6class": round(macro_f1, 4)
        },
        "per_class_metrics": {
            lbl: {
                "precision": round(float(precs[i]), 4),
                "recall": round(float(recs[i]), 4),
                "f1": round(float(f1s[i]), 4),
                "support": supports[i]
            } for i, lbl in enumerate(all_labels)
        },
        "confusion_matrix": {
            "matrix": cm,
            "row_label": "Empirical Human Ground Truth",
            "col_label": "M4-B Prediction",
            "labels": all_labels
        },
        "predicted_class_distribution": pred_dist,
        "confidence_diagnostics": {
            "overall_mean_confidence": round(mean_conf_overall, 4),
            "correct_predictions_mean_confidence": round(mean_conf_correct, 4),
            "incorrect_predictions_mean_confidence": round(mean_conf_incorrect, 4)
        },
        "error_records": error_list
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_eval_json = os.path.join(REPORTS_DIR, "empirical_m4_b_human_evaluation.json")
    with open(out_eval_json, "w") as f:
        json.dump(eval_results, f, indent=2)

    df_err = pd.DataFrame(error_list)
    out_err_csv = os.path.join(REPORTS_DIR, "m4_b_human_errors.csv")
    df_err.to_csv(out_err_csv, index=False)

    print(f"\n--- EMPIRICAL HUMAN EVALUATION METRICS (M4-B) ---")
    print(f" Sample Size (N)   : {len(merged)}")
    print(f" Accuracy          : {acc * 100:.2f}% ({sum(correct_mask)}/30)")
    print(f" Error Rate        : {(1.0 - acc) * 100:.2f}% ({len(error_list)}/30)")
    print(f" Balanced Accuracy : {bal_acc:.4f}")
    print(f" 6-Class Macro F1  : {macro_f1:.4f}")
    print(f" Mean Conf Correct : {mean_conf_correct * 100:.2f}%")
    print(f" Mean Conf Incorrect: {mean_conf_incorrect * 100:.2f}%" if len(error_list) > 0 else " Mean Conf Incorrect: N/A (0 errors)")
    print(f"--------------------------------------------------")

    print("\nPer-Class Breakdown:")
    for i, cat in enumerate(all_labels):
        print(f"  {cat:36s}: Prec={precs[i]:.4f}, Rec={recs[i]:.4f}, F1={f1s[i]:.4f}, Support={supports[i]}")

    print("\n6x6 Confusion Matrix (Rows: Human GT, Cols: M4-B Pred):")
    print(pd.DataFrame(cm, index=all_labels, columns=all_labels))

    print(f"\nSaved evaluation metrics to: {out_eval_json}")
    print(f"Saved error records to: {out_err_csv}")

    return eval_results

if __name__ == "__main__":
    run_evaluation()
