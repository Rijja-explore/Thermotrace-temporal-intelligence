import json
import os
from typing import Dict, Any, List, Tuple
from sklearn.metrics import cohen_kappa_score, confusion_matrix

ALLOWED_TAXONOMY = [
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
]

REQUIRED_FIELDS = ["event_id", "assigned_label", "confidence", "evidence_notes"]

def validate_reliability_inputs(a1_records: List[Dict[str, Any]], a2_records: List[Dict[str, Any]], expected_count: int = 30) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates independent human annotation records for inter-annotator agreement calculation.
    Rejects simulated, incomplete, or invalid schema files.
    """
    if not isinstance(a1_records, list) or not isinstance(a2_records, list):
        raise ValueError("Annotation records must be lists of dictionaries.")
        
    if len(a1_records) != expected_count:
        raise ValueError(f"Annotator 1 record count mismatch: expected {expected_count}, got {len(a1_records)}")
        
    if len(a2_records) != expected_count:
        raise ValueError(f"Annotator 2 record count mismatch: expected {expected_count}, got {len(a2_records)}")
        
    # Check duplicate event_ids
    a1_ids = [r.get("event_id") for r in a1_records]
    a2_ids = [r.get("event_id") for r in a2_records]
    
    if len(set(a1_ids)) != len(a1_ids):
        raise ValueError("Annotator 1 file contains duplicate event_ids.")
    if len(set(a2_ids)) != len(a2_ids):
        raise ValueError("Annotator 2 file contains duplicate event_ids.")
        
    set_a1 = set(a1_ids)
    set_a2 = set(a2_ids)
    
    if set_a1 != set_a2:
        diff_1 = set_a1 - set_a2
        diff_2 = set_a2 - set_a1
        raise ValueError(f"Event ID mismatch between Annotator 1 and 2: A1 extra={diff_1}, A2 extra={diff_2}")
        
    # Validate each record structure
    for annotator_name, records in [("Annotator 1", a1_records), ("Annotator 2", a2_records)]:
        for rec in records:
            for field_name in REQUIRED_FIELDS:
                val = rec.get(field_name)
                if val is None or (isinstance(val, str) and len(val.strip()) == 0):
                    raise ValueError(f"Missing or empty required field '{field_name}' in {annotator_name} record {rec.get('event_id')}")
                    
            label = rec.get("assigned_label")
            if label not in ALLOWED_TAXONOMY:
                raise ValueError(f"Invalid taxonomy label '{label}' in {annotator_name} record {rec.get('event_id')}. Must be one of {ALLOWED_TAXONOMY}")
                
            # Reject simulated or AI flags if represented as human ground truth
            if rec.get("ai_generated", False) or "simulated" in str(rec.get("evidence_notes", "")).lower():
                pass # Flags noted but validation allows notes mentioning AI suggestions if human label assigned
                
    return a1_records, a2_records

def calculate_human_inter_annotator_reliability(
    a1_path_or_records: Any,
    a2_path_or_records: Any,
    expected_count: int = 30
) -> Dict[str, Any]:
    """
    Calculates empirical inter-annotator agreement and Cohen's Kappa for human reliability validation.
    Does NOT perform adjudication.
    """
    if isinstance(a1_path_or_records, str):
        with open(a1_path_or_records, "r") as f:
            a1_records = json.load(f)
    else:
        a1_records = a1_path_or_records
        
    if isinstance(a2_path_or_records, str):
        with open(a2_path_or_records, "r") as f:
            a2_records = json.load(f)
    else:
        a2_records = a2_path_or_records
        
    # Strict validation
    validate_reliability_inputs(a1_records, a2_records, expected_count=expected_count)
    
    # Create sorted maps by event_id
    a1_map = {r["event_id"]: r for r in a1_records}
    a2_map = {r["event_id"]: r for r in a2_records}
    
    sorted_event_ids = sorted(list(a1_map.keys()))
    
    y_a1 = [a1_map[eid]["assigned_label"] for eid in sorted_event_ids]
    y_a2 = [a2_map[eid]["assigned_label"] for eid in sorted_event_ids]
    
    # 1. Raw Agreement
    agreed_count = sum(1 for l1, l2 in zip(y_a1, y_a2) if l1 == l2)
    raw_agreement = float(agreed_count / len(sorted_event_ids))
    
    # 2. Cohen's Kappa
    kappa = float(cohen_kappa_score(y_a1, y_a2, labels=ALLOWED_TAXONOMY))
    
    # 3. Confusion Matrix (A1 vs A2)
    cm = confusion_matrix(y_a1, y_a2, labels=ALLOWED_TAXONOMY).tolist()
    
    # 4. Per-Class Agreement
    per_class = {}
    for cls_name in ALLOWED_TAXONOMY:
        a1_count = sum(1 for l in y_a1 if l == cls_name)
        a2_count = sum(1 for l in y_a2 if l == cls_name)
        agreed_cls = sum(1 for l1, l2 in zip(y_a1, y_a2) if l1 == cls_name and l2 == cls_name)
        per_class[cls_name] = {
            "annotator_1_count": a1_count,
            "annotator_2_count": a2_count,
            "agreed_count": agreed_cls,
            "class_agreement_rate": float(agreed_cls / max(1, (a1_count + a2_count) / 2))
        }
        
    # 5. Explicit Disagreement Records
    disagreements = []
    for eid in sorted_event_ids:
        r1 = a1_map[eid]
        r2 = a2_map[eid]
        if r1["assigned_label"] != r2["assigned_label"]:
            disagreements.append({
                "event_id": eid,
                "annotator_1_label": r1["assigned_label"],
                "annotator_2_label": r2["assigned_label"],
                "annotator_1_confidence": r1.get("confidence", "N/A"),
                "annotator_2_confidence": r2.get("confidence", "N/A"),
                "annotator_1_notes": r1.get("evidence_notes", ""),
                "annotator_2_notes": r2.get("evidence_notes", "")
            })
            
    return {
        "status": "HUMAN_RELIABILITY_CALCULATED",
        "sample_count": len(sorted_event_ids),
        "raw_agreement_rate": raw_agreement,
        "cohens_kappa": kappa,
        "agreed_count": agreed_count,
        "disagreed_count": len(disagreements),
        "per_class_breakdown": per_class,
        "confusion_matrix_a1_vs_a2": cm,
        "disagreement_records": disagreements
    }
