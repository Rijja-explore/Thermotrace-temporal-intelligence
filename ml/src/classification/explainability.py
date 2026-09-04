from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import pandas as pd
from .features import validate_features

class ExplanationType(str, Enum):
    OBSERVATION = "OBSERVATION"
    SEMANTIC_EVIDENCE = "SEMANTIC_EVIDENCE"
    MODEL_EXPLANATION = "MODEL_EXPLANATION"

@dataclass
class ExplanationRecord:
    explanation_type: ExplanationType
    feature_name: str
    feature_value: Any
    unit: Optional[str]
    direction: Optional[str]
    importance: Optional[float]
    source: str
    description: str

class ObservationSummarizer:
    @staticmethod
    def _get_unit(feature: str) -> Optional[str]:
        if "frp" in feature:
            return "MW"
        if "hours" in feature or "duration" in feature:
            return "hours"
        if "fraction" in feature:
            return "percent"
        if "km" in feature or "distance" in feature:
            return "km"
        if "count" in feature or "events" in feature or "days" in feature:
            return "count"
        return None

    @staticmethod
    def _format_description(feature: str, value: Any) -> str:
        # Enforce strict factual wording. NO CAUSAL LANGUAGE ("causes", "proves", "wildfire", "industrial").
        if feature == "max_frp_mw":
            return f"Maximum observed FRP was {value} MW."
        if feature == "mean_frp_mw":
            return f"Mean observed FRP was {value} MW."
        if feature == "sum_frp_mw":
            return f"Cumulative observed FRP was {value} MW."
        if feature == "duration_hours":
            return f"Event duration was {value} hours."
        if feature == "detection_count":
            return f"Event contained {value} detections."
        if "events_previous_" in feature:
            days = feature.split("_")[-1].replace("d", "")
            return f"There were {value} prior thermal events in the preceding {days} days."
        if "fraction" in feature:
            kind = feature.split("_")[0]
            return f"The mapped {kind} land-cover fraction is {value}."
        if "distance_to_" in feature:
            poi = feature.replace("distance_to_", "").replace("_km", "").replace("_", " ")
            return f"Event is {value} km from nearest mapped {poi}."
        if feature.startswith("near_"):
            poi = feature.replace("near_", "").replace("_", " ")
            return f"Event is near OSM-mapped {poi}."
        return f"Observed {feature} is {value}."

    @staticmethod
    def summarize(features: Dict[str, Any]) -> List[ExplanationRecord]:
        # Only use approved features (rejects leakage/heuristic fields)
        valid_keys = validate_features(list(features.keys()))
        
        observations = []
        for k in valid_keys:
            val = features[k]
            if val is None or pd.isna(val) if isinstance(val, float) else False:
                continue
                
            unit = ObservationSummarizer._get_unit(k)
            desc = ObservationSummarizer._format_description(k, val)
            
            observations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name=k,
                feature_value=val,
                unit=unit,
                direction=None,
                importance=None,
                source="FIRMS/OSM derived feature",
                description=desc
            ))
        return observations

class ModelExplanationInterface:
    @staticmethod
    def generate_explanation(model: Any, lifecycle_state: str, features: Dict[str, Any]) -> List[ExplanationRecord]:
        if lifecycle_state == "NOT_TRAINED":
            # Explicitly refuse to operate, returning no explanations or raise state
            return []
            
        # Placeholder for future SHAP / Permutation Importance integration.
        return []
