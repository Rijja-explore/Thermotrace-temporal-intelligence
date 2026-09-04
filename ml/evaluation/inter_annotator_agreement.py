import json
import os
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

TAXONOMY = [
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
]

def calculate_inter_annotator_agreement(
    annotator_1_path="ml/data/ground_truth/human_verified/pilot_v2/annotator_1_assignments.json",
    annotator_2_path="ml/data/ground_truth/human_verified/pilot_v2/annotator_2_assignments.json"
):
    """
    Calculates inter-annotator agreement (Cohen's kappa, raw agreement, disagreement matrix)
    for double-annotated records.
    """
    a1_completed = "ml/data/ground_truth/human_verified/pilot_v2/annotator_1_completed.json"
    a2_completed = "ml/data/ground_truth/human_verified/pilot_v2/annotator_2_completed.json"
    
    if os.path.exists(a1_completed):
        annotator_1_path = a1_completed
    if os.path.exists(a2_completed):
        annotator_2_path = a2_completed
        
    if not os.path.exists(annotator_1_path) or not os.path.exists(annotator_2_path):
        return {
            "status": "error",
            "message": "Assignment files missing."
        }

    with open(annotator_1_path, "r") as f:
        a1_data = json.load(f)
    with open(annotator_2_path, "r") as f:
        a2_data = json.load(f)

    a1_map = {item["event_id"]: item for item in a1_data}
    a2_map = {item["event_id"]: item for item in a2_data}

    common_ids = sorted(list(set(a1_map.keys()).intersection(set(a2_map.keys()))))

    labels_a1 = []
    labels_a2 = []
    unlabeled_count = 0

    for eid in common_ids:
        l1 = a1_map[eid].get("assigned_label")
        l2 = a2_map[eid].get("assigned_label")

        if l1 is None or l2 is None:
            unlabeled_count += 1
        else:
            labels_a1.append(l1)
            labels_a2.append(l2)

    total_double_records = len(common_ids)
    completed_pairs = len(labels_a1)

    print("\n========================================================")
    print(" INTER-ANNOTATOR AGREEMENT EVALUATION (PILOT V2)")
    print("========================================================")
    print(f"Total Double-Annotated Records Target: {total_double_records}")
    print(f"Completed Double-Annotation Pairs   : {completed_pairs}")
    print(f"Pending/Unlabeled Double Pairs       : {unlabeled_count}\n")

    if completed_pairs < total_double_records or completed_pairs == 0:
        print("[NOTICE] Inter-annotator agreement (Cohen's kappa) is NOT yet computable.")
        print("Reason: No human-verified labels exist until annotators complete their assigned tasks.")
        print(f"Status: Pilot records are prepared for human verification; {completed_pairs}/{total_double_records} double annotations complete.\n")
        return {
            "status": "pending_human_annotation",
            "total_double_records": total_double_records,
            "completed_pairs": completed_pairs,
            "cohens_kappa": None,
            "raw_agreement": None,
            "disagreement_matrix": None
        }

    # If completed pairs exist:
    kappa = cohen_kappa_score(labels_a1, labels_a2, labels=TAXONOMY)
    raw_agreement = sum(1 for x, y in zip(labels_a1, labels_a2) if x == y) / completed_pairs
    cm = confusion_matrix(labels_a1, labels_a2, labels=TAXONOMY)
    cm_df = pd.DataFrame(cm, index=TAXONOMY, columns=TAXONOMY)

    print(f"Cohen's Kappa Score : {kappa:.4f}")
    print(f"Raw Agreement       : {raw_agreement * 100:.2f}% ({sum(1 for x, y in zip(labels_a1, labels_a2) if x == y)} / {completed_pairs})")
    print("\nDisagreement Matrix (Annotator 1 Rows vs Annotator 2 Columns):")
    print(cm_df)

    return {
        "status": "complete",
        "total_double_records": total_double_records,
        "completed_pairs": completed_pairs,
        "cohens_kappa": float(kappa),
        "raw_agreement": float(raw_agreement),
        "disagreement_matrix": cm_df.to_dict()
    }

if __name__ == "__main__":
    calculate_inter_annotator_agreement()
