import pytest
from src.classification.ground_truth import (
    EvidenceItem, EvidenceTier, ReviewerConclusion, 
    EvidenceRecord, GroundTruthEngine, LabelStatus, AIInvestigationHelper
)
from src.classification.candidate_acquisition import CandidateAcquisition
import pandas as pd

def test_ai_only_labels_rejected():
    ev = EvidenceItem(EvidenceTier.TIER_1_DIRECT, "SATELLITE_IMAGERY", "Sentinel", "url1", "summary")
    rev_ai = AIInvestigationHelper.create_hypothesis("wildfire_or_forest_fire", [ev])
    
    rec = EvidenceRecord("E1", reviews=[rev_ai])
    
    # Sufficiency might be VERIFIED_LABEL if AI found enough evidence
    status = GroundTruthEngine.check_sufficiency(rec)
    assert status == LabelStatus.VERIFIED_LABEL
    
    # But it is NOT training eligible because there are no human reviewers
    assert GroundTruthEngine.is_training_eligible(rec) is False

def test_heuristic_labels_rejected():
    ev1 = EvidenceItem(EvidenceTier.TIER_3_CONTEXTUAL, "OSM_PROXIMITY", "OSM", None, "Near factory")
    ev2 = EvidenceItem(EvidenceTier.TIER_3_CONTEXTUAL, "FRP_INTENSITY", "FIRMS", None, "High FRP")
    
    rev_human = ReviewerConclusion("user1", "industrial_fire_or_abnormal_event", "HIGH", [ev1, ev2])
    rec = EvidenceRecord("E2", reviews=[rev_human])
    
    # TIER_3 independent sources do not sum to sufficiency (need 1 Tier 1 or 2 Tier 2)
    assert GroundTruthEngine.check_sufficiency(rec) == LabelStatus.INSUFFICIENT_EVIDENCE
    assert GroundTruthEngine.is_training_eligible(rec) is False

def test_unreviewed_rejected():
    rec = EvidenceRecord("E3")
    assert GroundTruthEngine.check_sufficiency(rec) == LabelStatus.UNREVIEWED
    assert GroundTruthEngine.is_training_eligible(rec) is False

def test_conflicting_evidence_rejected():
    ev1 = EvidenceItem(EvidenceTier.TIER_1_DIRECT, "SATELLITE_IMAGERY", "Sentinel", "url1", "summary")
    rev1 = ReviewerConclusion("user1", "wildfire_or_forest_fire", "HIGH", [ev1])
    
    ev2 = EvidenceItem(EvidenceTier.TIER_1_DIRECT, "GROUND_REPORT", "FireService", "url2", "summary")
    rev2 = ReviewerConclusion("user2", "agricultural_burning", "HIGH", [ev2])
    
    rec = EvidenceRecord("E4", reviews=[rev1, rev2])
    
    assert GroundTruthEngine.check_sufficiency(rec) == LabelStatus.CONFLICTING_EVIDENCE
    assert GroundTruthEngine.is_training_eligible(rec) is False

def test_valid_evidence_accepted():
    ev1 = EvidenceItem(EvidenceTier.TIER_2_CORROBORATING, "NEWS", "News A", "urlA", "summary")
    ev2 = EvidenceItem(EvidenceTier.TIER_2_CORROBORATING, "NEWS", "News B", "urlB", "summary")
    
    rev1 = ReviewerConclusion("user1", "persistent_industrial_source", "HIGH", [ev1])
    rev2 = ReviewerConclusion("user2", "persistent_industrial_source", "HIGH", [ev2])
    
    rec = EvidenceRecord("E5", reviews=[rev1, rev2])
    
    # We have 2 independent Tier 2 sources across the agreed reviewers
    assert GroundTruthEngine.check_sufficiency(rec) == LabelStatus.VERIFIED_LABEL
    assert GroundTruthEngine.is_training_eligible(rec) is True
    assert rec.final_label == "persistent_industrial_source"

def test_duplicate_sources_not_independent():
    ev1 = EvidenceItem(EvidenceTier.TIER_2_CORROBORATING, "NEWS", "News A", "urlA", "summary")
    # Exact same URL
    ev2 = EvidenceItem(EvidenceTier.TIER_2_CORROBORATING, "NEWS", "News A Copy", "urlA", "summary")
    
    rev1 = ReviewerConclusion("user1", "persistent_industrial_source", "HIGH", [ev1])
    rev2 = ReviewerConclusion("user2", "persistent_industrial_source", "HIGH", [ev2])
    
    rec = EvidenceRecord("E6", reviews=[rev1, rev2])
    
    # Only 1 independent Tier 2 source, which is insufficient (needs 2)
    assert GroundTruthEngine.check_sufficiency(rec) == LabelStatus.INSUFFICIENT_EVIDENCE
    assert GroundTruthEngine.is_training_eligible(rec) is False

def test_label_leakage_protection():
    evidence_urls = ["http://news.local/factory_fire_2025"]
    
    # Safe feature
    features_safe = {"max_frp_mw": 100.5, "day_of_week": "Monday"}
    assert GroundTruthEngine.prevent_label_leakage(evidence_urls, features_safe) is True
    
    # Leaky feature (URL injected into text feature)
    features_leaky = {"llm_summary": "Based on http://news.local/factory_fire_2025 it was a fire."}
    assert GroundTruthEngine.prevent_label_leakage(evidence_urls, features_leaky) is False

def test_deterministic_candidate_selection():
    # Create mock dataframe
    data = []
    for i in range(200):
        data.append({
            "event_id": f"E_{i}",
            "max_frp_mw": 150.0 if i < 50 else 10.0,
            "distance_to_facility_km": 1.0 if i % 2 == 0 else 5.0,
            "detection_count": 5,
            "events_previous_30d": 1
        })
    df = pd.DataFrame(data)
    
    batch = CandidateAcquisition.generate_batch(df, batch_size=100, random_seed=42)
    
    assert len(batch) == 100
    counts = batch["acquisition_stratum"].value_counts()
    
    # Assert exact distribution
    assert counts["HIGH_PRIORITY"] == 50
    assert counts["RANDOM_CONTROL"] == 20
    assert counts["FACILITY_MATCHED_LOW_PRIORITY"] == 15
    assert counts["HIGH_FRP_UNMATCHED"] == 15
    
    # Ensure no duplicates
    assert batch["event_id"].nunique() == 100
