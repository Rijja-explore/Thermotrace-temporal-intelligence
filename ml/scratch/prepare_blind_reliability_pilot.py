"""Create blinded, unaided packets for the Pilot V2 reliability subset.

This tool intentionally reads the frozen double-annotation membership from the
canonical 100-record Pilot V2 dataset, then cross-checks it against the
existing 30-record Annotator 2 assignment file.  It never writes either source
file.  Packets contain only the evidence fields an annotator needs, plus the
stable ``event_id`` needed to reconcile completed work later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PILOT_DIR = Path("ml/data/ground_truth/human_verified/pilot_v2")
SOURCE_RECORDS_PATH = PILOT_DIR / "pilot_v2_records_100.json"
SUBSET_CROSSCHECK_PATH = PILOT_DIR / "annotator_2_assignments.json"
DEFAULT_OUTPUT_DIR = PILOT_DIR / "reliability"
EXPECTED_RECORD_COUNT = 30

# These are deliberately strict.  A source-schema change must be reviewed
# before it can be safely turned into a blinded human-annotation packet.
SOURCE_RECORD_FIELDS = {
    "event_id",
    "latitude",
    "longitude",
    "timestamp",
    "source_features",
    "ai_assisted_v2_label",
    "ai_assisted_confidence",
    "ai_assisted_reasoning",
    "human_verified_label",
    "annotator_1_label",
    "annotator_2_label",
    "adjudicated_label",
    "annotator_1_confidence",
    "annotator_2_confidence",
    "adjudicated_confidence",
    "annotator_1_notes",
    "annotator_2_notes",
    "adjudicated_notes",
    "verification_status",
    "provenance",
}
SOURCE_FEATURE_FIELDS = {
    "max_frp_mw",
    "duration_hours",
    "active_days_previous_30d",
    "events_previous_30d",
    "forest_fraction_1km",
    "cropland_fraction_1km",
    "builtup_fraction_1km",
    "distance_to_facility_km",
    "near_refinery",
    "near_factory",
    "near_mine",
    "near_quarry",
}
PROVENANCE_FIELDS = {
    "source_candidate_pool",
    "total_candidate_population",
    "pilot_size",
    "sampling_method",
    "random_seed",
    "sampling_stratum",
    "is_double_annotation_target",
}
SUBSET_ASSIGNMENT_FIELDS = {
    "event_id",
    "latitude",
    "longitude",
    "timestamp",
    "source_features",
    "ai_assisted_suggestion",
    "ai_assisted_confidence",
    "annotator_id",
    "is_double_annotation",
    "assigned_label",
    "annotator_confidence",
    "evidence_notes",
    "status",
}
PACKET_RECORD_FIELDS = ("event_id", "latitude", "longitude", "timestamp", "source_features")
REMOVED_FIELDS = (
    "ai_assisted_v2_label",
    "ai_assisted_confidence",
    "ai_assisted_reasoning",
    "human_verified_label",
    "annotator_1_label",
    "annotator_2_label",
    "adjudicated_label",
    "annotator_1_confidence",
    "annotator_2_confidence",
    "adjudicated_confidence",
    "annotator_1_notes",
    "annotator_2_notes",
    "adjudicated_notes",
    "verification_status",
    "provenance",
)


def _load_json(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Required source file is missing: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in source file {path}: {error}") from error
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list in {path}, got {type(payload).__name__}")
    return payload


def _require_exact_fields(record: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(record)
    missing, unexpected = expected - actual, actual - expected
    if missing or unexpected:
        raise ValueError(
            f"Unsafe source schema in {context}: missing={sorted(missing)}, "
            f"unexpected={sorted(unexpected)}"
        )


def _validate_source(records: list[dict[str, Any]], assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(records) != 100:
        raise ValueError(f"Expected 100 canonical Pilot V2 records, found {len(records)}")

    event_ids: set[str] = set()
    frozen_subset: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Unsafe source schema in record {index}: expected an object")
        _require_exact_fields(record, SOURCE_RECORD_FIELDS, f"canonical record {index}")
        if not isinstance(record["source_features"], dict):
            raise ValueError(f"Unsafe source schema in canonical record {index}: source_features is not an object")
        _require_exact_fields(record["source_features"], SOURCE_FEATURE_FIELDS, f"source_features for record {index}")
        if not isinstance(record["provenance"], dict):
            raise ValueError(f"Unsafe source schema in canonical record {index}: provenance is not an object")
        _require_exact_fields(record["provenance"], PROVENANCE_FIELDS, f"provenance for record {index}")
        event_id = record["event_id"]
        if not isinstance(event_id, str) or not event_id:
            raise ValueError(f"Unsafe source schema in canonical record {index}: invalid event_id")
        if event_id in event_ids:
            raise ValueError(f"Unsafe source dataset: duplicate event_id {event_id!r}")
        event_ids.add(event_id)
        if record["provenance"]["is_double_annotation_target"] is True:
            frozen_subset.append(record)

    if len(frozen_subset) != EXPECTED_RECORD_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_RECORD_COUNT} frozen double-annotation records, found {len(frozen_subset)}"
        )

    assignment_ids: set[str] = set()
    for index, assignment in enumerate(assignments):
        if not isinstance(assignment, dict):
            raise ValueError(f"Unsafe source schema in assignment {index}: expected an object")
        _require_exact_fields(assignment, SUBSET_ASSIGNMENT_FIELDS, f"subset assignment {index}")
        if assignment["is_double_annotation"] is not True:
            raise ValueError(f"Unsafe source subset in assignment {index}: is_double_annotation is not true")
        event_id = assignment["event_id"]
        if event_id in assignment_ids:
            raise ValueError(f"Unsafe source subset: duplicate event_id {event_id!r}")
        assignment_ids.add(event_id)

    frozen_ids = {record["event_id"] for record in frozen_subset}
    if len(assignments) != EXPECTED_RECORD_COUNT or assignment_ids != frozen_ids:
        raise ValueError("Frozen-subset cross-check failed: Annotator 2 assignments do not exactly match canonical targets")
    return frozen_subset


def _packet_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{field: deepcopy(record[field]) for field in PACKET_RECORD_FIELDS} for record in records]


def _shuffle(records: list[dict[str, Any]], seed: int, packet_name: str) -> list[dict[str, Any]]:
    shuffled = list(records)
    # Packet-specific, hash-derived RNG seeds give independent reproducible orders.
    derived_seed = int.from_bytes(hashlib.sha256(f"{seed}:{packet_name}".encode("utf-8")).digest()[:16], "big")
    random.Random(derived_seed).shuffle(shuffled)
    return shuffled


def prepare_blind_reliability_pilot(
    *,
    seed: int | None = None,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    source_records_path: Path | str = SOURCE_RECORDS_PATH,
    subset_crosscheck_path: Path | str = SUBSET_CROSSCHECK_PATH,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write two blinded packets and a provenance manifest, returning the manifest."""
    source_records_path = Path(source_records_path)
    subset_crosscheck_path = Path(subset_crosscheck_path)
    output_dir = Path(output_dir)
    records = _validate_source(_load_json(source_records_path), _load_json(subset_crosscheck_path))

    effective_seed = secrets.randbits(64) if seed is None else seed
    if not isinstance(effective_seed, int):
        raise ValueError("seed must be an integer or None")
    packet_1 = _shuffle(_packet_records(records), effective_seed, "blind_annotator_1")
    packet_2 = _shuffle(_packet_records(records), effective_seed, "blind_annotator_2")
    if [item["event_id"] for item in packet_1] == [item["event_id"] for item in packet_2]:
        # This is exceptionally unlikely, but never permit identical presentation order.
        packet_2 = packet_2[1:] + packet_2[:1]

    created_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "source_dataset": str(source_records_path).replace("\\", "/"),
        "source_record_ids": sorted(record["event_id"] for record in records),
        "record_count": EXPECTED_RECORD_COUNT,
        "packet_generation_timestamp": created_at,
        "randomization": {
            "approach": "packet-specific SHA-256-derived Python random.Random shuffles",
            "seed": effective_seed,
            "seed_supplied": seed is not None,
            "packet_names": ["blind_annotator_1", "blind_annotator_2"],
        },
        "fields_deliberately_removed_for_blinding": list(REMOVED_FIELDS),
        "schema": {
            "source_record_fields": sorted(SOURCE_RECORD_FIELDS),
            "source_feature_fields": sorted(SOURCE_FEATURE_FIELDS),
            "source_provenance_sampling_method": records[0]["provenance"]["sampling_method"],
            "source_provenance_random_seed": records[0]["provenance"]["random_seed"],
            "packet_record_fields": list(PACKET_RECORD_FIELDS),
            "schema_version": "pilot_v2_reliability_blind_packet_v1",
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, packet in (("blind_annotator_1.json", packet_1), ("blind_annotator_2.json", packet_2)):
        (output_dir / filename).write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    (output_dir / "reliability_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare blinded Pilot V2 reliability annotation packets.")
    parser.add_argument("--seed", type=int, help="Optional seed for reproducible packet order.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    manifest = prepare_blind_reliability_pilot(seed=args.seed, output_dir=args.output_dir)
    print(f"Wrote {manifest['record_count']} records to each blinded reliability packet in {args.output_dir}")


if __name__ == "__main__":
    main()
