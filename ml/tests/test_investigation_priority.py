import pytest
import pandas as pd
import json
import dataclasses
from src.classification.investigation_priority import InvestigationPrioritizer, PrioritizationResult
from src.classification.explainability import ExplanationType

def get_sample_event():
    return {
        "event_id": "TT-TEST-001",
        "max_frp_mw": 150.0,
        "detection_count": 25,
        "events_previous_30d": 3,
        "distance_to_facility_km": 1.5,
        "forest_fraction_1km": 0.0,
        "cropland_fraction_1km": 0.8
    }

def test_deterministic_output():
    model = InvestigationPrioritizer(ablation_group="D")
    # Not fitted, uses baseline
    event = get_sample_event()
    res1 = model.rank_event(event["event_id"], event)
    res2 = model.rank_event(event["event_id"], event)
    
    assert res1.priority_score == res2.priority_score
    assert res1.priority_tier == res2.priority_tier
    # Verify serialization consistency
    assert json.dumps(dataclasses.asdict(res1), sort_keys=True) == json.dumps(dataclasses.asdict(res2), sort_keys=True)

def test_no_synthetic_risk_or_leakage_features_accepted():
    model = InvestigationPrioritizer()
    event = get_sample_event()
    event["baseline_risk_score"] = 99.0
    event["events_local_7d"] = 10
    
    with pytest.raises(ValueError, match="Feature rejected: explicitly excluded or identifier field"):
        model.rank_event(event["event_id"], event)

def test_no_semantic_labels_required_and_no_causal_language():
    model = InvestigationPrioritizer()
    res = model.rank_event("TT-TEST", get_sample_event())
    
    # Check that there are no probability or class fields
    assert not hasattr(res, "class_probabilities")
    assert not hasattr(res, "predicted_label")
    
    # Check explanations for factual statements only
    for exp in res.explanations:
        desc = exp.description.lower()
        assert "cause" not in desc
        assert "wildfire" not in desc
        assert "industrial" not in desc
        assert "prove" not in desc

def test_stable_ranking_with_missing_values():
    model = InvestigationPrioritizer()
    event = get_sample_event()
    del event["events_previous_30d"] # Missing feature
    
    res = model.rank_event(event["event_id"], event)
    assert res.priority_score > 0 # Still gets baseline score from max_frp_mw

def test_ablation_groups_restrict_features():
    model_A = InvestigationPrioritizer(ablation_group="A") # Thermal only
    event = get_sample_event()
    res_A = model_A.rank_event(event["event_id"], event)
    
    # A should NOT include distance_to_facility_km in explanations because it's group D
    assert not any(e.feature_name == "distance_to_facility_km" for e in res_A.explanations)
    
    model_D = InvestigationPrioritizer(ablation_group="D") # Infra included
    res_D = model_D.rank_event(event["event_id"], event)
    assert any(e.feature_name == "distance_to_facility_km" for e in res_D.explanations)

def test_baseline_exact_arithmetic():
    model = InvestigationPrioritizer(ablation_group="D")
    event = get_sample_event()
    # FRP(150)*0.1 = 15.0
    # detection_count(25)*1.0 = 25.0
    # events_previous_30d(3)*5.0 = 15.0
    # distance_to_facility_km(1.5)<2.0 = 20.0
    # Expected: 15.0 + 25.0 + 15.0 + 20.0 = 75.0
    res = model.rank_event(event["event_id"], event)
    assert res.diagnostics["baseline_score"] == 75.0
    # Check that high score corresponds to HIGH tier
    assert res.priority_tier == "HIGH"

def test_unsupervised_fit():
    model = InvestigationPrioritizer()
    df = pd.DataFrame([get_sample_event(), get_sample_event(), {"event_id":"X", "max_frp_mw":10}])
    # Should fit without labels
    model.fit(df)
    assert model.is_fitted
    
    res = model.rank_event("TT", get_sample_event())
    assert res.diagnostics["anomaly_score"] is not None
