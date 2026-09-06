from typing import List, Dict, Any
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from .prediction import fail_prediction, PredictionContract, PredictionStatus, VerificationState, DataQuality

TAXONOMY_CLASSES = [
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
]

class BaseClassifier:
    def __init__(self, skip_verification: bool = False):
        self.trained = False
        self.skip_verification = skip_verification

    def fit(self, X, y):
        if y is None or len(y) == 0:
            raise ValueError("NO_VERIFIED_GROUND_TRUTH")
        
        for label in y:
            if label not in TAXONOMY_CLASSES:
                raise ValueError(f"Invalid taxonomy class: {label}")
                
        if not self.skip_verification and all(label == "unknown_requires_verification" for label in y):
            raise ValueError("NO_VERIFIED_GROUND_TRUTH")
            
        self.trained = True

    def predict(self, X):
        if not self.trained:
            raise ValueError("NO_VERIFIED_GROUND_TRUTH: Model not trained")
        return ["unknown_requires_verification"] * len(X)
        
    def predict_proba(self, X):
        if not self.trained:
            raise ValueError("NO_VERIFIED_GROUND_TRUTH: Model not trained")
        return None

class LogisticRegressionWrapper(BaseClassifier):
    def __init__(self, skip_verification: bool = False, **kwargs):
        super().__init__(skip_verification)
        self.model = LogisticRegression(**kwargs)
        
    def fit(self, X, y):
        super().fit(X, y)
        self.model.fit(X, y)
        
    def predict(self, X):
        super().predict(X)
        return self.model.predict(X)
        
    def predict_proba(self, X):
        super().predict_proba(X)
        return self.model.predict_proba(X)

class RandomForestWrapper(BaseClassifier):
    def __init__(self, skip_verification: bool = False, **kwargs):
        super().__init__(skip_verification)
        self.model = RandomForestClassifier(**kwargs)
        
    def fit(self, X, y):
        super().fit(X, y)
        self.model.fit(X, y)
        
    def predict(self, X):
        super().predict(X)
        return self.model.predict(X)
        
    def predict_proba(self, X):
        super().predict_proba(X)
        return self.model.predict_proba(X)

class HybridClassifier(BaseClassifier):
    """
    HybridClassifier combining ML probability outputs with transparent rule-based evidence signals.
    Preserves ML class probabilities while incorporating rule evidence transparently.
    Allows returning unknown_requires_verification when signals are weak/conflicting.
    """
    def __init__(self, ml_classifier=None, rule_classifier=None, ml_weight: float = 0.6, skip_verification: bool = False):
        super().__init__(skip_verification=skip_verification)
        if rule_classifier is None:
            from .baseline import RuleBasedClassifier
            rule_classifier = RuleBasedClassifier(skip_verification=skip_verification)
        self.ml_classifier = ml_classifier if ml_classifier is not None else RandomForestWrapper(skip_verification=skip_verification)
        self.rule_classifier = rule_classifier
        self.ml_weight = ml_weight
        self.rule_weight = 1.0 - ml_weight

    def fit(self, X, y):
        super().fit(X, y)
        self.ml_classifier.fit(X, y)
        self.rule_classifier.fit(X, y)

    def predict_event(self, event_dict: Dict[str, Any]) -> PredictionContract:
        # Get rule contract
        rule_contract = self.rule_classifier.predict_event(event_dict)
        
        # Get ML probabilities if ML model trained
        if self.ml_classifier.trained:
            # Predict single sample using fitted feature columns if available
            df_single = pd.DataFrame([event_dict])
            if hasattr(self.ml_classifier.model, "feature_names_in_"):
                cols = [c for c in self.ml_classifier.model.feature_names_in_ if c in df_single.columns]
                df_single = df_single[cols].fillna(0)
            ml_probs_raw = self.ml_classifier.predict_proba(df_single)[0]
            ml_classes = getattr(self.ml_classifier.model, "classes_", TAXONOMY_CLASSES[:5])
            ml_prob_map = {cls: float(prob) for cls, prob in zip(ml_classes, ml_probs_raw)}
        else:
            ml_prob_map = {c: 0.2 for c in TAXONOMY_CLASSES if c != "unknown_requires_verification"}

        # Combine ML probabilities with rule probabilities
        combined_probs = {}
        rule_probs = rule_contract.class_probabilities
        for c in TAXONOMY_CLASSES:
            if c == "unknown_requires_verification":
                continue
            ml_p = ml_prob_map.get(c, 0.0)
            rule_p = rule_probs.get(c, 0.0)
            combined_probs[c] = (self.ml_weight * ml_p) + (self.rule_weight * rule_p)

        top_label = max(combined_probs, key=combined_probs.get)
        top_prob = combined_probs[top_label]

        # Uncertainty check: if top probability < 0.25, preserve unknown_requires_verification
        if top_prob < 0.25:
            predicted_label = "unknown_requires_verification"
            model_conf = None
            evidence_conf = rule_contract.evidence_confidence
        else:
            predicted_label = top_label
            model_conf = float(top_prob)
            evidence_conf = rule_contract.evidence_confidence

        # Normalize output probabilities
        prob_sum = sum(combined_probs.values())
        norm_probs = {k: v / prob_sum for k, v in combined_probs.items()}
        norm_probs["unknown_requires_verification"] = 1.0 - sum(norm_probs.values()) if predicted_label == "unknown_requires_verification" else 0.0

        return PredictionContract(
            event_id=str(event_dict.get("event_id", "UNKNOWN")),
            prediction_status=PredictionStatus.PREDICTION_AVAILABLE,
            predicted_label=predicted_label,
            model_confidence=model_conf,
            evidence_confidence=evidence_conf,
            data_quality=rule_contract.data_quality,
            class_probabilities=norm_probs,
            evidence=rule_contract.evidence,
            explanations=rule_contract.explanations,
            model_version="HYBRID_V1",
            prediction_timestamp="N/A",
            verification_state=VerificationState.MODEL_PREDICTION_REQUIRES_VERIFICATION
        )

    def predict(self, X):
        super().predict(X)
        records = X.to_dict('records') if isinstance(X, pd.DataFrame) else X
        return [self.predict_event(r).predicted_label for r in records]

