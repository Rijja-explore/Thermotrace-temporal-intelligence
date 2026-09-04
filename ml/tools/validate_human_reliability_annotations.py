"""
validate_human_reliability_annotations.py

Import and validation tool for independent human reliability annotations on the frozen 30-record Pilot V2 sample.
"""

import os
import sys
import json
import hashlib
from typing import Dict, Any, List, Tuple

# Ensure ml is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.classification.models import TAXONOMY_CLASSES

RELIABILITY_DIR = "ml/data/ground_truth/human_verified/pilot_v2/reliability"
BLIND_ANNOTATOR_1_PATH = os.path.join(RELIABILITY_DIR, "blind_annotator_1.json")
BLIND_ANNOTATOR_2_PATH = os.path.join(RELIABILITY_DIR, "blind_annotator_2.json")
MANIFEST_PATH = os.path.join(RELIABILITY_DIR, "reliability_manifest.json")

# Known SHA-256 Checksums for Integrity Verification
FROZEN_CHECKSUMS = {
    "blind_annotator_1.json": "fb99905cfc4ae7ca3974be1054e5fb8132277466f4b05e64a0979e2fa31e6b8f",
    "blind_annotator_2.json": "8c6440256949df0d87bb9bdca0c6a9f1fec64296724889c35d2c690d88e8c924",
    "reliability_manifest.json": "c81f9a7f756dd50ef38fce374a57b494912a0b53d7b71dfc97495fe424900b9c"
}

ALLOWED_CONFIDENCE_VALUES = {
    1, 2, 3, 4, 5,
    "low", "medium", "high", "1", "2", "3", "4", "5"
}

def verify_frozen_packet_integrity() -> Dict[str, Any]:
    """
    Verifies SHA-256 checksums and structural integrity of the frozen reliability packets.
    Does NOT modify any files.
    """
    results = {}
    for filename, expected_hash in FROZEN_CHECKSUMS.items():
        filepath = os.path.join(RELIABILITY_DIR, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Frozen reliability artifact missing: {filepath}")
        
        with open(filepath, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
            
        if actual_hash != expected_hash:
            raise ValueError(
                f"INTEGRITY VIOLATION! File '{filename}' hash mismatch.\n"
                f"Expected: {expected_hash}\nActual:   {actual_hash}"
            )
        results[filename] = {"status": "VERIFIED_UNCHANGED", "sha256": actual_hash}

    # Verify packet record structures
    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
    with open(BLIND_ANNOTATOR_2_PATH, "r") as f:
        pkt2 = json.load(f)
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    if len(pkt1) != 30 or len(pkt2) != 30:
        raise ValueError(f"Packet record count mismatch: pkt1={len(pkt1)}, pkt2={len(pkt2)}, expected 30")

    ids1 = set(r["event_id"] for r in pkt1)
    ids2 = set(r["event_id"] for r in pkt2)
    manifest_ids = set(manifest["source_record_ids"])

    if ids1 != ids2 or ids1 != manifest_ids:
        raise ValueError("Packet event_ids do not match manifest source_record_ids!")

    order1 = [r["event_id"] for r in pkt1]
    order2 = [r["event_id"] for r in pkt2]
    if order1 == order2:
        raise ValueError("Packets 1 and 2 must have distinct record orderings!")

    forbidden_keys = {
        "ai_assisted_label", "ai_assisted_v2_label", "ai_assisted_confidence",
        "human_verified_label", "annotator_1_label", "annotator_2_label",
        "adjudicated_label", "strata", "sampling_group", "provenance"
    }

    for idx, r in enumerate(pkt1 + pkt2):
        found_forbidden = forbidden_keys.intersection(r.keys())
        if found_forbidden:
            raise ValueError(f"Blinding violation: record contains forbidden keys {found_forbidden}")

    return {
        "packet_integrity": "100% PASS",
        "record_count": 30,
        "event_id_match": True,
        "shuffled_ordering": True,
        "blinding_verified": True,
        "checksums": results
    }

def validate_single_annotator_file(file_path_or_records, expected_event_ids: set = None) -> List[Dict[str, Any]]:
    """
    Validates a single completed human annotation file or list of records.
    """
    if isinstance(file_path_or_records, str):
        if not os.path.exists(file_path_or_records):
            raise FileNotFoundError(f"Annotation file not found: {file_path_or_records}")
        with open(file_path_or_records, "r") as f:
            records = json.load(f)
    elif isinstance(file_path_or_records, list):
        records = file_path_or_records
    else:
        raise TypeError("Input must be a file path string or a list of dict records.")

    if not isinstance(records, list):
        raise ValueError("Annotation data must be a JSON array (list of objects).")

    if len(records) != 30:
        raise ValueError(f"Annotation file must contain exactly 30 records, found {len(records)}.")

    seen_ids = set()
    validated_records = []

    for idx, r in enumerate(records):
        if not isinstance(r, dict):
            raise ValueError(f"Record index {idx} is not a dictionary object.")

        eid = r.get("event_id")
        if not eid or not isinstance(eid, str):
            raise ValueError(f"Record index {idx} missing or invalid 'event_id'.")

        if eid in seen_ids:
            raise ValueError(f"Duplicate 'event_id' detected: {eid}")
        seen_ids.add(eid)

        # Label check
        label = r.get("assigned_label") or r.get("label") or r.get("human_label")
        if not label:
            raise ValueError(f"Record '{eid}' missing target label field ('assigned_label').")

        if label not in TAXONOMY_CLASSES:
            raise ValueError(
                f"Record '{eid}' label '{label}' is invalid.\n"
                f"Must be one of canonical taxonomy classes: {TAXONOMY_CLASSES}"
            )

        # Optional confidence check
        confidence = r.get("confidence")
        if confidence is not None:
            if isinstance(confidence, (int, float)):
                if not (0.0 <= confidence <= 5.0):
                    raise ValueError(f"Record '{eid}' confidence {confidence} outside allowed range [0.0, 5.0].")
            elif isinstance(confidence, str):
                if confidence.lower() not in ALLOWED_CONFIDENCE_VALUES:
                    raise ValueError(f"Record '{eid}' confidence string '{confidence}' invalid.")
            else:
                raise ValueError(f"Record '{eid}' confidence field invalid type.")

        # Check for forbidden AI / ground-truth contamination
        forbidden_injected = {"ai_assisted_label", "ai_assisted_v2_label", "adjudicated_label"}
        if forbidden_injected.intersection(r.keys()):
            raise ValueError(f"Record '{eid}' contains forbidden metadata key.")

        validated_records.append({
            "event_id": eid,
            "assigned_label": label,
            "confidence": confidence,
            "notes": r.get("notes", ""),
            "annotator_id": r.get("annotator_id", "unknown_annotator")
        })

    if expected_event_ids and seen_ids != expected_event_ids:
        missing = expected_event_ids - seen_ids
        extra = seen_ids - expected_event_ids
        raise ValueError(f"Annotation event_ids do not match expected frozen set! Missing: {missing}, Extra: {extra}")

    return validated_records

def validate_human_reliability_pair(file_path_a: str, file_path_b: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates a pair of completed human annotation files (Annotator A and Annotator B).
    Ensures both annotators completed all 30 frozen records independently.
    """
    verify_frozen_packet_integrity()

    with open(BLIND_ANNOTATOR_1_PATH, "r") as f:
        pkt1 = json.load(f)
    frozen_ids = set(r["event_id"] for r in pkt1)

    recs_a = validate_single_annotator_file(file_path_a, expected_event_ids=frozen_ids)
    recs_b = validate_single_annotator_file(file_path_b, expected_event_ids=frozen_ids)

    print(f"VALIDATION SUCCESSFUL: Annotator A ({len(recs_a)} records) and Annotator B ({len(recs_b)} records) validated.")
    return recs_a, recs_b

if __name__ == "__main__":
    print("Running frozen reliability packet integrity check...")
    res = verify_frozen_packet_integrity()
    print(json.dumps(res, indent=2))
