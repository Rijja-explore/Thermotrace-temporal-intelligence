import pandas as pd
import json
from pathlib import Path

class LabelValidator:
    def __init__(self, schema_path: str | Path):
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
            
    def validate_labels(self, labels_df: pd.DataFrame, canonical_df: pd.DataFrame):
        errors = []
        
        # 1. Missing labels
        if labels_df.empty:
            return ["Labels dataset is empty."]
            
        # 2. Required fields
        for field in self.schema["required_fields"]:
            if field not in labels_df.columns:
                errors.append(f"Missing required field: {field}")
                
        if errors:
            return errors
            
        # 3. Duplicate event_ids
        if not labels_df["event_id"].is_unique:
            errors.append("Duplicate event_ids found in labels.")
            
        # 4. Valid event_id (exists in canonical)
        valid_ids = set(canonical_df["event_id"])
        invalid_ids = set(labels_df["event_id"]) - valid_ids
        if invalid_ids:
            errors.append(f"Found {len(invalid_ids)} event_ids in labels not present in canonical dataset.")
            
        for idx, row in labels_df.iterrows():
            # 5. Valid taxonomy
            if pd.notna(row.get("final_label")) and row["final_label"] not in self.schema["allowed_labels"]:
                errors.append(f"Row {idx}: Invalid final_label '{row['final_label']}'")
                
            # 6. Unknown requires verification logic
            if row.get("final_label") == "unknown_requires_verification":
                pass # valid label, but means it's unknown
                
            # 7. Reviewer disagreement
            rev1 = row.get("reviewer_1")
            rev2 = row.get("reviewer_2")
            if pd.notna(rev1) and pd.notna(rev2) and rev1 != rev2:
                # Need a final consensus
                if pd.isna(row.get("final_label")):
                    errors.append(f"Row {idx}: Reviewers disagree but no final_label provided.")
                    
            # 8. Evidence requirements
            if pd.notna(row.get("final_label")) and row["final_label"] != "unknown_requires_verification":
                if self.schema["evidence_requirements"]["evidence_urls_required_if_not_unknown"]:
                    if pd.isna(row.get("evidence_urls")) or str(row.get("evidence_urls")).strip() == "":
                        errors.append(f"Row {idx}: Evidence URL required for non-unknown label '{row['final_label']}'.")
                        
            # 9. Confidence values
            conf = row.get("label_confidence")
            if pd.notna(conf) and conf not in self.schema["confidence_values"]:
                errors.append(f"Row {idx}: Invalid confidence value '{conf}'.")
                
        return errors
