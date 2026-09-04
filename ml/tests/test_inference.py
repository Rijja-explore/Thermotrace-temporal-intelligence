import pytest
import json
import dataclasses
from src.classification.inference import adapt_inference_event
from src.classification.prediction import PredictionStatus, ModelLifecycleState, VerificationState
from src.classification.explainability import ExplanationType

def test_inference_adapter_valid():
    event = {"event_id": "TT-001", "max_frp_mw": 50.0}
    pred = adapt_inference_event(event)
    assert pred.event_id == "TT-001"
    assert pred.prediction_status == PredictionStatus.MODEL_NOT_TRAINED_NO_VERIFIED_LABELS
    assert pred.predicted_label == "unknown_requires_verification"
    assert pred.verification_state == VerificationState.MODEL_NOT_AVAILABLE
    assert pred.model_version == "UNTRAINED"
    assert pred.class_probabilities == {}
    assert len(pred.explanations) == 1
    assert pred.explanations[0].explanation_type == ExplanationType.OBSERVATION
    assert pred.explanations[0].feature_name == "max_frp_mw"
    assert pred.explanations[0].feature_value == 50.0

def test_inference_adapter_missing_id():
    event = {"max_frp_mw": 50.0}
    with pytest.raises(ValueError, match="Missing event_id"):
        adapt_inference_event(event)

def test_inference_adapter_invalid_feature():
    # 'start_time' and 'metadata_flag' are unknown/operational features, not explicitly leaky.
    # They should be safely dropped without triggering the explicit leakage validation.
    event = {"event_id": "TT-001", "max_frp_mw": 50.0, "start_time": "2025-01-01", "metadata_flag": 1.0}
    pred = adapt_inference_event(event)
    # The operational features should not be in the observations
    assert not any(obs.feature_name == "start_time" for obs in pred.explanations)
    assert not any(obs.feature_name == "metadata_flag" for obs in pred.explanations)
    assert any(obs.feature_name == "max_frp_mw" for obs in pred.explanations)

def test_inference_adapter_leakage_feature():
    # Explicit leakage feature 'events_local_7d' MUST trigger a strict validation crash,
    # proving the adapter does not silently discard prohibited variables.
    event = {"event_id": "TT-001", "max_frp_mw": 50.0, "events_local_7d": 5}
    with pytest.raises(ValueError, match="Invalid feature schema"):
        adapt_inference_event(event)

def test_inference_adapter_synthetic_risk_leakage():
    # Synthetic risk must also trigger explicit crash
    event = {"event_id": "TT-001", "max_frp_mw": 50.0, "baseline_risk_score": 99.0}
    with pytest.raises(ValueError, match="Invalid feature schema"):
        adapt_inference_event(event)

def test_prediction_contract_serialization():
    event = {"event_id": "TT-001", "max_frp_mw": 50.0}
    pred = adapt_inference_event(event)
    pred_dict = dataclasses.asdict(pred)
    json_str = json.dumps(pred_dict)
    assert "MODEL_NOT_TRAINED_NO_VERIFIED_LABELS" in json_str
    assert "UNTRAINED" in json_str
    assert "OBSERVATION" in json_str
    assert "MODEL_NOT_AVAILABLE" in json_str
    
def test_model_lifecycle_states():
    assert ModelLifecycleState.NOT_TRAINED.value == "NOT_TRAINED"
    assert ModelLifecycleState.TRAINED_UNVALIDATED.value == "TRAINED_UNVALIDATED"
    assert ModelLifecycleState.TRAINED_VALIDATED.value == "TRAINED_VALIDATED"
    assert ModelLifecycleState.RETIRED.value == "RETIRED"

def test_contract_probabilities_and_evidence():
    event = {"event_id": "TT-001", "max_frp_mw": 50.0}
    pred = adapt_inference_event(event)
    assert pred.class_probabilities == {}
    assert pred.evidence == []
    
def test_contract_determinism():
    event = {"event_id": "TT-001", "max_frp_mw": 50.0, "duration_hours": 12.0}
    pred1 = adapt_inference_event(event)
    pred2 = adapt_inference_event(event)
    j1 = json.dumps(dataclasses.asdict(pred1), sort_keys=True)
    j2 = json.dumps(dataclasses.asdict(pred2), sort_keys=True)
    assert j1 == j2

def test_future_trained_payload_structure():
    # Test that the contract can structurally represent a future trained prediction
    from src.classification.prediction import PredictionContract, DataQuality
    pred = PredictionContract(
        event_id="TT-001",
        prediction_status=PredictionStatus.PREDICTION_AVAILABLE,
        predicted_label="persistent_industrial_source",
        model_confidence=0.95,
        evidence_confidence=None,
        data_quality=DataQuality.HIGH,
        class_probabilities={"persistent_industrial_source": 0.95, "unknown_requires_verification": 0.05},
        evidence=[],
        explanations=[],
        model_version="v1.0",
        prediction_timestamp="2025-01-01T00:00:00Z",
        verification_state=VerificationState.MODEL_PREDICTION_REQUIRES_VERIFICATION
    )
    assert pred.model_confidence == 0.95
    assert "persistent_industrial_source" in pred.class_probabilities

def test_invalid_lifecycle_states_rejected():
    with pytest.raises(ValueError):
        ModelLifecycleState("INVALID_STATE")
