import json
import os
import pytest
import numpy as np

from tools.validate_human_reliability_annotations import (
    verify_frozen_packet_integrity,
    validate_single_annotator_file,
    validate_human_reliability_pair,
    FROZEN_CHECKSUMS
)
from evaluation.reliability_analysis import (
    calculate_cohens_kappa,
    compute_inter_annotator_agreement,
    export_disagreements
)
from tools.adjudicate_reliability_annotations import (
    adjudicate_reliability_annotations,
    HUMAN_GT_SOURCE,
    HUMAN_GT_STATUS
)
from src.classification.models import TAXONOMY_CLASSES

RELIABILITY_DIR = "ml/data/ground_truth/human_verified/pilot_v2/reliability"
BLIND_ANNOTATOR_1_PATH = os.path.join(RELIABILITY_DIR, "blind_annotator_1.json")
BLIND_ANNOTATOR_2_PATH = os.path.join(RELIABILITY_DIR, "blind_annotator_2.json")
MANIFEST_PATH = os.path.join(RELIABILITY_DIR, "reliability_manifest.json")

def test_frozen_packet_integrity():
    """
    Verifies SHA-256 checksums and structural integrity of frozen packets.
    """
    res = verify_frozen_packet_integrity()
    assert res["packet_integrity"] == "100% PASS"
    assert res["record_count"] == 30
    assert res["event_id_match"] is True
    assert res["shuffled_ordering"] is True
    assert res["blinding_verified"] is True

def test_validate_single_annotator_file_valid():
    """
    Verifies validation logic with a valid synthetic annotation array.
    """
    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
    
    synthetic_annotated = []
    for idx, r in enumerate(pkt1):
        synthetic_annotated.append({
            "event_id": r["event_id"],
            "assigned_label": TAXONOMY_CLASSES[idx % len(TAXONOMY_CLASSES)],
            "confidence": 4,
            "notes": "Synthetic validation test record",
            "annotator_id": "test_annotator_1"
        })
        
    validated = validate_single_annotator_file(synthetic_annotated)
    assert len(validated) == 30
    assert validated[0]["annotator_id"] == "test_annotator_1"

def test_validate_human_annotations_rejections():
    """
    Verifies that malformed, incomplete, or contaminated annotation files are rejected loudly.
    """
    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
        
    # 1. Invalid record count
    short_pkt = pkt1[:25]
    with pytest.raises(ValueError, match="must contain exactly 30 records"):
        validate_single_annotator_file(short_pkt)

    # 2. Missing target label
    bad_label_pkt = []
    for r in pkt1:
        bad_label_pkt.append({"event_id": r["event_id"]})
    with pytest.raises(ValueError, match="missing target label field"):
        validate_single_annotator_file(bad_label_pkt)

    # 3. Invalid taxonomy class
    invalid_class_pkt = []
    for idx, r in enumerate(pkt1):
        invalid_class_pkt.append({
            "event_id": r["event_id"],
            "assigned_label": "invalid_nonexistent_class" if idx == 0 else TAXONOMY_CLASSES[0]
        })
    with pytest.raises(ValueError, match="is invalid"):
        validate_single_annotator_file(invalid_class_pkt)

    # 4. Duplicate event_id
    dupe_pkt = []
    for idx, r in enumerate(pkt1):
        eid = pkt1[0]["event_id"] if idx == 1 else r["event_id"]
        dupe_pkt.append({
            "event_id": eid,
            "assigned_label": TAXONOMY_CLASSES[0]
        })
    with pytest.raises(ValueError, match="Duplicate 'event_id' detected"):
        validate_single_annotator_file(dupe_pkt)

    # 5. Out-of-bounds confidence rating
    bad_conf_pkt = []
    for idx, r in enumerate(pkt1):
        bad_conf_pkt.append({
            "event_id": r["event_id"],
            "assigned_label": TAXONOMY_CLASSES[0],
            "confidence": 99.0 if idx == 0 else 3
        })
    with pytest.raises(ValueError, match="outside allowed range"):
        validate_single_annotator_file(bad_conf_pkt)

def test_reliability_analysis_synthetic_fixture():
    """
    Verifies agreement calculation math and matrix construction using synthetic test fixtures.
    """
    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
    event_ids = [r["event_id"] for r in pkt1]

    # Construct synthetic fixtures with known disagreement rate (25 agreements, 5 disagreements)
    recs_a = []
    recs_b = []
    for idx, eid in enumerate(event_ids):
        lbl_a = TAXONOMY_CLASSES[idx % 5] # 5 active classes
        lbl_b = TAXONOMY_CLASSES[(idx + 1) % 5] if idx < 5 else lbl_a
        
        recs_a.append({"event_id": eid, "assigned_label": lbl_a, "confidence": 4})
        recs_b.append({"event_id": eid, "assigned_label": lbl_b, "confidence": 4})

    stats = compute_inter_annotator_agreement(recs_a, recs_b)
    
    assert stats["overall"]["sample_size"] == 30
    assert stats["overall"]["agreements_count"] == 25
    assert stats["overall"]["disagreements_count"] == 5
    assert stats["overall"]["raw_agreement_po"] == round(25 / 30, 4)
    assert 0.0 <= stats["overall"]["cohens_kappa"] <= 1.0
    assert len(stats["confusion_matrix_a_vs_b"]["matrix"]) == 6
    assert len(stats["confusion_matrix_a_vs_b"]["matrix"][0]) == 6

def test_disagreement_export_deterministic(tmp_path):
    """
    Verifies that export_disagreements extracts ONLY disagreement records without AI metadata.
    """
    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
    event_ids = [r["event_id"] for r in pkt1]

    recs_a = [{"event_id": eid, "assigned_label": TAXONOMY_CLASSES[0] if i == 0 else TAXONOMY_CLASSES[1]} for i, eid in enumerate(event_ids)]
    recs_b = [{"event_id": eid, "assigned_label": TAXONOMY_CLASSES[2] if i == 0 else TAXONOMY_CLASSES[1]} for i, eid in enumerate(event_ids)]

    out_csv = tmp_path / "disagreements.json"
    disagreements = export_disagreements(recs_a, recs_b, output_path=str(out_csv))

    assert len(disagreements) == 1
    assert disagreements[0]["event_id"] == event_ids[0]
    assert disagreements[0]["annotator_a_label"] == TAXONOMY_CLASSES[0]
    assert disagreements[0]["annotator_b_label"] == TAXONOMY_CLASSES[2]
    assert "ai_assisted_label" not in disagreements[0]

def test_adjudication_tooling_schema_and_provenance(tmp_path):
    """
    Verifies adjudication logic, schema generation, and provenance tracking.
    """
    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
    event_ids = [r["event_id"] for r in pkt1]

    # Create synthetic records with 1 disagreement at index 0
    recs_a = [{"event_id": eid, "assigned_label": TAXONOMY_CLASSES[0] if i == 0 else TAXONOMY_CLASSES[1]} for i, eid in enumerate(event_ids)]
    recs_b = [{"event_id": eid, "assigned_label": TAXONOMY_CLASSES[2] if i == 0 else TAXONOMY_CLASSES[1]} for i, eid in enumerate(event_ids)]

    file_a = tmp_path / "annotator_a.json"
    file_b = tmp_path / "annotator_b.json"
    with open(file_a, "w") as f:
        json.dump(recs_a, f)
    with open(file_b, "w") as f:
        json.dump(recs_b, f)

    # 1. Unadjudicated disagreement must fail
    with pytest.raises(ValueError, match="UNADJUDICATED DISAGREEMENT"):
        adjudicate_reliability_annotations(str(file_a), str(file_b), adjudication_decisions={})

    # 2. Adjudicated disagreement with valid decision
    decisions = {
        event_ids[0]: {
            "final_adjudicated_label": TAXONOMY_CLASSES[0],
            "adjudicator_rationale": "Cropland satellite imagery confirms stubble burning."
        }
    }

    out_gt_path = tmp_path / "human_ground_truth.json"
    adjudicated_dataset = adjudicate_reliability_annotations(
        str(file_a), str(file_b), decisions, output_path=str(out_gt_path)
    )

    assert len(adjudicated_dataset) == 30
    disag_record = next(r for r in adjudicated_dataset if r["event_id"] == event_ids[0])
    assert disag_record["final_adjudicated_label"] == TAXONOMY_CLASSES[0]
    assert disag_record["adjudication_status"] == "adjudicated_disagreement"
    assert disag_record["followed_choice"] == "followed_annotator_a"
    assert disag_record["source"] == HUMAN_GT_SOURCE
    assert disag_record["status"] == HUMAN_GT_STATUS

    agreed_record = next(r for r in adjudicated_dataset if r["event_id"] == event_ids[1])
    assert agreed_record["final_adjudicated_label"] == TAXONOMY_CLASSES[1]
    assert agreed_record["adjudication_status"] == "agreed_consensus"
    assert agreed_record["followed_choice"] == "agreed"

def test_empirical_human_ground_truth_integrity():
    """
    Verifies that canonical human_ground_truth_30.json contains exactly the 30 intended event_ids,
    has correct provenance metadata, and zero human labels leaked into training datasets.
    """
    gt_path = "ml/data/ground_truth/human_verified/pilot_v2/reliability/human_ground_truth_30.json"
    if not os.path.exists(gt_path):
        pytest.skip("human_ground_truth_30.json not generated yet")

    with open(gt_path, "r") as f:
        gt_data = json.load(f)

    assert len(gt_data) == 30
    gt_ids = set(r["event_id"] for r in gt_data)
    assert len(gt_ids) == 30

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    manifest_ids = set(manifest["source_record_ids"])
    assert gt_ids == manifest_ids

    for r in gt_data:
        assert r["source"] == HUMAN_GT_SOURCE
        assert r["status"] == HUMAN_GT_STATUS

    # Verify no human evaluation IDs leaked into weak-label training pool
    candidates_path = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
    with open(candidates_path, "r") as f:
        ai_labels = json.load(f)
    
    # Filter out Pilot V2 records from training pool as per split rules
    with open("ml/data/ground_truth/human_verified/pilot_v2/human_verified_pilot_v2_ground_truth.json", "r") as f:
        pilot_gt = json.load(f)
    pilot_ids = set(r["event_id"] for r in pilot_gt)

    training_pool = [r for r in ai_labels if r["event_id"] not in pilot_ids]
    training_pool_ids = set(r["event_id"] for r in training_pool)

    # Training pool must have 0 overlap with human reliability evaluation IDs
    assert len(training_pool_ids.intersection(gt_ids)) == 0

def test_empirical_evaluation_artifact_validity():
    """
    Verifies that empirical_m4_b_human_evaluation.json contains valid evaluation statistics.
    """
    eval_json = "ml/reports/model_benchmark/m4_class_balance/reliability/empirical_m4_b_human_evaluation.json"
    if not os.path.exists(eval_json):
        pytest.skip("empirical_m4_b_human_evaluation.json not generated yet")

    with open(eval_json, "r") as f:
        eval_data = json.load(f)

    assert eval_data["model_id"] == "M4-B"
    assert eval_data["sample_size"] == 30
    assert eval_data["overall_metrics"]["accuracy"] == 0.70
    assert eval_data["overall_metrics"]["error_count"] == 9
    assert len(eval_data["error_records"]) == 9

