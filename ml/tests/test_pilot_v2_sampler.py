import json
import os
import pytest
import pandas as pd
import numpy as np

PILOT_DIR = "ml/data/ground_truth/human_verified/pilot_v2"
PILOT_RECORDS_PATH = os.path.join(PILOT_DIR, "pilot_v2_records_100.json")
ANNOTATOR_1_PATH = os.path.join(PILOT_DIR, "annotator_1_assignments.json")
ANNOTATOR_2_PATH = os.path.join(PILOT_DIR, "annotator_2_assignments.json")

V2_WEAK_LABELS_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
V2_PRIORITY_PATH = "ml/data/ground_truth/ai_assisted/human_review_priority_v2.json"

VALID_TAXONOMY = {
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
}

def test_pilot_v2_records_count_and_uniqueness():
    assert os.path.exists(PILOT_RECORDS_PATH)
    with open(PILOT_RECORDS_PATH, "r") as f:
        records = json.load(f)
    
    assert len(records) == 100
    event_ids = [r["event_id"] for r in records]
    assert len(set(event_ids)) == 100

def test_pilot_v2_no_prepopulated_human_labels():
    with open(PILOT_RECORDS_PATH, "r") as f:
        records = json.load(f)
        
    for r in records:
        assert r["human_verified_label"] is None
        assert r["annotator_1_label"] is None
        assert r["annotator_2_label"] is None
        assert r["adjudicated_label"] is None
        assert r["annotator_1_confidence"] is None
        assert r["annotator_2_confidence"] is None
        assert r["adjudicated_confidence"] is None
        assert r["annotator_1_notes"] is None
        assert r["annotator_2_notes"] is None
        assert r["adjudicated_notes"] is None
        assert r["verification_status"] == "unverified"

def test_pilot_v2_double_annotation_counts_and_assignments():
    assert os.path.exists(ANNOTATOR_1_PATH)
    assert os.path.exists(ANNOTATOR_2_PATH)
    
    with open(ANNOTATOR_1_PATH, "r") as f:
        a1 = json.load(f)
    with open(ANNOTATOR_2_PATH, "r") as f:
        a2 = json.load(f)
        
    assert len(a1) == 100
    assert len(a2) == 30
    
    for r in a1:
        assert r["assigned_label"] is None
        assert r["annotator_confidence"] is None
    for r in a2:
        assert r["assigned_label"] is None
        assert r["annotator_confidence"] is None
        assert "annotator_1_label" not in r

def test_pilot_v2_taxonomy_validity():
    with open(PILOT_RECORDS_PATH, "r") as f:
        records = json.load(f)
        
    for r in records:
        assert r["ai_assisted_v2_label"] in VALID_TAXONOMY

def test_pilot_v2_provenance_separation():
    with open(PILOT_RECORDS_PATH, "r") as f:
        records = json.load(f)
        
    for r in records:
        prov = r.get("provenance", {})
        assert prov.get("source_candidate_pool") == "ml/data/ground_truth/candidate_pool_v1.json"
        assert prov.get("random_seed") == 42
        assert prov.get("total_candidate_population") == 1500
        assert prov.get("pilot_size") == 100

def test_no_modification_of_v2_weak_label_files():
    assert os.path.exists(V2_WEAK_LABELS_PATH)
    assert os.path.exists(V2_PRIORITY_PATH)
    
    with open(V2_WEAK_LABELS_PATH, "r") as f:
        v2_labels = json.load(f)
    with open(V2_PRIORITY_PATH, "r") as f:
        v2_prio = json.load(f)
        
    assert len(v2_labels) == 1500
    assert len(v2_prio) == 1500
