import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from .models import BaseClassifier, TAXONOMY_CLASSES
from .prediction import PredictionContract, PredictionStatus, VerificationState, DataQuality
from .explainability import ExplanationRecord, ExplanationType

class ThermalOnlyBaseline(BaseClassifier):
    """
    Thermal-only baseline model predicting based on FRP intensity and thermal spread.
    Fails closed to unknown_requires_verification if thermal signal is ambiguous.
    """
    def __init__(self, high_frp_threshold: float = 100.0, skip_verification: bool = False):
        super().__init__(skip_verification=skip_verification)
        self.high_frp_threshold = high_frp_threshold

    def fit(self, X, y):
        super().fit(X, y)

    def predict(self, X):
        super().predict(X)
        preds = []
        # Convert DataFrame or dict list to iterable
        records = X.to_dict('records') if isinstance(X, pd.DataFrame) else X
        for r in records:
            frp = float(r.get("max_frp_mw", 0.0) or 0.0)
            if frp >= self.high_frp_threshold:
                preds.append("wildfire_or_forest_fire")
            else:
                preds.append("unknown_requires_verification")
        return preds

class RuleBasedClassifier(BaseClassifier):
    """
    Transparent deterministic RuleBasedClassifier implementing taxonomy rules.
    Facility proximity ALONE does not trigger industrial classification.
    Requires multi-feature combinations (persistence, land cover, facility type, spatial stability).
    """
    def __init__(
        self,
        facility_dist_km: float = 2.0,
        high_frp_mw: float = 150.0,
        persistence_days: float = 30.0,
        forest_threshold: float = 0.4,
        crop_threshold: float = 0.4,
        builtup_threshold: float = 0.3,
        min_confidence_diff: float = 0.15,
        skip_verification: bool = False
    ):
        super().__init__(skip_verification=skip_verification)
        self.facility_dist_km = facility_dist_km
        self.high_frp_mw = high_frp_mw
        self.persistence_days = persistence_days
        self.forest_threshold = forest_threshold
        self.crop_threshold = crop_threshold
        self.builtup_threshold = builtup_threshold
        self.min_confidence_diff = min_confidence_diff

    def fit(self, X, y):
        super().fit(X, y)

    def predict_event(self, event_dict: Dict[str, Any]) -> PredictionContract:
        event_id = str(event_dict.get("event_id", "UNKNOWN"))
        dist_fac = float(event_dict.get("distance_to_facility_km", 999.0) if event_dict.get("distance_to_facility_km") is not None else 999.0)
        near_refinery = bool(event_dict.get("near_refinery", False))
        near_factory = bool(event_dict.get("near_factory", False))
        near_mine = bool(event_dict.get("near_mine", False))
        near_quarry = bool(event_dict.get("near_quarry", False))
        active_days = float(event_dict.get("active_days_previous_30d", 0.0) or 0.0)
        events_30d = float(event_dict.get("events_previous_30d", 0.0) or 0.0)
        max_frp = float(event_dict.get("max_frp_mw", 0.0) or 0.0)
        forest_frac = float(event_dict.get("forest_fraction_1km", 0.0) or 0.0)
        crop_frac = float(event_dict.get("cropland_fraction_1km", 0.0) or 0.0)
        builtup_frac = float(event_dict.get("builtup_fraction_1km", 0.0) or 0.0)
        duration_hrs = float(event_dict.get("duration_hours", 0.0) or 0.0)

        explanations = []
        scores = {c: 0.0 for c in TAXONOMY_CLASSES if c != "unknown_requires_verification"}

        # Rule 1: Persistent Industrial Source (Must have facility proximity AND high persistence/active days)
        if dist_fac <= self.facility_dist_km and active_days >= 10.0:
            scores["persistent_industrial_source"] += 0.8
            explanations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name="distance_to_facility_km",
                feature_value=dist_fac,
                unit="km",
                direction="BELOW",
                importance=0.4,
                source="OSM Facility Proximity",
                description="Close facility proximity combined with high 30-day active days indicator."
            ))
        elif dist_fac <= self.facility_dist_km:
            # Facility proximity ALONE gives low partial score, not triggering classification alone
            scores["persistent_industrial_source"] += 0.2
            explanations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name="distance_to_facility_km",
                feature_value=dist_fac,
                unit="km",
                direction="BELOW",
                importance=0.1,
                source="OSM Facility Proximity",
                description="Proximity to facility detected, but insufficient temporal persistence for industrial classification."
            ))

        # Rule 2: Industrial Fire or Abnormal Event (Refinery/Factory + high FRP or abnormally high duration)
        if (near_refinery or near_factory or builtup_frac >= self.builtup_threshold) and max_frp >= self.high_frp_mw:
            scores["industrial_fire_or_abnormal_event"] += 0.75
            explanations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name="max_frp_mw",
                feature_value=max_frp,
                unit="MW",
                direction="ABOVE",
                importance=0.5,
                source="FIRMS FRP Intensity",
                description="High FRP intensity near refinery/factory or high built-up land cover."
            ))

        # Rule 3: Mining or Other Industrial Activity (Mine/Quarry proximity + recurrence/builtup)
        if (near_mine or near_quarry) and (dist_fac <= self.facility_dist_km or builtup_frac > 0.1):
            scores["mining_or_other_industrial_activity"] += 0.85
            explanations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name="near_mine",
                feature_value=float(near_mine or near_quarry),
                unit=None,
                direction="TRUE",
                importance=0.6,
                source="OSM Mining Context",
                description="Confirmed proximity to active mine or quarry zone."
            ))

        # Rule 4: Wildfire or Forest Fire (High forest cover + spatial extent/duration, low builtup/facility)
        if forest_frac >= self.forest_threshold and dist_fac > self.facility_dist_km:
            scores["wildfire_or_forest_fire"] += 0.8
            explanations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name="forest_fraction_1km",
                feature_value=forest_frac,
                unit="fraction",
                direction="ABOVE",
                importance=0.5,
                source="WorldCover Land Cover",
                description="Dominant forest cover away from industrial facility infrastructure."
            ))

        # Rule 5: Agricultural Burning (High crop cover + transient duration/low active days)
        if crop_frac >= self.crop_threshold and active_days < 5.0 and dist_fac > self.facility_dist_km:
            scores["agricultural_burning"] += 0.75
            explanations.append(ExplanationRecord(
                explanation_type=ExplanationType.OBSERVATION,
                feature_name="cropland_fraction_1km",
                feature_value=crop_frac,
                unit="fraction",
                direction="ABOVE",
                importance=0.4,
                source="WorldCover Land Cover",
                description="High cropland landcover fraction with transient thermal duration."
            ))

        # Calculate probabilities via Softmax over rule scores
        top_label = max(scores, key=scores.get)
        top_score = scores[top_label]

        # Decision Threshold: If top score is below threshold or ambiguous, return unknown_requires_verification
        if top_score < 0.5:
            predicted_label = "unknown_requires_verification"
            model_confidence = 0.0
        else:
            predicted_label = top_label
            model_confidence = float(top_score)

        # Normalize class probabilities
        exp_scores = {k: float(np.exp(v)) for k, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        class_probs = {k: v / sum_exp for k, v in exp_scores.items()}
        class_probs["unknown_requires_verification"] = 1.0 - sum(class_probs.values()) if predicted_label == "unknown_requires_verification" else 0.0

        return PredictionContract(
            event_id=event_id,
            prediction_status=PredictionStatus.PREDICTION_AVAILABLE,
            predicted_label=predicted_label,
            model_confidence=model_confidence,
            evidence_confidence=model_confidence,
            data_quality=DataQuality.HIGH if max_frp > 0 else DataQuality.MEDIUM,
            class_probabilities=class_probs,
            evidence=[],
            explanations=explanations,
            model_version="RULE_BASED_V1",
            prediction_timestamp="N/A",
            verification_state=VerificationState.MODEL_PREDICTION_REQUIRES_VERIFICATION
        )

    def predict(self, X):
        records = X.to_dict('records') if isinstance(X, pd.DataFrame) else X
        return [self.predict_event(r).predicted_label for r in records]

# Backward compatibility alias
RuleBasedBaseline = RuleBasedClassifier


