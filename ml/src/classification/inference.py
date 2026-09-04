from typing import Dict, Any, Union
import pandas as pd
from datetime import datetime
from .prediction import PredictionContract, fail_prediction
from .features import validate_features
from .explainability import ObservationSummarizer, ModelExplanationInterface

def adapt_inference_event(event_data: Union[Dict[str, Any], pd.Series]) -> PredictionContract:
    """
    Adapter bridging the raw incoming event features to the standard PredictionContract.
    Currently hardcoded to fail cleanly, because the model is in the NOT_TRAINED lifecycle state.
    """
    if isinstance(event_data, pd.Series):
        event_data = event_data.to_dict()
        
    event_id = event_data.get("event_id")
    if not event_id:
        raise ValueError("Missing event_id in event data")

    from .features import APPROVED_FEATURES, EXCLUDED_FEATURES
    
    # We explicitly extract APPROVED_FEATURES to run through the validation boundary.
    # However, to prevent a silent-drop security vulnerability, any explicitly prohibited
    # leakage feature or synthetic risk score MUST be passed into validate_features() 
    # so that it forcefully triggers rejection.
    # Legitimate operational metadata (timestamps, identifiers) are gracefully ignored.
    
    keys_to_validate = []
    for k in event_data.keys():
        if k in APPROVED_FEATURES:
            keys_to_validate.append(k)
        elif k in EXCLUDED_FEATURES:
            # Operational identifiers and unencoded categoricals are allowed to be dropped
            if k == "event_id" or k.endswith("_id") or k == "landcover_class":
                continue
            # All other EXCLUDED_FEATURES are leakage/synthetics. Pass them so it fails.
            keys_to_validate.append(k)
        elif "baseline_risk" in k or "events_local_" in k or "thermal_density_" in k:
            # Catch dynamic variations of leakages
            keys_to_validate.append(k)
            
    try:
        # We validate the keys through the approved registry
        valid_keys = validate_features(keys_to_validate)
    except ValueError as e:
        raise ValueError(f"Invalid feature schema: {e}")
        
    # Generate structured observations for the evidence layer
    valid_feature_dict = {k: event_data[k] for k in valid_keys if k in event_data}
    observations = ObservationSummarizer.summarize(valid_feature_dict)

    # For now, immediately return the untrained prediction (with observations attached)
    return fail_prediction(event_id, explanations=observations)
