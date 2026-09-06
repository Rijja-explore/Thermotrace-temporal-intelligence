import pytest
import pandas as pd
import json
from pathlib import Path
from src.label_validation import LabelValidator

@pytest.fixture
def temp_label_schema(tmp_path):
    schema = {
        "allowed_labels": ["fire", "unknown_requires_verification"],
        "required_fields": ["event_id", "final_label"],
        "confidence_values": ["HIGH", "LOW"],
        "evidence_requirements": {
            "evidence_urls_required_if_not_unknown": True
        }
    }
    schema_path = tmp_path / "label_schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f)
    return schema_path

def test_empty_labels(temp_label_schema):
    validator = LabelValidator(temp_label_schema)
    df = pd.DataFrame()
    canon_df = pd.DataFrame({"event_id": ["E1"]})
    errors = validator.validate_labels(df, canon_df)
    assert "Labels dataset is empty." in errors

def test_missing_required_field(temp_label_schema):
    validator = LabelValidator(temp_label_schema)
    df = pd.DataFrame({"event_id": ["E1"]}) # Missing final_label
    canon_df = pd.DataFrame({"event_id": ["E1"]})
    errors = validator.validate_labels(df, canon_df)
    assert any("Missing required field: final_label" in e for e in errors)

def test_invalid_taxonomy(temp_label_schema):
    validator = LabelValidator(temp_label_schema)
    df = pd.DataFrame({"event_id": ["E1"], "final_label": ["not_a_fire"]})
    canon_df = pd.DataFrame({"event_id": ["E1"]})
    errors = validator.validate_labels(df, canon_df)
    assert any("Invalid final_label 'not_a_fire'" in e for e in errors)

def test_missing_evidence(temp_label_schema):
    validator = LabelValidator(temp_label_schema)
    df = pd.DataFrame({"event_id": ["E1"], "final_label": ["fire"], "evidence_urls": [""]})
    canon_df = pd.DataFrame({"event_id": ["E1"]})
    errors = validator.validate_labels(df, canon_df)
    assert any("Evidence URL required" in e for e in errors)

def test_reviewer_disagreement(temp_label_schema):
    validator = LabelValidator(temp_label_schema)
    df = pd.DataFrame({
        "event_id": ["E1"], 
        "reviewer_1": ["fire"], 
        "reviewer_2": ["unknown"], 
        "final_label": [None],
        "evidence_urls": ["url"]
    })
    canon_df = pd.DataFrame({"event_id": ["E1"]})
    errors = validator.validate_labels(df, canon_df)
    assert any("Reviewers disagree but no final_label provided" in e for e in errors)

def test_invalid_event_id(temp_label_schema):
    validator = LabelValidator(temp_label_schema)
    df = pd.DataFrame({"event_id": ["E2"], "final_label": ["fire"], "evidence_urls": ["url"]})
    canon_df = pd.DataFrame({"event_id": ["E1"]})
    errors = validator.validate_labels(df, canon_df)
    assert any("not present in canonical dataset" in e for e in errors)
