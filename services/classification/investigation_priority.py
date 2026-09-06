import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .features import validate_features, ABLATION_GROUPS, APPROVED_FEATURES
from .explainability import ObservationSummarizer, ExplanationRecord

@dataclass
class PrioritizationResult:
    event_id: str
    priority_score: float
    priority_tier: str  # e.g., "HIGH", "MEDIUM", "LOW"
    explanations: List[ExplanationRecord]
    diagnostics: Dict[str, Any]

class InvestigationPrioritizer:
    def __init__(self, ablation_group: str = "D"):
        """
        Initializes the prioritizer with an ablation group setting:
        A: Thermal only
        B: Thermal + Temporal
        C: Thermal + Temporal + Environmental
        D: Thermal + Temporal + Environmental + Infrastructure
        """
        if ablation_group not in ABLATION_GROUPS:
            raise ValueError(f"Invalid ablation group: {ablation_group}")
        self.ablation_group = ablation_group
        self.allowed_features = ABLATION_GROUPS[ablation_group]
        
        # We use IsolationForest as a label-free unsupervised anomaly detection mechanism.
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, df: pd.DataFrame):
        """Fits the unsupervised isolation forest on historical unlabeled data."""
        # Clean down to exactly what is allowed by the ablation group and approved by registry
        safe_cols = [c for c in df.columns if c in self.allowed_features and c in APPROVED_FEATURES]
        # Ensure we explicitly validate to catch any explicit leakages (they will crash)
        valid_cols = validate_features(safe_cols)
        
        X = df[valid_cols].fillna(0)
        if len(X) == 0:
            raise ValueError("No valid features remaining for prioritization model.")
            
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        self.train_cols = valid_cols

    def _deterministic_baseline(self, features: Dict[str, Any]) -> float:
        """
        A fallback deterministic ranking mechanism prioritizing extreme FRP and repetition.
        Higher score = higher priority.
        """
        score = 0.0
        # Thermal size/intensity
        score += features.get("max_frp_mw", 0) * 0.1
        score += features.get("detection_count", 0) * 1.0
        # Temporal persistence
        score += features.get("events_previous_30d", 0) * 5.0
        # Infrastructure context (not a semantic label, just an investigation routing metric)
        if features.get("distance_to_facility_km", 999) < 2.0:
            score += 20.0
        return score

    def rank_event(self, event_id: str, event_data: Dict[str, Any]) -> PrioritizationResult:
        """
        Ranks a single event, explicitly mapping it to an investigation priority, NOT a semantic class.
        """
        from .features import EXCLUDED_FEATURES
        keys_to_validate = []
        for k in event_data.keys():
            if k in self.allowed_features and k in APPROVED_FEATURES:
                keys_to_validate.append(k)
            elif k in EXCLUDED_FEATURES:
                if k == "event_id" or k.endswith("_id") or k == "landcover_class":
                    continue
                keys_to_validate.append(k)
            elif "baseline_risk" in k or "events_local_" in k or "thermal_density_" in k:
                keys_to_validate.append(k)
                
        # Pass through strict validation (will crash if leakages were appended)
        valid_keys = validate_features(keys_to_validate)
        
        feature_dict = {k: event_data[k] for k in valid_keys if k in event_data}
        
        # Explainability: only output factual observations
        explanations = ObservationSummarizer.summarize(feature_dict)
        
        # Compute ML Novelty / Anomaly Score (if fitted), else fallback to deterministic
        anomaly_score = None
        if self.is_fitted:
            X_df = pd.DataFrame([feature_dict])
            # Ensure all columns present
            for c in self.train_cols:
                if c not in X_df.columns:
                    X_df[c] = 0.0
            X_df = X_df[self.train_cols].fillna(0)
            X_scaled = self.scaler.transform(X_df)
            
            # IsolationForest decision_function returns > 0 for normal, < 0 for anomalies.
            # We want higher score = higher investigation priority (more anomalous).
            anomaly_score = float(-self.model.decision_function(X_scaled)[0])
        
        baseline_score = self._deterministic_baseline(feature_dict)
        
        # Combine or select scoring mechanism. We use a hybrid for robustness.
        final_score = baseline_score
        if anomaly_score is not None:
            final_score += (anomaly_score * 50)  # scale anomaly to impact baseline
            
        # Assign Tier
        tier = "LOW"
        if final_score > 50:
            tier = "HIGH"
        elif final_score > 20:
            tier = "MEDIUM"
            
        diagnostics = {
            "baseline_score": baseline_score,
            "anomaly_score": anomaly_score,
            "ablation_group": self.ablation_group
        }
        
        return PrioritizationResult(
            event_id=event_id,
            priority_score=final_score,
            priority_tier=tier,
            explanations=explanations,
            diagnostics=diagnostics
        )
