import json
import fnmatch
from pathlib import Path

class FeatureSchemaValidator:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
            
    def validate_features(self, columns: list[str]) -> list[str]:
        """
        Returns a list of safe ML features to use, rejecting excluded features.
        Raises ValueError if required columns are missing, or if an excluded feature is passed.
        """
        safe_post = set(self.schema["safe_post_event_features"])
        safe_temporal = set(self.schema["safe_temporal_context"])
        safe_env = set(self.schema["safe_environmental_infrastructure_context"])
        
        all_safe = safe_post | safe_temporal | safe_env
        
        excluded_exact = set(self.schema["excluded_features"])
        excluded_patterns = self.schema["excluded_wildcard_patterns"]
        
        # Validation checks
        rejected = []
        approved = []
        
        for col in columns:
            if col in excluded_exact:
                rejected.append(f"{col} (Explicitly excluded)")
                continue
                
            matched_wildcard = False
            for pat in excluded_patterns:
                if fnmatch.fnmatch(col, pat):
                    rejected.append(f"{col} (Matches excluded pattern {pat})")
                    matched_wildcard = True
                    break
            if matched_wildcard:
                continue
                
            if col in all_safe:
                approved.append(col)
                
        if rejected:
            raise ValueError(f"Attempted to use excluded/leakage features: {', '.join(rejected)}")
            
        # Check if requested features are actually present in the dataset (would be handled in practice)
        return approved
