import hashlib
import json
from pathlib import Path

from scratch.prepare_blind_reliability_pilot import prepare_blind_reliability_pilot


PILOT_DIR = Path("ml/data/ground_truth/human_verified/pilot_v2")
# Snapshot every pre-existing V2 JSON artifact, not just the two files the
# preparer reads.  The reliability output lives in a child directory and is
# therefore deliberately excluded.
SOURCE_FILES = tuple(sorted(PILOT_DIR.glob("*.json")))
FORBIDDEN_FIELDS = {
    "ai_assisted_v2_label", "ai_assisted_confidence", "ai_assisted_reasoning",
    "human_verified_label", "annotator_1_label", "annotator_2_label",
    "adjudicated_label", "annotator_1_confidence", "annotator_2_confidence",
    "adjudicated_confidence", "annotator_1_notes", "annotator_2_notes",
    "adjudicated_notes", "verification_status", "provenance", "assigned_label",
    "evidence_notes", "annotator_id", "is_double_annotation",
}


def _read_packets(output_dir):
    return [json.loads((output_dir / f"blind_annotator_{number}.json").read_text()) for number in (1, 2)]


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_blind_packets_are_complete_independent_and_free_of_annotation_fields(tmp_path):
    output_dir = tmp_path / "reliability"
    manifest = prepare_blind_reliability_pilot(seed=20260904, output_dir=output_dir)
    first, second = _read_packets(output_dir)

    assert len(first) == len(second) == 30
    first_ids = [record["event_id"] for record in first]
    second_ids = [record["event_id"] for record in second]
    assert set(first_ids) == set(second_ids) == set(manifest["source_record_ids"])
    assert first_ids != second_ids
    for packet in (first, second):
        for record in packet:
            assert not (set(record) & FORBIDDEN_FIELDS)
            assert set(record) == {"event_id", "latitude", "longitude", "timestamp", "source_features"}


def test_fixed_seed_reproduces_packet_content(tmp_path):
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    kwargs = {"seed": 79, "generated_at": "2026-09-04T00:00:00Z"}
    prepare_blind_reliability_pilot(output_dir=first_dir, **kwargs)
    prepare_blind_reliability_pilot(output_dir=second_dir, **kwargs)

    for filename in ("blind_annotator_1.json", "blind_annotator_2.json", "reliability_manifest.json"):
        assert (first_dir / filename).read_bytes() == (second_dir / filename).read_bytes()


def test_preparation_does_not_modify_sources(tmp_path):
    before = {path: _digest(path) for path in SOURCE_FILES}
    prepare_blind_reliability_pilot(seed=5, output_dir=tmp_path / "reliability")
    assert {path: _digest(path) for path in SOURCE_FILES} == before
