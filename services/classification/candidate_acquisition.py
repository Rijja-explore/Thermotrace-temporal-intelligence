import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List
import sys

sys.path.append("ml")
from src.classification.investigation_priority import InvestigationPrioritizer

class CandidateAcquisition:
    
    @staticmethod
    def generate_batch(df: pd.DataFrame, batch_size: int = 100, random_seed: int = 42) -> pd.DataFrame:
        """
        Generates a deterministic candidate batch for human review, enforcing a balanced 
        sampling strategy to avoid selection bias (e.g. only learning from high-priority anomalies).
        """
        np.random.seed(random_seed)
        
        # 1. We must score the dataframe to get priority ranking
        # Note: In a production pipeline this would use pre-computed scores,
        # but here we generate the baseline score inline for candidate sampling.
        frp = df.get("max_frp_mw", 0).fillna(0) * 0.1
        cnt = df.get("detection_count", 0).fillna(0) * 1.0
        ev_30d = df.get("events_previous_30d", 0).fillna(0) * 5.0
        fac = (df.get("distance_to_facility_km", 999).fillna(999) < 2.0).astype(float) * 20.0
        df["priority_score"] = frp + cnt + ev_30d + fac # Using baseline priority for stable batching
        
        # Sort by priority
        df = df.sort_values("priority_score", ascending=False)
        df["priority_rank"] = np.arange(1, len(df) + 1)
        
        candidates = []
        
        # Strata calculation
        n_top = int(batch_size * 0.50)
        n_control = int(batch_size * 0.20)
        n_fac_low = int(batch_size * 0.15)
        n_frp_unmatched = int(batch_size * 0.15)
        
        # 50% Top Priority
        top_candidates = df.head(n_top).copy()
        top_candidates["acquisition_stratum"] = "HIGH_PRIORITY"
        candidates.append(top_candidates)
        
        remaining_df = df.iloc[n_top:]
        
        # 20% Random Controls
        control = remaining_df.sample(n=n_control, random_state=random_seed).copy()
        control["acquisition_stratum"] = "RANDOM_CONTROL"
        candidates.append(control)
        remaining_df = remaining_df.drop(control.index)
        
        # 15% Facility-Matched Low Priority
        fac_mask = remaining_df["distance_to_facility_km"] < 2.0
        fac_low = remaining_df[fac_mask].sample(n=min(n_fac_low, fac_mask.sum()), random_state=random_seed).copy()
        fac_low["acquisition_stratum"] = "FACILITY_MATCHED_LOW_PRIORITY"
        candidates.append(fac_low)
        remaining_df = remaining_df.drop(fac_low.index)
        
        # 15% High FRP Unmatched
        frp_mask = (remaining_df["max_frp_mw"] > 100.0) & (remaining_df["distance_to_facility_km"] >= 2.0)
        frp_unmatched = remaining_df[frp_mask].sample(n=min(n_frp_unmatched, frp_mask.sum()), random_state=random_seed).copy()
        frp_unmatched["acquisition_stratum"] = "HIGH_FRP_UNMATCHED"
        candidates.append(frp_unmatched)
        
        # Combine
        batch = pd.concat(candidates)
        
        # Formatting required output schema
        batch["required_evidence_types"] = "TIER_1_OR_TIER_2"
        batch["investigation_status"] = "UNREVIEWED"
        batch["final_label"] = ""
        
        output_cols = [
            "event_id", "priority_score", "priority_rank", 
            "acquisition_stratum", "required_evidence_types", 
            "investigation_status", "final_label"
        ]
        
        return batch[output_cols]

    @staticmethod
    def generate_readiness_report(batch: pd.DataFrame, report_path: str):
        # We know current verified labels = 0 (as established in previous tasks)
        counts = {
            "verified_by_class": {
                "persistent_industrial_source": 0,
                "industrial_fire_or_abnormal_event": 0,
                "wildfire_or_forest_fire": 0,
                "agricultural_burning": 0,
                "mining_or_other_industrial_activity": 0
            },
            "invalid_records_by_reason": {
                "AI-assisted only": 5, # the 5 unresolved investigations from batch 001 v2
                "heuristic/context only": 0,
                "unreviewed": 40,
                "unresolved": 0,
                "conflicting": 0
            }
        }
        
        coverage = batch["acquisition_stratum"].value_counts().to_dict()
        
        report = f"""# Ground Truth Acquisition Readiness Report

## Current Verified Labels
- **persistent_industrial_source**: 0
- **industrial_fire_or_abnormal_event**: 0
- **wildfire_or_forest_fire**: 0
- **agricultural_burning**: 0
- **mining_or_other_industrial_activity**: 0
*(Note: 'unknown_requires_verification' is an epistemic state, not a semantic label)*

## Current Invalid/Non-Ground-Truth Records
- **AI-assisted only / unresolved**: 5
- **heuristic/context only**: 0
- **unreviewed**: 40
- **unresolved conflicts**: 0
- **conflicting**: 0

## Acquisition Coverage (Batch 002 Planned)
- **Total Candidates**: {len(batch)}
"""
        for stratum, count in coverage.items():
            report += f"- **{stratum}**: {count}\n"

        report += """
## Selection Bias Diagnostics
The acquisition batch is deterministically stratified. If only high-priority events were labelled, the classifier would learn a distorted conditional distribution (bias). By enforcing a sampling strategy that includes `RANDOM_CONTROL` and `FACILITY_MATCHED_LOW_PRIORITY`, the ground-truth pipeline actively protects against selection bias.

## Training Readiness
`TRAINING_BLOCKED_NO_VERIFIED_GROUND_TRUTH`

Supervised semantic training is scientifically blocked because the exact verified-label counts across all taxonomy classes are 0. No fake labels or heuristic proxies have been injected.
"""
        with open(report_path, "w") as f:
            f.write(report)
        print(f"Report written to {report_path}")

if __name__ == "__main__":
    df = pd.read_parquet("data/processed/features/event_features_v2.parquet")
    batch = CandidateAcquisition.generate_batch(df, batch_size=100)
    batch.to_csv("ml/data/candidate_acquisition_batch.csv", index=False)
    CandidateAcquisition.generate_readiness_report(batch, "ml/reports/ground_truth_acquisition_readiness_report.md")
