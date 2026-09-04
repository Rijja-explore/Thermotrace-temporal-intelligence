import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.classification.features import ABLATION_GROUPS, validate_features
from src.classification.models import RandomForestWrapper
from src.classification.baseline import ThermalOnlyBaseline
from src.classification.evaluation import calculate_metrics, calculate_industrial_precision, calculate_false_positive_reduction
from src.classification.splits import unseen_facility_split

MOCK_DATA_PATH = "ml/data/mock_remote_sensing_ground_truth.json"
DATASET_PATH = "data/processed/features/event_features_v2.parquet"
OUTPUT_REPORT_PATH = "ml/reports/ablation_benchmark_results_v1.json"

def run_ablation_benchmark():
    if not os.path.exists(MOCK_DATA_PATH):
        raise FileNotFoundError(f"Mock ground truth not found: {MOCK_DATA_PATH}")
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
        
    with open(MOCK_DATA_PATH, "r") as f:
        gt_list = json.load(f)
        
    gt_df = pd.DataFrame(gt_list)
    eligible_gt = gt_df[gt_df['is_training_eligible']]
    
    df_all = pd.read_parquet(DATASET_PATH)
    merged_df = eligible_gt.merge(df_all, on="event_id")
    
    # Perform unseen-facility split
    train_df, test_df = unseen_facility_split(merged_df, test_ratio=0.3, random_state=42)
    y_train = train_df['final_label']
    y_test = test_df['final_label']
    
    # 1. Thermal Baseline Predictions for FP Reduction calculation
    baseline = ThermalOnlyBaseline(high_frp_threshold=100.0, skip_verification=True)
    baseline.fit(train_df, y_train)
    baseline_preds = baseline.predict(test_df)
    
    ablation_results = {}
    
    # Evaluate Groups A, B, C, D
    for group_key in ['A', 'B', 'C', 'D']:
        group_features = ABLATION_GROUPS[group_key]
        validated_group = validate_features([f for f in group_features if f in train_df.columns])
        
        X_train = train_df[validated_group].fillna(0)
        X_test = test_df[validated_group].fillna(0)
        
        model = RandomForestWrapper(skip_verification=True, n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)
        
        # Calculate full metrics
        metrics = calculate_metrics(
            y_true=y_test.tolist(),
            y_pred=preds.tolist(),
            y_probs=probs,
            labels=sorted(list(set(y_train.tolist() + y_test.tolist()))),
            baseline_preds=baseline_preds
        )
        
        ablation_results[group_key] = {
            "group": group_key,
            "feature_count": len(validated_group),
            "features": validated_group,
            "metrics": metrics
        }
        
    benchmark_report = {
        "status": "ABLATION_BENCHMARK_COMPLETE",
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "unseen_facility_split": True,
        "ablations": ablation_results
    }
    
    os.makedirs(os.path.dirname(OUTPUT_REPORT_PATH), exist_ok=True)
    with open(OUTPUT_REPORT_PATH, "w") as f:
        json.dump(benchmark_report, f, indent=2)
        
    print(f"Ablation benchmark complete! Results written to {OUTPUT_REPORT_PATH}")
    return benchmark_report

if __name__ == "__main__":
    run_ablation_benchmark()
