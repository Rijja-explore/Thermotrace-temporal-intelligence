import pytest
from evaluation.human_reliability_tool import (
    validate_reliability_inputs,
    calculate_human_inter_annotator_reliability,
    ALLOWED_TAXONOMY
)

def make_mock_record(event_id: str, label: str, conf: str = "HIGH", notes: str = "Clear evidence"):
    return {
        "event_id": event_id,
        "assigned_label": label,
        "confidence": conf,
        "evidence_notes": notes
    }

def test_validate_reliability_inputs_valid():
    a1 = [make_mock_record(f"TT-EVT-{i:06d}", ALLOWED_TAXONOMY[i % len(ALLOWED_TAXONOMY)]) for i in range(30)]
    a2 = [make_mock_record(f"TT-EVT-{i:06d}", ALLOWED_TAXONOMY[i % len(ALLOWED_TAXONOMY)]) for i in range(30)]
    
    val1, val2 = validate_reliability_inputs(a1, a2, expected_count=30)
    assert len(val1) == 30
    assert len(val2) == 30

def test_validate_reliability_inputs_mismatched_count():
    a1 = [make_mock_record(f"TT-EVT-{i:06d}", "agricultural_burning") for i in range(30)]
    a2 = [make_mock_record(f"TT-EVT-{i:06d}", "agricultural_burning") for i in range(29)]
    
    with pytest.raises(ValueError, match="Annotator 2 record count mismatch"):
        validate_reliability_inputs(a1, a2, expected_count=30)

def test_validate_reliability_inputs_duplicate_ids():
    a1 = [make_mock_record(f"TT-EVT-{i:06d}", "agricultural_burning") for i in range(30)]
    a1[1]["event_id"] = a1[0]["event_id"] # duplicate
    a2 = [make_mock_record(f"TT-EVT-{i:06d}", "agricultural_burning") for i in range(30)]
    
    with pytest.raises(ValueError, match="Annotator 1 file contains duplicate event_ids"):
        validate_reliability_inputs(a1, a2, expected_count=30)

def test_validate_reliability_inputs_invalid_label():
    a1 = [make_mock_record(f"TT-EVT-{i:06d}", "agricultural_burning") for i in range(30)]
    a2 = [make_mock_record(f"TT-EVT-{i:06d}", "agricultural_burning") for i in range(30)]
    a2[5]["assigned_label"] = "invalid_class_label"
    
    with pytest.raises(ValueError, match="Invalid taxonomy label"):
        validate_reliability_inputs(a1, a2, expected_count=30)

def test_calculate_human_inter_annotator_reliability_perfect_agreement():
    a1 = [make_mock_record(f"TT-EVT-{i:06d}", ALLOWED_TAXONOMY[i % len(ALLOWED_TAXONOMY)]) for i in range(30)]
    a2 = [make_mock_record(f"TT-EVT-{i:06d}", ALLOWED_TAXONOMY[i % len(ALLOWED_TAXONOMY)]) for i in range(30)]
    
    res = calculate_human_inter_annotator_reliability(a1, a2, expected_count=30)
    assert res["raw_agreement_rate"] == 1.0
    assert res["cohens_kappa"] == 1.0
    assert res["agreed_count"] == 30
    assert len(res["disagreement_records"]) == 0

def test_calculate_human_inter_annotator_reliability_with_disagreements():
    a1 = [make_mock_record(f"TT-EVT-{i:06d}", "wildfire_or_forest_fire") for i in range(30)]
    a2 = [make_mock_record(f"TT-EVT-{i:06d}", "wildfire_or_forest_fire") for i in range(30)]
    
    # Introduce 5 disagreements
    for k in range(5):
        a2[k]["assigned_label"] = "agricultural_burning"
        
    res = calculate_human_inter_annotator_reliability(a1, a2, expected_count=30)
    assert res["agreed_count"] == 25
    assert res["disagreed_count"] == 5
    assert len(res["disagreement_records"]) == 5
    assert res["raw_agreement_rate"] == pytest.approx(25 / 30)
