"""
Run Pipeline Script — Executes the full ThermoTrace temporal & classification pipeline on sample events.
"""
import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "services", "temporal_intelligence"))
sys.path.insert(0, os.path.join(ROOT, "services", "classification"))

from services.temporal_intelligence.thermotrace_temporal.pipeline import analyze_event
from services.classification.inference import adapt_inference_event

def run():
    print("=== Executing ThermoTrace Full GeoAI Pipeline ===")
    
    sample_obs = [{
        "observation_id": "OBS_PIPE_001",
        "latitude": 22.4707,
        "longitude": 70.0577,
        "timestamp_utc": "2026-09-01T12:00:00",
        "frp": 128.5,
        "brightness": 345.2,
        "confidence": 95.0,
        "satellite": "VIIRS_NPP"
    }]
    
    fac_context = {
        "facility_id": "FAC_JAMNAGAR_01",
        "facility_type": "refinery",
        "facility_distance_km": 0.12,
        "landcover_class": "builtup"
    }
    
    # 1. Temporal Intelligence Engine Analysis
    temporal_output = analyze_event(observations=sample_obs, facility_context=fac_context)
    print(f"1. Temporal Analysis Complete: Event ID = {temporal_output.get('event_id')}")
    print(f"   Industrial Likelihood: {temporal_output.get('industrial_likelihood', {}).get('score')}")
    print(f"   Operational Risk: {temporal_output.get('operational_risk', {}).get('risk_score')}")
    
    # 2. AI Model Classification Analysis
    ml_feature_dict = {
        "event_id": temporal_output.get("event_id"),
        "distance_to_facility_km": 0.12,
        "active_days_previous_30d": 34,
        "builtup_fraction_1km": 0.78,
        "near_refinery": True
    }
    classification_output = adapt_inference_event(ml_feature_dict)
    print(f"2. AI Classification Complete: Label = {classification_output.predicted_label}")
    print(f"   Confidence = {classification_output.model_confidence}")
    print(f"   Model Version = {classification_output.model_version}")

if __name__ == "__main__":
    run()
