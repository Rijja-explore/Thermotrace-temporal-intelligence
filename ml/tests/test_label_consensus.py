import pytest
import pandas as pd
from pathlib import Path
from src.label_consensus import ConsensusBuilder

@pytest.fixture
def mock_schema(tmp_path):
    import json
    schema = {
        "allowed_labels": ["fire", "unknown_requires_verification"],
        "confidence_values": ["HIGH", "LOW"],
        "evidence_requirements": {
            "evidence_urls_required_if_not_unknown": True
        }
    }
    path = tmp_path / "label_schema.json"
    with open(path, "w") as f:
        json.dump(schema, f)
    return path

def test_consensus_builder_empty(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    df = pd.DataFrame([{"event_id": "E1"}])
    res, adj = cb.process_worksheet(df)
    assert len(adj) == 0

def test_valid_reviewer(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    row = {
        "reviewer_1": "Alice",
        "label": "fire",
        "reviewer_1_confidence": "HIGH",
        "reviewer_1_evidence_urls": "http://evidence"
    }
    valid, msg = cb.validate_reviewer(row, "reviewer_1")
    assert valid

def test_invalid_taxonomy(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    row = {
        "reviewer_1": "Alice",
        "label": "not_a_fire",
        "reviewer_1_confidence": "HIGH",
        "reviewer_1_evidence_urls": "http://evidence"
    }
    valid, msg = cb.validate_reviewer(row, "reviewer_1")
    assert not valid
    assert "Invalid taxonomy" in msg

def test_missing_evidence(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    row = {
        "reviewer_1": "Alice",
        "label": "fire",
        "reviewer_1_confidence": "HIGH",
        "reviewer_1_evidence_urls": ""
    }
    valid, msg = cb.validate_reviewer(row, "reviewer_1")
    assert not valid

def test_unknown_class(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    row = {
        "reviewer_1": "Alice",
        "label": "unknown_requires_verification",
        "reviewer_1_confidence": "LOW",
        "reviewer_1_evidence_urls": ""
    }
    valid, msg = cb.validate_reviewer(row, "reviewer_1")
    assert valid

def test_disagreement_detection(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    row = pd.Series({"reviewer_1_label": "fire", "reviewer_2_label": "unknown"})
    status = cb.generate_consensus(row)
    assert status == "disagreement"

def test_consensus_detection(mock_schema):
    cb = ConsensusBuilder(mock_schema)
    row = pd.Series({"reviewer_1_label": "fire", "reviewer_2_label": "fire"})
    status = cb.generate_consensus(row)
    assert status == "consensus"
