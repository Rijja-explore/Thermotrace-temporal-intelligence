import pytest
import json
import os

PILOT_DIR = "ml/data/ground_truth/human_verified/pilot"

def test_pilot_dataset_sizes():
    with open(os.path.join(PILOT_DIR, "pilot_records_150.json"), "r") as f:
        pilot_150 = json.load(f)
    with open(os.path.join(PILOT_DIR, "annotator_1_assignments.json"), "r") as f:
        ann_1 = json.load(f)
    with open(os.path.join(PILOT_DIR, "annotator_2_assignments.json"), "r") as f:
        ann_2 = json.load(f)
        
    assert len(pilot_150) == 150
    assert len(ann_1) == 150
    assert len(ann_2) == 100 # Exactly 100 double-annotated events

def test_no_duplicate_event_ids_in_pilot():
    with open(os.path.join(PILOT_DIR, "pilot_records_150.json"), "r") as f:
        pilot_150 = json.load(f)
    ids = [r["event_id"] for r in pilot_150]
    assert len(ids) == len(set(ids))

def test_evidence_fields_present_no_labels_prepopulated():
    with open(os.path.join(PILOT_DIR, "annotator_1_assignments.json"), "r") as f:
        ann_1 = json.load(f)
        
    req_fields = [
        "event_id", "centroid_lat", "centroid_lon", "start_time",
        "max_frp_mw", "events_previous_30d", "forest_fraction_1km", "distance_to_facility_km"
    ]
    for r in ann_1:
        for f in req_fields:
            assert f in r
        # Ensure no semantic labels or predictions are pre-populated
        assert r["assigned_class"] is None
        assert r["confidence"] is None
        assert r["review_status"] == "pending"

def test_mock_benchmark_remains_separate():
    mock_path = "ml/data/mock_remote_sensing_ground_truth.json"
    assert os.path.exists(mock_path)
    assert not mock_path.startswith(PILOT_DIR)
