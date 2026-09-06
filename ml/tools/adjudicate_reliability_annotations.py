"""
adjudicate_reliability_annotations.py

Adjudication tool for building adjudicated human ground-truth datasets from independent dual-human annotations.
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Tuple

# Ensure ml is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.classification.models import TAXONOMY_CLASSES
from tools.validate_human_reliability_annotations import validate_single_annotator_file

HUMAN_GT_SOURCE = "human_independent_annotation"
HUMAN_GT_STATUS = "adjudicated"

def adjudicate_reliability_annotations(
    file_path_a: str,
    file_path_b: str,
    adjudication_decisions: Dict[str, Dict[str, Any]],
    output_path: str = None
) -> List[Dict[str, Any]]:
    """
    Combines completed Annotator A and Annotator B records with explicit human adjudication decisions
    to produce the canonical human-ground-truth dataset.

    - Agreed records automatically retain their agreed label.
    - Disagreements REQUIRE an explicit entry in `adjudication_decisions`. Auto-adjudication is strictly forbidden.
    """
    recs_a = validate_single_annotator_file(file_path_a)
    recs_b = validate_single_annotator_file(file_path_b)

    dict_a = {r["event_id"]: r for r in recs_a}
    dict_b = {r["event_id"]: r for r in recs_b}

    common_ids = sorted(list(set(dict_a.keys()).intersection(set(dict_b.keys()))))
    if len(common_ids) != 30:
        raise ValueError(f"Expected 30 common event_ids between Annotator A and B, found {len(common_ids)}")

    adjudicated_records = []
    timestamp_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for eid in common_ids:
        ra = dict_a[eid]
        rb = dict_b[eid]

        la = ra["assigned_label"]
        lb = rb["assigned_label"]

        if la == lb:
            final_label = la
            status = "agreed_consensus"
            followed = "agreed"
            rationale = "Independent dual-human consensus"
        else:
            # Disagreement requires explicit human decision in decisions dictionary
            if eid not in adjudication_decisions:
                raise ValueError(
                    f"UNADJUDICATED DISAGREEMENT! Event '{eid}' has label A='{la}' vs label B='{lb}', "
                    f"but is missing from the supplied adjudication decisions mapping."
                )

            decision = adjudication_decisions[eid]
            final_label = decision.get("final_adjudicated_label") or decision.get("adjudicated_label")
            if not final_label or final_label not in TAXONOMY_CLASSES:
                raise ValueError(f"Invalid adjudicated label '{final_label}' for event '{eid}'.")

            status = "adjudicated_disagreement"
            rationale = decision.get("adjudicator_rationale") or decision.get("rationale", "")
            if not rationale:
                raise ValueError(f"Adjudication rationale required for disagreement event '{eid}'.")

            if final_label == la:
                followed = "followed_annotator_a"
            elif final_label == lb:
                followed = "followed_annotator_b"
            else:
                followed = "neither_assigned_third_label"

        record_gt = {
            "event_id": eid,
            "annotator_a_label": la,
            "annotator_b_label": lb,
            "final_adjudicated_label": final_label,
            "adjudication_status": status,
            "followed_choice": followed,
            "annotator_a_confidence": ra.get("confidence"),
            "annotator_b_confidence": rb.get("confidence"),
            "annotator_a_notes": ra.get("notes", ""),
            "annotator_b_notes": rb.get("notes", ""),
            "adjudicator_rationale": rationale,
            "source": HUMAN_GT_SOURCE,
            "status": HUMAN_GT_STATUS,
            "adjudication_timestamp": timestamp_str
        }

        adjudicated_records.append(record_gt)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(adjudicated_records, f, indent=2)
        print(f"Successfully saved adjudicated human ground-truth dataset ({len(adjudicated_records)} records) to: {output_path}")

    return adjudicated_records
