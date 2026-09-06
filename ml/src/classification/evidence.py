from enum import Enum
from dataclasses import dataclass
from typing import Optional

class EvidenceType(Enum):
    OBSERVATION = 'OBSERVATION'
    SEMANTIC_EVIDENCE = 'SEMANTIC_EVIDENCE'
    UNVERIFIED_EXTERNAL_CLAIM = 'UNVERIFIED_EXTERNAL_CLAIM'

@dataclass
class EvidenceRecord:
    source_type: str
    source_url: str
    source_name: str
    publication_or_acquisition_time: str
    event_time: str
    independent_of_firms: bool
    independently_verified: bool
    provenance_status: str
    notes: Optional[str] = None
    
    @property
    def evidence_type(self) -> EvidenceType:
        # FIRMS detection, OSM proximity, land cover, recurrence
        if not self.independent_of_firms:
            return EvidenceType.OBSERVATION
            
        # External claims that are not independently verified
        if not self.independently_verified:
            return EvidenceType.UNVERIFIED_EXTERNAL_CLAIM
            
        # Strict promotion rule: must be independent, verified, and have strict provenance
        if self.independent_of_firms and self.independently_verified and self.provenance_status == "VERIFIED":
            return EvidenceType.SEMANTIC_EVIDENCE
            
        return EvidenceType.UNVERIFIED_EXTERNAL_CLAIM
