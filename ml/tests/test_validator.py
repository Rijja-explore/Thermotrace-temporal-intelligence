import pytest
import pandas as pd
from pathlib import Path
from src.validate_human_review_submission import SubmissionValidator

@pytest.fixture
def master_ids():
    return [f"EVT_{i}" for i in range(40)]
    
@pytest.fixture
def valid_submission(tmp_path, master_ids):
    df = pd.DataFrame({
        'event_id': master_ids,
        'reviewer_id': 'reviewer_1',
        'label': 'wildfire_or_forest_fire',
        'label_confidence': 'HIGH',
        'evidence_urls': 'http://evidence',
        'evidence_summary': 'Looks like fire',
        'reviewer_notes': '',
        'review_complete': True
    })
    path = tmp_path / "sub.csv"
    df.to_csv(path, index=False)
    return path

def test_valid_submission(master_ids, valid_submission):
    v = SubmissionValidator(master_ids, 'reviewer_1')
    status, msg = v.validate(valid_submission)
    assert status == "VALID_COMPLETED_SUBMISSION"

def test_missing_event(tmp_path, master_ids):
    df = pd.DataFrame({
        'event_id': master_ids[:39],
        'reviewer_id': 'reviewer_1',
        'review_complete': False
    })
    p = tmp_path / "bad.csv"
    df.to_csv(p, index=False)
    v = SubmissionValidator(master_ids, 'reviewer_1')
    status, _ = v.validate(p)
    assert status == "INVALID_SUBMISSION"

def test_incomplete_submission(tmp_path, master_ids):
    df = pd.DataFrame({
        'event_id': master_ids,
        'reviewer_id': 'reviewer_1',
        'review_complete': False
    })
    p = tmp_path / "inc.csv"
    df.to_csv(p, index=False)
    v = SubmissionValidator(master_ids, 'reviewer_1')
    status, msg = v.validate(p)
    assert status == "INCOMPLETE_SUBMISSION"

def test_missing_evidence_on_complete(tmp_path, master_ids):
    df = pd.DataFrame({
        'event_id': master_ids,
        'reviewer_id': 'reviewer_1',
        'label': 'wildfire_or_forest_fire',
        'label_confidence': 'HIGH',
        'evidence_urls': '', # Missing
        'evidence_summary': 'Looks like fire',
        'review_complete': True
    })
    p = tmp_path / "ev.csv"
    df.to_csv(p, index=False)
    v = SubmissionValidator(master_ids, 'reviewer_1')
    status, msg = v.validate(p)
    assert status == "INVALID_SUBMISSION"
    assert "missing evidence_urls" in msg

def test_invalid_taxonomy(tmp_path, master_ids):
    df = pd.DataFrame({
        'event_id': master_ids,
        'reviewer_id': 'reviewer_1',
        'label': 'bad_label',
        'label_confidence': 'HIGH',
        'evidence_urls': 'http',
        'evidence_summary': 'yep',
        'review_complete': True
    })
    p = tmp_path / "tax.csv"
    df.to_csv(p, index=False)
    v = SubmissionValidator(master_ids, 'reviewer_1')
    status, msg = v.validate(p)
    assert status == "INVALID_SUBMISSION"
    assert "invalid label" in msg
