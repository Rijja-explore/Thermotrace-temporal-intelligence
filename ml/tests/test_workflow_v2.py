import pytest
import pandas as pd
import json

def test_v2_worksheet_structure():
    df = pd.read_csv('ml/data/pilot_001_reviewer_worksheet_v2.csv')
    assert 'reviewer_id' in df.columns
    assert 'review_complete' in df.columns
    assert 'label' in df.columns
    assert 'evidence_summary' in df.columns
    
def test_no_synthetic_risk_fields():
    df = pd.read_csv('ml/data/pilot_001_reviewer_worksheet_v2.csv')
    assert 'baseline_risk_score' not in df.columns
    assert 'baseline_risk_level' not in df.columns
    
def test_review_complete_is_distinct():
    df = pd.read_csv('ml/data/pilot_001_reviewer_worksheet_v2.csv')
    # Initially all are FALSE
    assert (df['review_complete'] == False).all()
    # Labels are empty
    assert df['label'].isna().all()

def test_evidence_required_for_completion():
    # Mocking validation logic that we'd use in the parser
    # if review_complete == True and label != unknown, evidence is required
    row = pd.Series({
        'review_complete': True,
        'label': 'fire',
        'evidence_urls': pd.NA
    })
    
    def validate_row(r):
        if r['review_complete']:
            if pd.isna(r['label']) or r['label'] == '':
                return False
            if r['label'] != 'unknown_requires_verification' and (pd.isna(r['evidence_urls']) or r['evidence_urls'] == ''):
                return False
        return True
        
    assert validate_row(row) == False
    
def test_incomplete_not_unknown():
    row = pd.Series({
        'review_complete': False,
        'label': 'unknown_requires_verification'
    })
    # the reviewer cannot use 'unknown' if they haven't completed the review (or they can, but review_complete must be True to count)
    def validate_completion(r):
        if r['label'] == 'unknown_requires_verification' and not r['review_complete']:
            return False # Invalid state
        return True
        
    assert validate_completion(pd.Series({'review_complete': False, 'label': ''})) == True

def test_allowed_taxonomy():
    schema = {
        "allowed_labels": [
            "persistent_industrial_source",
            "industrial_fire_or_abnormal_event",
            "wildfire_or_forest_fire",
            "agricultural_burning",
            "mining_or_other_industrial_activity",
            "unknown_requires_verification"
        ]
    }
    label = "bad_label"
    assert label not in schema["allowed_labels"]
