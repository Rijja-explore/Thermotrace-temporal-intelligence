import pytest
import json
from pathlib import Path
from src.feature_schema import FeatureSchemaValidator

@pytest.fixture
def temp_schema(tmp_path):
    schema = {
        "safe_post_event_features": ["feature_a"],
        "safe_temporal_context": ["feature_b"],
        "safe_environmental_infrastructure_context": ["feature_c"],
        "excluded_features": ["bad_feature", "event_id"],
        "excluded_wildcard_patterns": ["*_risk_component"]
    }
    schema_path = tmp_path / "feature_schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f)
    return schema_path

def test_valid_features(temp_schema):
    validator = FeatureSchemaValidator(temp_schema)
    cols = ["feature_a", "feature_b"]
    approved = validator.validate_features(cols)
    assert set(approved) == set(cols)
    
def test_explicitly_excluded_feature(temp_schema):
    validator = FeatureSchemaValidator(temp_schema)
    cols = ["feature_a", "event_id"]
    with pytest.raises(ValueError, match="Attempted to use excluded/leakage features: event_id"):
        validator.validate_features(cols)
        
def test_wildcard_excluded_feature(temp_schema):
    validator = FeatureSchemaValidator(temp_schema)
    cols = ["feature_c", "thermal_risk_component"]
    with pytest.raises(ValueError, match="Matches excluded pattern \\*_risk_component"):
        validator.validate_features(cols)
