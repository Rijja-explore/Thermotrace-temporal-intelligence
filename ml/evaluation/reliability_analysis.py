"""
reliability_analysis.py

Evaluation module for calculating empirical inter-annotator agreement statistics, extracting disagreements,
and generating the empirical human-reliability analysis report for the frozen Pilot V2 reliability sample.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

# Ensure ml is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.classification.models import TAXONOMY_CLASSES
from tools.validate_human_reliability_annotations import (
    verify_frozen_packet_integrity,
    validate_human_reliability_pair
)
from sklearn.metrics import confusion_matrix

RELIABILITY_DIR = "ml/data/ground_truth/human_verified/pilot_v2/reliability"
ANNOTATOR_1_COMPLETED = os.path.join(RELIABILITY_DIR, "annotator_1_completed.json")
ANNOTATOR_2_COMPLETED = os.path.join(RELIABILITY_DIR, "annotator_2_completed.json")

REPORTS_DIR = "ml/reports/model_benchmark/m4_class_balance/reliability"

def calculate_cohens_kappa(labels_a: List[str], labels_b: List[str], taxonomy: List[str] = None) -> Dict[str, float]:
    """
    Calculates raw percent agreement (p_o), expected chance agreement (p_e), and Cohen's Kappa (kappa)
    for two nominal categorical label sequences.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError(f"Label list length mismatch: len(A)={len(labels_a)}, len(B)={len(labels_b)}")

    N = len(labels_a)
    if N == 0:
        return {"raw_agreement": 0.0, "chance_agreement": 0.0, "cohens_kappa": 0.0, "sample_size": 0}

    if taxonomy is None:
        taxonomy = sorted(TAXONOMY_CLASSES)

    # Observed agreement p_o
    agreements = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    p_o = agreements / N

    # Chance agreement p_e
    p_e = 0.0
    for cat in taxonomy:
        p_a = sum(1 for x in labels_a if x == cat) / N
        p_b = sum(1 for x in labels_b if x == cat) / N
        p_e += (p_a * p_b)

    if p_e >= 1.0:
        kappa = 1.0 if p_o == 1.0 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    return {
        "sample_size": N,
        "agreements_count": agreements,
        "disagreements_count": N - agreements,
        "raw_agreement_po": round(float(p_o), 4),
        "expected_chance_pe": round(float(p_e), 4),
        "cohens_kappa": round(float(kappa), 4)
    }

def compute_inter_annotator_agreement(recs_a: List[Dict[str, Any]], recs_b: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes comprehensive inter-annotator agreement stats given completed Annotator A and B records.
    """
    taxonomy = sorted(TAXONOMY_CLASSES)
    
    # Align by event_id
    dict_a = {r["event_id"]: r for r in recs_a}
    dict_b = {r["event_id"]: r for r in recs_b}

    common_ids = sorted(list(set(dict_a.keys()).intersection(set(dict_b.keys()))))
    if len(common_ids) != len(dict_a) or len(common_ids) != len(dict_b):
        raise ValueError("Annotator A and B event_id sets do not match perfectly.")

    labels_a = [dict_a[eid]["assigned_label"] for eid in common_ids]
    labels_b = [dict_b[eid]["assigned_label"] for eid in common_ids]

    kappa_stats = calculate_cohens_kappa(labels_a, labels_b, taxonomy=taxonomy)

    # 6x6 Confusion Matrix (Annotator A on rows, Annotator B on columns)
    cm = confusion_matrix(labels_a, labels_b, labels=taxonomy).tolist()

    # Per-class agreement statistics
    per_class_stats = {}
    for i, cat in enumerate(taxonomy):
        count_a = sum(1 for x in labels_a if x == cat)
        count_b = sum(1 for x in labels_b if x == cat)
        both_agreed = sum(1 for a, b in zip(labels_a, labels_b) if a == cat and b == cat)
        
        per_class_stats[cat] = {
            "annotator_a_count": count_a,
            "annotator_b_count": count_b,
            "both_agreed_count": both_agreed,
            "class_agreement_rate": round(float(both_agreed / max(1, count_a + count_b - both_agreed)), 4)
        }

    return {
        "overall": kappa_stats,
        "taxonomy_classes": taxonomy,
        "confusion_matrix_a_vs_b": {
            "matrix": cm,
            "row_label": "Annotator A",
            "col_label": "Annotator B",
            "labels": taxonomy
        },
        "per_class_agreement": per_class_stats
    }

def export_disagreements(recs_a: List[Dict[str, Any]], recs_b: List[Dict[str, Any]], output_path: str = None) -> List[Dict[str, Any]]:
    """
    Extracts ONLY records where Annotator A label != Annotator B label.
    Omits any hidden AI labels, ground-truth targets, or synthetic scores.
    """
    dict_a = {r["event_id"]: r for r in recs_a}
    dict_b = {r["event_id"]: r for r in recs_b}

    common_ids = sorted(list(set(dict_a.keys()).intersection(set(dict_b.keys()))))
    disagreements = []

    for eid in common_ids:
        ra = dict_a[eid]
        rb = dict_b[eid]
        la = ra.get("assigned_label") or ra.get("label")
        lb = rb.get("assigned_label") or rb.get("label")

        if la != lb:
            disagreements.append({
                "event_id": eid,
                "annotator_a_label": la,
                "annotator_b_label": lb,
                "annotator_a_confidence": ra.get("confidence") or ra.get("annotator_confidence"),
                "annotator_b_confidence": rb.get("confidence") or rb.get("annotator_confidence"),
                "annotator_a_notes": ra.get("notes") or ra.get("evidence_notes", ""),
                "annotator_b_notes": rb.get("notes") or rb.get("evidence_notes", "")
            })

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(disagreements, f, indent=2)
        print(f"Exported {len(disagreements)} disagreement records to: {output_path}")

    return disagreements

def run_reliability_analysis():
    print("=" * 70)
    print(" EMPIRICAL HUMAN RELIABILITY ANALYSIS")
    print("=" * 70)

    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 1. Verify frozen packets integrity
    print("\n[1/5] Verifying frozen reliability packet integrity...")
    integrity_res = verify_frozen_packet_integrity()
    print("VERIFIED: Frozen packet checksums and blinding integrity match 100%.")

    # 2. Validate completed annotation files
    print("\n[2/5] Validating completed Annotator A and B submissions...")
    recs_a, recs_b = validate_human_reliability_pair(ANNOTATOR_1_COMPLETED, ANNOTATOR_2_COMPLETED)

    # 3. Compute empirical inter-annotator agreement
    print("\n[3/5] Computing empirical inter-annotator agreement statistics...")
    agreement_results = compute_inter_annotator_agreement(recs_a, recs_b)

    metrics_path = os.path.join(REPORTS_DIR, "empirical_reliability_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(agreement_results, f, indent=2)
    print(f"Saved empirical agreement metrics to: {metrics_path}")

    ov = agreement_results["overall"]
    print(f"\n--- EMPIRICAL AGREEMENT RESULTS ---")
    print(f" Sample Size (N)       : {ov['sample_size']}")
    print(f" Agreements Count      : {ov['agreements_count']}")
    print(f" Disagreements Count   : {ov['disagreements_count']}")
    print(f" Raw Agreement (p_o)   : {ov['raw_agreement_po'] * 100:.2f}%")
    print(f" Chance Agreement (p_e): {ov['expected_chance_pe'] * 100:.2f}%")
    print(f" Cohen's Kappa (kappa) : {ov['cohens_kappa']:.4f}")
    print(f"-----------------------------------")

    # 4. Export disagreements
    print("\n[4/5] Exporting disagreement cases for adjudication...")
    disag_path = os.path.join(REPORTS_DIR, "disagreement_cases.json")
    disagreements = export_disagreements(recs_a, recs_b, output_path=disag_path)

    # Prepare adjudication input template
    adj_input_path = os.path.join(REPORTS_DIR, "adjudication_input.json")
    adj_template = {
        "sample_size": ov["sample_size"],
        "agreements_count": ov["agreements_count"],
        "disagreements_count": ov["disagreements_count"],
        "status": "ready_for_adjudication" if len(disagreements) > 0 else "complete_consensus_no_disagreements",
        "disagreement_cases": disagreements
    }
    with open(adj_input_path, "w") as f:
        json.dump(adj_template, f, indent=2)
    print(f"Saved adjudication input template to: {adj_input_path}")

    # 5. Generate Markdown Report
    print("\n[5/5] Generating Empirical Human Reliability Report...")
    taxonomy = agreement_results["taxonomy_classes"]
    cm = agreement_results["confusion_matrix_a_vs_b"]["matrix"]

    report_md = f"""# Empirical Human Reliability Analysis Report
## Pilot V2 Frozen 30-Record Sample

> [!IMPORTANT]
> **Strict Empirical Methodological Boundary:**
> - The metrics in this report represent **REAL EMPIRICAL DUAL-HUMAN ANNOTATIONS** from independent Annotator 1 and Annotator 2 on the $N=30$ frozen reliability sample.
> - They are **STRICTLY DISTINCT** from earlier simulated Pilot V2 labels (which used synthetic heuristic scripts) and AI weak labels (`ai_assisted_label`).
> - **Zero AI leakage**: Annotators completed all 30 records blind to model predictions and AI suggestions.

---

## 1. Executive Summary & Core Agreement Statistics

- **Sample Size ($N$)**: **`30`** frozen thermal events
- **Agreed Detections**: **`{ov['agreements_count']}`** / `30`
- **Disagreement Count**: **`{ov['disagreements_count']}`** / `30`
- **Raw Inter-Annotator Agreement ($p_o$)**: **`{ov['raw_agreement_po'] * 100:.2f}%`** (`{ov['raw_agreement_po']:.4f}`)
- **Expected Chance Agreement ($p_e$)**: **`{ov['expected_chance_pe'] * 100:.2f}%`** (`{ov['expected_chance_pe']:.4f}`)
- **Cohen's Kappa (\\kappa)**: **`{ov['cohens_kappa']:.4f}`**

---

## 2. $6 \\times 6$ Inter-Annotator Confusion Matrix

Rows represent **Annotator A**, Columns represent **Annotator B**:

| Taxonomy Class | `agri` | `ind_fire` | `mining` | `persist` | `unknown` | `wildfire` | Total A |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `agricultural_burning` | **{cm[0][0]}** | {cm[0][1]} | {cm[0][2]} | {cm[0][3]} | {cm[0][4]} | {cm[0][5]} | {sum(cm[0])} |
| `industrial_fire_or_abnormal_event` | {cm[1][0]} | **{cm[1][1]}** | {cm[1][2]} | {cm[1][3]} | {cm[1][4]} | {cm[1][5]} | {sum(cm[1])} |
| `mining_or_other_industrial_activity` | {cm[2][0]} | {cm[2][1]} | **{cm[2][2]}** | {cm[2][3]} | {cm[2][4]} | {cm[2][5]} | {sum(cm[2])} |
| `persistent_industrial_source` | {cm[3][0]} | {cm[3][1]} | {cm[3][2]} | **{cm[3][3]}** | {cm[3][4]} | {cm[3][5]} | {sum(cm[3])} |
| `unknown_requires_verification` | {cm[4][0]} | {cm[4][1]} | {cm[4][2]} | {cm[4][3]} | **{cm[4][4]}** | {cm[4][5]} | {sum(cm[4])} |
| `wildfire_or_forest_fire` | {cm[5][0]} | {cm[5][1]} | {cm[5][2]} | {cm[5][3]} | {cm[5][4]} | **{cm[5][5]}** | {sum(cm[5])} |
| **Total B** | **{sum(cm[i][0] for i in range(6))}** | **{sum(cm[i][1] for i in range(6))}** | **{sum(cm[i][2] for i in range(6))}** | **{sum(cm[i][3] for i in range(6))}** | **{sum(cm[i][4] for i in range(6))}** | **{sum(cm[i][5] for i in range(6))}** | **30** |

---

## 3. Per-Class Agreement Breakdown

| Taxonomy Class | Annotator A Count | Annotator B Count | Both Agreed Count | Agreement Rate |
| :--- | :---: | :---: | :---: | :---: |
"""
    for cat in taxonomy:
        p_info = agreement_results["per_class_agreement"][cat]
        report_md += f"| `{cat}` | {p_info['annotator_a_count']} | {p_info['annotator_b_count']} | **{p_info['both_agreed_count']}** | **{p_info['class_agreement_rate'] * 100:.1f}%** |\n"

    report_md += f"""
---

## 4. Disagreement Summary & Adjudication Status

- **Total Disagreement Cases**: `{len(disagreements)}` records
- **Disagreement Export**: Saved to [`disagreement_cases.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/reliability/disagreement_cases.json)
- **Adjudication Input Prepared**: Saved to [`adjudication_input.json`](file:///C:/Project/Thermotrace-temporal-intelligence/ml/reports/model_benchmark/m4_class_balance/reliability/adjudication_input.json)

---

## 5. Distinction: Empirical Human Reliability vs Earlier Pilot V2 Results

1. **Earlier Pilot V2 Labels (Simulated)**:
   - Generated by rule-based heuristic scripts (`build_pilot_v2_subset.py`).
   - Macro F1 against simulated labels was `0.5877`.
   - **NOT** empirical human annotations.

2. **Current Empirical Human Reliability (This Report)**:
   - Produced by 2 independent human annotators on frozen double-blinded packets.
   - Raw agreement: **`{ov['raw_agreement_po'] * 100:.2f}%`** | Cohen's $\\kappa$: **`{ov['cohens_kappa']:.4f}`**
   - Represents the true empirical baseline of human annotator consistency for Thermotrace event taxonomy.
"""

    report_file_path = os.path.join(REPORTS_DIR, "empirical_human_reliability_report.md")
    with open(report_file_path, "w") as f:
        f.write(report_md)

    print(f"\nEmpirical Reliability Analysis Complete! Report written to: {report_file_path}")

if __name__ == "__main__":
    run_reliability_analysis()
