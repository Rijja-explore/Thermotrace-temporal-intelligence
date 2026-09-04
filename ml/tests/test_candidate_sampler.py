import pytest
import pandas as pd
from pathlib import Path
from src.candidate_sampler import CandidateSampler
from src.feature_schema import FeatureSchemaValidator
import json

@pytest.fixture
def mock_schema(tmp_path):
    schema = {
        "safe_post_event_features": ["max_frp_mw"],
        "safe_temporal_context": ["events_previous_30d"],
        "safe_environmental_infrastructure_context": ["distance_to_facility_km"],
        "excluded_features": ["baseline_risk_score", "state"],
        "excluded_wildcard_patterns": ["*_risk_component"]
    }
    path = tmp_path / "schema.json"
    with open(path, "w") as f:
        json.dump(schema, f)
    return path

@pytest.fixture
def mock_df():
    data = {
        "event_id": [f"E{i}" for i in range(100)],
        "centroid_lat": [20.0 + i*0.01 for i in range(100)],
        "centroid_lon": [80.0 + i*0.01 for i in range(100)],
        "max_frp_mw": [10.0 + i for i in range(100)],
        "distance_to_facility_km": [0.5 if i % 2 == 0 else 10.0 for i in range(100)],
        "events_previous_30d": [0 if i % 3 == 0 else 5 for i in range(100)],
        "duration_hours": [0, 5] * 50,
        "builtup_fraction_1km": [0.0] * 100,
        "baseline_risk_score": [50.0] * 100, # Leakage feature
        "thermal_risk_component": [10.0] * 100 # Wildcard Leakage
    }
    return pd.DataFrame(data)

def test_sampler_reproducibility(mock_df, mock_schema):
    validator = FeatureSchemaValidator(mock_schema)
    sampler1 = CandidateSampler(mock_df, validator, seed=42)
    sampler2 = CandidateSampler(mock_df, validator, seed=42)
    
    out1 = sampler1.get_stratified_sample(n_target=20)
    out2 = sampler2.get_stratified_sample(n_target=20)
    
    assert (out1["event_id"] == out2["event_id"]).all()
    
def test_leakage_exclusion(mock_df, mock_schema):
    validator = FeatureSchemaValidator(mock_schema)
    sampler = CandidateSampler(mock_df, validator, seed=42)
    out = sampler.get_stratified_sample(n_target=20)
    
    filtered = sampler.filter_leakage_features(out)
    assert "baseline_risk_score" not in filtered.columns
    assert "thermal_risk_component" not in filtered.columns
    assert "max_frp_mw" in filtered.columns
    
def test_no_duplicate_ids(mock_df, mock_schema):
    validator = FeatureSchemaValidator(mock_schema)
    sampler = CandidateSampler(mock_df, validator, seed=42)
    out = sampler.get_stratified_sample(n_target=50)
    assert out["event_id"].is_unique
    
def test_sampling_metadata_presence(mock_df, mock_schema):
    validator = FeatureSchemaValidator(mock_schema)
    sampler = CandidateSampler(mock_df, validator, seed=42)
    out = sampler.get_stratified_sample(n_target=20)
    assert "sampling_stratum" in out.columns
    assert "sampling_reason" in out.columns
    assert "sampling_batch" in out.columns
