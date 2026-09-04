import pytest
import json
import dataclasses
from src.classification.explainability import ExplanationRecord, ObservationSummarizer, ModelExplanationInterface, ExplanationType
from src.classification.prediction import fail_prediction, VerificationState

def test_observation_generation_factual():
    features = {
        "max_frp_mw": 120.5,
        "duration_hours": 48.0,
        "events_previous_30d": 3,
        "cropland_fraction_1km": 0.85,
        "distance_to_major_road_km": 1.2
    }
    obs = ObservationSummarizer.summarize(features)
    assert len(obs) == 5
    
    # Check max_frp_mw
    frp_obs = next(o for o in obs if o.feature_name == "max_frp_mw")
    assert frp_obs.explanation_type == ExplanationType.OBSERVATION
    assert frp_obs.unit == "MW"
    assert frp_obs.description == "Maximum observed FRP was 120.5 MW."
    
    # Check cropland fraction
    crop_obs = next(o for o in obs if o.feature_name == "cropland_fraction_1km")
    assert crop_obs.unit == "percent"
    assert crop_obs.description == "The mapped cropland land-cover fraction is 0.85."

def test_excluded_feature_rejection():
    # Should throw ValueError from validate_features
    features = {
        "max_frp_mw": 120.5,
        "baseline_risk_score": 90.0, # Excluded synthetic risk
        "events_local_7d": 1 # Excluded leaky density
    }
    with pytest.raises(ValueError, match="Invalid feature schema" if False else "rejected"):
        ObservationSummarizer.summarize(features)

def test_no_causal_language():
    features = {
        "max_frp_mw": 120.5,
        "duration_hours": 48.0,
        "near_factory": 1
    }
    obs = ObservationSummarizer.summarize(features)
    for o in obs:
        desc = o.description.lower()
        # Ensure causal language is absent
        assert "caused" not in desc
        assert "proves" not in desc
        assert "wildfire" not in desc
        assert "industrial" not in desc

def test_model_explanation_unavailable_when_untrained():
    exps = ModelExplanationInterface.generate_explanation(model=None, lifecycle_state="NOT_TRAINED", features={"max_frp_mw": 50})
    assert len(exps) == 0

def test_confidence_separation_and_verification_status():
    pred = fail_prediction("TT-123")
    assert pred.model_confidence is None
    assert pred.evidence_confidence is None
    assert pred.data_quality.value == "UNKNOWN"
    assert pred.verification_state == VerificationState.MODEL_NOT_AVAILABLE
    
def test_json_serialization():
    pred = fail_prediction("TT-123")
    pred_dict = dataclasses.asdict(pred)
    json_str = json.dumps(pred_dict)
    assert "MODEL_NOT_AVAILABLE" in json_str
    assert "model_confidence" in json_str
    assert "evidence_confidence" in json_str
