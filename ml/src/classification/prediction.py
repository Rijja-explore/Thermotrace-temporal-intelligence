from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from .evidence import EvidenceRecord
from .explainability import ExplanationRecord

class ModelLifecycleState(str, Enum):
    NOT_TRAINED = "NOT_TRAINED"
    TRAINED_UNVALIDATED = "TRAINED_UNVALIDATED"
    TRAINED_VALIDATED = "TRAINED_VALIDATED"
    RETIRED = "RETIRED"

class PredictionStatus(str, Enum):
    MODEL_NOT_TRAINED_NO_VERIFIED_LABELS = "MODEL_NOT_TRAINED_NO_VERIFIED_LABELS"
    PREDICTION_AVAILABLE = "PREDICTION_AVAILABLE"

class VerificationState(str, Enum):
    VERIFIED = "VERIFIED"
    MODEL_PREDICTION_REQUIRES_VERIFICATION = "MODEL_PREDICTION_REQUIRES_VERIFICATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"

class DataQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

@dataclass
class PredictionContract:
    event_id: str
    prediction_status: PredictionStatus
    predicted_label: str
    
    # Separated confidence semantics
    model_confidence: Optional[float]
    evidence_confidence: Optional[float]
    data_quality: DataQuality
    
    class_probabilities: Dict[str, float]
    evidence: List[EvidenceRecord]
    explanations: List[ExplanationRecord]
    
    model_version: str
    prediction_timestamp: str
    verification_state: VerificationState

def fail_prediction(event_id: str, explanations: List[ExplanationRecord] = None) -> PredictionContract:
    """Returns a canonical failure prediction when model is unverified/untrained."""
    if explanations is None:
        explanations = []
        
    return PredictionContract(
        event_id=event_id,
        prediction_status=PredictionStatus.MODEL_NOT_TRAINED_NO_VERIFIED_LABELS,
        predicted_label="unknown_requires_verification",
        model_confidence=None,
        evidence_confidence=None,
        data_quality=DataQuality.UNKNOWN,
        class_probabilities={},
        evidence=[], # Structured evidence representation empty in untrained state
        explanations=explanations,
        model_version="UNTRAINED",
        prediction_timestamp="N/A",
        verification_state=VerificationState.MODEL_NOT_AVAILABLE
    )
