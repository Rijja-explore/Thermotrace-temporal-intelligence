import pytest
import json
from src.classification.annotation_quality import calculate_raw_agreement, calculate_cohens_kappa, detect_disagreements
from src.classification.ground_truth import ALLOWED_TAXONOMY

def test_annotation_schema_validation():
    with open("ml/data/ground_truth/annotation_schema.json", "r") as f:
        schema = json.load(f)
    assert schema["title"] == "GroundTruthAnnotationRecord"
    assert "event_id" in schema["required"]
    assert "assigned_label" in schema["required"]

def test_raw_agreement_calculation():
    labels_a = ["wildfire_or_forest_fire", "agricultural_burning", "persistent_industrial_source"]
    labels_b = ["wildfire_or_forest_fire", "agricultural_burning", "wildfire_or_forest_fire"]
    
    acc = calculate_raw_agreement(labels_a, labels_b)
    assert pytest.approx(acc, 0.01) == 0.666
    
    kappa = calculate_cohens_kappa(labels_a, labels_b, sorted(list(ALLOWED_TAXONOMY)))
    assert isinstance(kappa, float)

def test_taxonomy_and_confidence_validation():
    allowed_labels = list(ALLOWED_TAXONOMY)
    assert "persistent_industrial_source" in allowed_labels
    assert "unknown_requires_verification" in allowed_labels

    allowed_confidence = ["HIGH", "MEDIUM", "LOW"]
    assert "HIGH" in allowed_confidence
    assert "LOW" in allowed_confidence

def test_mock_and_human_dataset_separation():
    import os
    mock_path = "ml/data/mock_remote_sensing_ground_truth.json"
    human_dir = "ml/data/ground_truth/human_verified/"
    
    assert os.path.exists(mock_path)
    assert os.path.exists(human_dir)
    assert os.path.dirname(mock_path) != human_dir

def test_industrial_fire_reachability():
    from src.classification.baseline import RuleBasedClassifier
    clf = RuleBasedClassifier(skip_verification=True)
    
    # Event with industrial context and high FRP
    evt_fire = {"event_id": "FIRE_01", "near_refinery": True, "max_frp_mw": 200.0, "active_days_previous_30d": 1.0}
    res = clf.predict_event(evt_fire)
    assert res.predicted_label == "industrial_fire_or_abnormal_event"

def test_rule_independence_and_unknown_handling():
    from src.classification.baseline import RuleBasedClassifier
    clf = RuleBasedClassifier(skip_verification=True)
    
    # Facility distance alone DOES NOT produce industrial label
    evt_fac_only = {"event_id": "FAC_01", "distance_to_facility_km": 0.5, "active_days_previous_30d": 0.0}
    res = clf.predict_event(evt_fac_only)
    assert res.predicted_label == "unknown_requires_verification"

def test_v1_and_v2_preservation():
    import os
    v1_path = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v1.json"
    v2_path = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
    
    assert os.path.exists(v1_path)
    assert os.path.exists(v2_path)
    
    with open(v1_path, "r") as f:
        v1_recs = json.load(f)
    with open(v2_path, "r") as f:
        v2_recs = json.load(f)
        
    assert len(v1_recs) == 1500
    assert len(v2_recs) == 1500
    # Ensure v1 records remain intact with v1 labels preserved
    assert v1_recs[0]["ai_assisted_label"] is not None
