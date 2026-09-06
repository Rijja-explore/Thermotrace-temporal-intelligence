import os
import joblib
from typing import Dict, Any, Union, List
import pandas as pd
import numpy as np
from datetime import datetime

from .prediction import PredictionContract, PredictionStatus, VerificationState, DataQuality, fail_prediction
from .features import APPROVED_FEATURES, EXCLUDED_FEATURES, validate_features
from .explainability import ObservationSummarizer
from .baseline import RuleBasedClassifier

MODEL_PATH = os.path.join("models", "trained", "best_m4_class_balance_variant.joblib")
_MODEL_CACHE = None

TARGET_CLASSES = [
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "wildfire_or_forest_fire",
    "agricultural_burning",
    "mining_or_other_industrial_activity",
    "unknown_requires_verification"
]

def load_classifier_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    
    candidate_paths = [
        MODEL_PATH,
        os.path.join("models", "trained", "m3_random_forest.joblib"),
        os.path.join("models", "trained", "m2_logistic_regression.joblib"),
        os.path.join(os.path.dirname(__file__), "..", "..", "models", "trained", "best_m4_class_balance_variant.joblib"),
        os.path.join(os.path.dirname(__file__), "..", "..", "member2", "ml", "models", "benchmark", "m4_class_balance", "best_m4_class_balance_variant.joblib")
    ]
    for path in candidate_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            try:
                _MODEL_CACHE = joblib.load(abs_path)
                return _MODEL_CACHE
            except Exception:
                continue
    return None

def adapt_inference_event(event_data: Union[Dict[str, Any], pd.Series]) -> PredictionContract:
    """
    Adapter bridging incoming event features to PredictionContract.
    Evaluates ML model or transparent RuleBasedClassifier fallback.
    """
    if isinstance(event_data, pd.Series):
        event_data = event_data.to_dict()
        
    event_id = str(event_data.get("event_id", "UNKNOWN_EVENT"))

    keys_to_validate = []
    for k in event_data.keys():
        if k in APPROVED_FEATURES:
            keys_to_validate.append(k)
        elif k in EXCLUDED_FEATURES:
            if k == "event_id" or k.endswith("_id") or k == "landcover_class":
                continue
            keys_to_validate.append(k)
        elif "baseline_risk" in k or "events_local_" in k or "thermal_density_" in k:
            keys_to_validate.append(k)
            
    try:
        valid_keys = validate_features(keys_to_validate)
    except ValueError as e:
        return fail_prediction(event_id, explanations=[f"Leakage validation error: {e}"])
        
    valid_feature_dict = {k: float(event_data[k]) if isinstance(event_data[k], (int, float, np.number)) else event_data[k] 
                          for k in valid_keys if k in event_data}
    observations = ObservationSummarizer.summarize(valid_feature_dict)

    # 1. Attempt ML model inference
    model = load_classifier_model()
    if model is not None:
        try:
            expected_cols = getattr(model, "feature_names_in_", list(APPROVED_FEATURES))
            feature_vector = []
            for feat in expected_cols:
                val = valid_feature_dict.get(feat, 0.0)
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    val = 0.0
                feature_vector.append(float(val))
                
            df_feat = pd.DataFrame([feature_vector], columns=list(expected_cols))
            
            probs_raw = model.predict_proba(df_feat)[0]
            classes_in_model = getattr(model, "classes_", TARGET_CLASSES)
            
            probabilities = {}
            for cls_name, prob in zip(classes_in_model, probs_raw):
                probabilities[str(cls_name)] = round(float(prob), 4)
                
            for tc in TARGET_CLASSES:
                if tc not in probabilities:
                    probabilities[tc] = 0.0
                    
            best_label = max(probabilities.items(), key=lambda x: x[1])[0]
            confidence = probabilities[best_label]
            
            if confidence < 0.40:
                best_label = "unknown_requires_verification"
                
            return PredictionContract(
                event_id=event_id,
                prediction_status=PredictionStatus.PREDICTION_AVAILABLE,
                predicted_label=best_label,
                model_confidence=round(confidence, 4),
                evidence_confidence=round(confidence, 4),
                data_quality=DataQuality.HIGH,
                class_probabilities=probabilities,
                evidence=[],
                explanations=observations,
                model_version=f"ML_{type(model).__name__}_v1.0",
                prediction_timestamp=datetime.utcnow().isoformat(),
                verification_state=VerificationState.MODEL_PREDICTION_REQUIRES_VERIFICATION
            )
        except Exception as e:
            print(f"ML model prediction failed ({e}), falling back to rule-based classifier.")

    # 2. Rule-based model fallback
    rule_clf = RuleBasedClassifier()
    rule_result = rule_clf.predict_event(valid_feature_dict)
    
    return rule_result
