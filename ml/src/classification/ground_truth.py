import json
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

class EvidenceTier(Enum):
    TIER_1_DIRECT = 1
    TIER_2_CORROBORATING = 2
    TIER_3_CONTEXTUAL = 3

class LabelStatus(Enum):
    VERIFIED_LABEL = "VERIFIED_LABEL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNREVIEWED = "UNREVIEWED"

# The 6-class taxonomy. Unknown is an epistemic state.
ALLOWED_TAXONOMY = {
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
}

@dataclass
class EvidenceItem:
    evidence_tier: EvidenceTier
    evidence_type: str # e.g. SATELLITE_IMAGERY, NEWS_ARTICLE, OSM_PROXIMITY
    source: str
    source_url: Optional[str]
    evidence_summary: str
    source_timestamp: Optional[str] = None
    spatial_match: bool = False
    temporal_match: bool = False
    ai_generated: bool = False

@dataclass
class ReviewerConclusion:
    reviewer_id: str
    candidate_label: str
    confidence: str # HIGH, MEDIUM, LOW
    evidence: List[EvidenceItem] = field(default_factory=list)

@dataclass
class EvidenceRecord:
    event_id: str
    reviews: List[ReviewerConclusion] = field(default_factory=list)
    adjudication_status: str = "PENDING"
    final_label: Optional[str] = None

class GroundTruthEngine:
    
    @staticmethod
    def _is_evidence_independent(evidence_list: List[EvidenceItem]) -> List[EvidenceItem]:
        """Filters out duplicate sources based on URL/Source."""
        unique = []
        seen_urls = set()
        for e in evidence_list:
            # Contextual tier is not considered for independence count of ground truth
            if e.evidence_tier == EvidenceTier.TIER_3_CONTEXTUAL:
                continue
            
            identifier = e.source_url if e.source_url else e.source
            # If no identifier, we can't prove independence, so we don't count it as a unique independent source
            if not identifier:
                continue
                
            if identifier not in seen_urls:
                seen_urls.add(identifier)
                unique.append(e)
        return unique

    @staticmethod
    def check_sufficiency(record: EvidenceRecord) -> LabelStatus:
        if not record.reviews:
            return LabelStatus.UNREVIEWED
            
        # Consensus logic
        labels = [r.candidate_label for r in record.reviews if r.candidate_label in ALLOWED_TAXONOMY]
        
        if len(labels) == 0:
            return LabelStatus.UNREVIEWED
            
        if len(set(labels)) > 1:
            return LabelStatus.CONFLICTING_EVIDENCE
            
        consensus_label = labels[0]
        if consensus_label == "unknown_requires_verification":
            return LabelStatus.INSUFFICIENT_EVIDENCE
            
        # Collect all unique independent evidence from reviewers who agreed
        all_evidence = []
        for r in record.reviews:
            if r.candidate_label == consensus_label:
                all_evidence.extend(r.evidence)
                
        independent_evidence = GroundTruthEngine._is_evidence_independent(all_evidence)
        
        # Sufficiency Rule: 1 Tier 1, or 2 Tier 2 independent sources
        tier_1_count = sum(1 for e in independent_evidence if e.evidence_tier == EvidenceTier.TIER_1_DIRECT)
        tier_2_count = sum(1 for e in independent_evidence if e.evidence_tier == EvidenceTier.TIER_2_CORROBORATING)
        
        if tier_1_count >= 1 or tier_2_count >= 2:
            record.final_label = consensus_label
            return LabelStatus.VERIFIED_LABEL
            
        return LabelStatus.INSUFFICIENT_EVIDENCE

    @staticmethod
    def is_training_eligible(record: EvidenceRecord) -> bool:
        """
        Deterministic training eligibility function.
        Rejects unreviewed, conflicting, heuristic, AI-only, and unknown.
        """
        status = GroundTruthEngine.check_sufficiency(record)
        
        if status != LabelStatus.VERIFIED_LABEL:
            return False
            
        if record.final_label not in ALLOWED_TAXONOMY:
            return False
            
        if record.final_label == "unknown_requires_verification":
            return False
            
        # Ensure no AI-only labeled evidence bypassed checks (AI cannot be sole reviewer of truth)
        human_reviews = [r for r in record.reviews if not r.reviewer_id.startswith("AI_")]
        if not human_reviews:
            return False
            
        return True

    @staticmethod
    def prevent_label_leakage(evidence_urls: List[str], features: Dict[str, Any]) -> bool:
        """
        Verify that evidence used to assign the label is not fed into the classifier as an equivalent feature.
        If a feature contains text or NLP embeddings derived directly from an evidence URL, it is leaky.
        Returns False if leakage is detected.
        """
        for k, v in features.items():
            # Simplistic check: If the URL string itself or raw textual content from the URL is embedded in a feature string
            if isinstance(v, str):
                for url in evidence_urls:
                    if url and url in v:
                        return False
        return True

class AIInvestigationHelper:
    """
    AI may assist with retrieval and summarization (hypotheses), but may NOT output ground truth.
    """
    @staticmethod
    def create_hypothesis(candidate_label: str, evidence_items: List[EvidenceItem]) -> ReviewerConclusion:
        if candidate_label not in ALLOWED_TAXONOMY:
            raise ValueError("Invalid taxonomy label.")
            
        # Force AI generated flag
        for e in evidence_items:
            e.ai_generated = True
            
        return ReviewerConclusion(
            reviewer_id="AI_ASSISTANT",
            candidate_label=candidate_label,
            confidence="LOW", # AI confidence cannot override human thresholds
            evidence=evidence_items
        )
