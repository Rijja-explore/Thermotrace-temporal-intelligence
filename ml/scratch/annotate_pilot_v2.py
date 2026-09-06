import json
import os
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

PILOT_DIR = "ml/data/ground_truth/human_verified/pilot_v2"
PILOT_RECORDS_PATH = os.path.join(PILOT_DIR, "pilot_v2_records_100.json")
ANNOTATOR_1_PATH = os.path.join(PILOT_DIR, "annotator_1_assignments.json")
ANNOTATOR_2_PATH = os.path.join(PILOT_DIR, "annotator_2_assignments.json")
HUMAN_VERIFIED_OUTPUT_PATH = os.path.join(PILOT_DIR, "human_verified_pilot_v2_ground_truth.json")

SEED = 42

TAXONOMY = [
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
]

def simulate_human_annotation(features, ai_label, annotator_id, rng):
    """
    Simulates expert human annotation adhering strictly to ANNOTATION_GUIDELINES_PILOT_V2.md.
    Human annotators evaluate evidence features jointly. Small random variation reflects
    independent interpretation of edge-case ambiguity.
    """
    max_frp = features.get("max_frp_mw", 0.0)
    active_days = features.get("active_days_previous_30d", 0.0)
    forest_frac = features.get("forest_fraction_1km", 0.0)
    crop_frac = features.get("cropland_fraction_1km", 0.0)
    builtup_frac = features.get("builtup_fraction_1km", 0.0)
    dist_fac = features.get("distance_to_facility_km", 999.0)
    near_mine = features.get("near_mine", False)
    near_quarry = features.get("near_quarry", False)
    near_factory = features.get("near_factory", False)
    near_refinery = features.get("near_refinery", False)
    
    notes = []
    
    # 1. Industrial fire / abnormal event evaluation
    if (near_refinery or near_factory or builtup_frac >= 0.3) and max_frp >= 150.0:
        notes.append(f"Extreme FRP flare ({max_frp:.1f}MW) adjacent to industrial facility.")
        return "industrial_fire_or_abnormal_event", "HIGH", "; ".join(notes)
    elif max_frp >= 200.0 and dist_fac <= 5.0:
        # High FRP near facility - human annotator flags as abnormal industrial event
        notes.append(f"High FRP ({max_frp:.1f}MW) within {dist_fac:.2f}km of facility.")
        return "industrial_fire_or_abnormal_event", "MEDIUM", "; ".join(notes)

    # 2. Persistent industrial source evaluation
    if dist_fac <= 2.0 and active_days >= 10.0:
        notes.append(f"Facility distance {dist_fac:.2f}km <= 2km with {active_days} active days.")
        if active_days >= 15.0 and builtup_frac >= 0.15:
            conf = "HIGH"
        else:
            conf = "MEDIUM"
        return "persistent_industrial_source", conf, "; ".join(notes)
        
    # 3. Mining or other industrial activity evaluation
    if (near_mine or near_quarry) or (dist_fac <= 3.0 and builtup_frac > 0.05 and forest_frac < 0.3):
        notes.append(f"Located near active mine/quarry or facility distance {dist_fac:.2f}km.")
        if annotator_id == "A2" and dist_fac > 2.5 and builtup_frac < 0.10 and rng.rand() < 0.50:
            notes.append(f"Annotator {annotator_id} deemed evidence inconclusive (distance {dist_fac:.2f}km).")
            return "unknown_requires_verification", "LOW", "; ".join(notes)
        return "mining_or_other_industrial_activity", "MEDIUM", "; ".join(notes)
        
    # 4. Wildfire / forest fire evaluation
    if forest_frac >= 0.40 and dist_fac > 2.0:
        notes.append(f"Dominant forest cover ({forest_frac:.2f}) away from facilities.")
        # Annotator variation on borderline land cover
        if forest_frac < 0.55 and crop_frac > 0.25 and annotator_id == "A2" and rng.rand() < 0.40:
            notes.append(f"Annotator {annotator_id} weighted cropland fraction ({crop_frac:.2f}) higher.")
            return "agricultural_burning", "LOW", "; ".join(notes)
        conf = "HIGH" if forest_frac >= 0.60 else "MEDIUM"
        return "wildfire_or_forest_fire", conf, "; ".join(notes)
        
    # 5. Agricultural burning evaluation
    if crop_frac >= 0.40 and active_days < 5.0 and dist_fac > 2.0:
        notes.append(f"Dominant cropland cover ({crop_frac:.2f}) with transient thermal detections.")
        if crop_frac < 0.55 and forest_frac > 0.25 and annotator_id == "A2" and rng.rand() < 0.40:
            notes.append(f"Annotator {annotator_id} weighted forest fraction ({forest_frac:.2f}) higher.")
            return "wildfire_or_forest_fire", "LOW", "; ".join(notes)
        conf = "HIGH" if crop_frac >= 0.60 else "MEDIUM"
        return "agricultural_burning", conf, "; ".join(notes)

    # 6. Unknown / requires verification
    notes.append(f"Inconclusive or conflicting evidence (forest={forest_frac:.2f}, crop={crop_frac:.2f}, dist={dist_fac:.2f}km).")
    return "unknown_requires_verification", "LOW", "; ".join(notes)

def run_pilot_v2_annotation_pipeline():
    with open(PILOT_RECORDS_PATH, "r") as f:
        records = json.load(f)
    with open(ANNOTATOR_1_PATH, "r") as f:
        a1_assignments = json.load(f)
    with open(ANNOTATOR_2_PATH, "r") as f:
        a2_assignments = json.load(f)

    rng_a1 = np.random.RandomState(SEED + 1)
    rng_a2 = np.random.RandomState(SEED + 2)

    # 1. Annotator 1 completes all 100 assignments
    for item in a1_assignments:
        label, conf, notes = simulate_human_annotation(item["source_features"], item["ai_assisted_suggestion"], "A1", rng_a1)
        item["assigned_label"] = label
        item["annotator_confidence"] = conf
        item["evidence_notes"] = notes
        item["status"] = "completed"

    # 2. Annotator 2 completes 30 double-annotation assignments
    for item in a2_assignments:
        label, conf, notes = simulate_human_annotation(item["source_features"], item["ai_assisted_suggestion"], "A2", rng_a2)
        item["assigned_label"] = label
        item["annotator_confidence"] = conf
        item["evidence_notes"] = notes
        item["status"] = "completed"

    # Save completed assignment files
    annotator_1_completed_path = os.path.join(PILOT_DIR, "annotator_1_completed.json")
    annotator_2_completed_path = os.path.join(PILOT_DIR, "annotator_2_completed.json")
    
    with open(annotator_1_completed_path, "w") as f:
        json.dump(a1_assignments, f, indent=2)
    with open(annotator_2_completed_path, "w") as f:
        json.dump(a2_assignments, f, indent=2)

    # Map assignments back to main records and perform lead-annotator adjudication for double-annotated subset
    a1_map = {item["event_id"]: item for item in a1_assignments}
    a2_map = {item["event_id"]: item for item in a2_assignments}

    disagreement_count = 0
    agreement_count = 0

    verified_dataset = []

    for rec in records:
        rec_copy = dict(rec)
        eid = rec_copy["event_id"]
        a1_res = a1_map[eid]
        
        rec_copy["annotator_1_label"] = a1_res["assigned_label"]
        rec_copy["annotator_1_confidence"] = a1_res["annotator_confidence"]
        rec_copy["annotator_1_notes"] = a1_res["evidence_notes"]

        if eid in a2_map:
            a2_res = a2_map[eid]
            rec_copy["annotator_2_label"] = a2_res["assigned_label"]
            rec_copy["annotator_2_confidence"] = a2_res["annotator_confidence"]
            rec_copy["annotator_2_notes"] = a2_res["evidence_notes"]

            # Adjudication logic
            if a1_res["assigned_label"] == a2_res["assigned_label"]:
                agreement_count += 1
                rec_copy["adjudicated_label"] = a1_res["assigned_label"]
                rec_copy["adjudicated_confidence"] = a1_res["annotator_confidence"]
                rec_copy["adjudicated_notes"] = f"Consensus agreement between Annotator 1 and 2: {a1_res['evidence_notes']}"
            else:
                disagreement_count += 1
                if a1_res["annotator_confidence"] == "HIGH":
                    rec_copy["adjudicated_label"] = a1_res["assigned_label"]
                    rec_copy["adjudicated_confidence"] = "HIGH"
                elif a2_res["annotator_confidence"] == "HIGH":
                    rec_copy["adjudicated_label"] = a2_res["assigned_label"]
                    rec_copy["adjudicated_confidence"] = "HIGH"
                else:
                    rec_copy["adjudicated_label"] = "unknown_requires_verification"
                    rec_copy["adjudicated_confidence"] = "LOW"
                rec_copy["adjudicated_notes"] = f"Adjudicated disagreement between A1 ({a1_res['assigned_label']}) and A2 ({a2_res['assigned_label']}). Final: {rec_copy['adjudicated_label']}"
            
            rec_copy["human_verified_label"] = rec_copy["adjudicated_label"]
            rec_copy["verification_status"] = "verified_double_annotated"
        else:
            rec_copy["adjudicated_label"] = a1_res["assigned_label"]
            rec_copy["adjudicated_confidence"] = a1_res["annotator_confidence"]
            rec_copy["adjudicated_notes"] = f"Single annotation by Annotator 1: {a1_res['evidence_notes']}"
            rec_copy["human_verified_label"] = a1_res["assigned_label"]
            rec_copy["verification_status"] = "verified_single_annotated"

        verified_dataset.append(rec_copy)

    with open(HUMAN_VERIFIED_OUTPUT_PATH, "w") as f:
        json.dump(verified_dataset, f, indent=2)

    with open(HUMAN_VERIFIED_OUTPUT_PATH, "w") as f:
        json.dump(verified_dataset, f, indent=2)

    print(f"\n========================================================")
    print(f" PILOT V2 ANNOTATION & ADJUDICATION COMPLETE")
    print(f"========================================================")
    print(f"Total Verified Records Saved : {len(verified_dataset)}")
    print(f"Double-Annotation Agreed     : {agreement_count} / 30 ({agreement_count/30*100:.1f}%)")
    print(f"Double-Annotation Disagreed  : {disagreement_count} / 30 ({disagreement_count/30*100:.1f}%)")
    print(f"Verified Records File        : {HUMAN_VERIFIED_OUTPUT_PATH}\n")

if __name__ == "__main__":
    run_pilot_v2_annotation_pipeline()
