import numpy as np
from typing import List, Dict, Any, Tuple
from collections import Counter

def calculate_raw_agreement(labels_a: List[str], labels_b: List[str]) -> float:
    if len(labels_a) == 0 or len(labels_a) != len(labels_b):
        raise ValueError("Mismatched or empty label lists.")
    matches = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    return float(matches / len(labels_a))

def calculate_cohens_kappa(labels_a: List[str], labels_b: List[str], categories: List[str]) -> float:
    if len(labels_a) == 0 or len(labels_a) != len(labels_b):
        raise ValueError("Mismatched or empty label lists.")
        
    n = len(labels_a)
    po = calculate_raw_agreement(labels_a, labels_b)
    
    count_a = Counter(labels_a)
    count_b = Counter(labels_b)
    
    pe = sum((count_a[cat] / n) * (count_b[cat] / n) for cat in categories)
    
    if pe == 1.0:
        return 1.0
    return float((po - pe) / (1.0 - pe))

def detect_disagreements(records_a: List[Dict[str, Any]], records_b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    disagreements = []
    map_b = {r['event_id']: r for r in records_b}
    
    for r_a in records_a:
        event_id = r_a['event_id']
        if event_id in map_b:
            r_b = map_b[event_id]
            if r_a['assigned_label'] != r_b['assigned_label']:
                disagreements.append({
                    "event_id": event_id,
                    "label_annotator_a": r_a['assigned_label'],
                    "label_annotator_b": r_b['assigned_label'],
                    "status": "ADJUDICATION_REQUIRED"
                })
    return disagreements
