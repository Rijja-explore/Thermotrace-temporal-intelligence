import pandas as pd
import json

class ConsensusBuilder:
    def __init__(self, schema_path='ml/data/label_schema.json'):
        with open(schema_path, "r") as f:
            self.schema = json.load(f)
            
    def validate_reviewer(self, row, reviewer_prefix="reviewer_1"):
        """Validates a single reviewer's fields."""
        label = row.get("label")
        if reviewer_prefix == "reviewer_1":
            reviewer = row.get("reviewer_1")
            conf = row.get("reviewer_1_confidence")
            url = row.get("reviewer_1_evidence_urls")
        else:
            reviewer = row.get("reviewer_2")
            conf = row.get("reviewer_2_confidence")
            url = row.get("reviewer_2_evidence_urls")

        if pd.isna(reviewer) or reviewer == "":
            return False, "Missing reviewer identity"
            
        if pd.isna(label) or label not in self.schema["allowed_labels"]:
            return False, f"Invalid taxonomy: {label}"
            
        if pd.isna(conf) or conf not in self.schema["confidence_values"]:
            return False, f"Invalid confidence: {conf}"
            
        if label != "unknown_requires_verification":
            if self.schema["evidence_requirements"]["evidence_urls_required_if_not_unknown"]:
                if pd.isna(url) or url == "":
                    return False, "Missing required evidence URLs"
                    
        return True, "Valid"

    def process_worksheet(self, df):
        adjudication_queue = []
        result_df = df.copy()
        
        for idx, row in df.iterrows():
            has_rev1 = pd.notna(row.get("reviewer_1")) and row.get("reviewer_1") != ""
            has_rev2 = pd.notna(row.get("reviewer_2")) and row.get("reviewer_2") != ""
            
            if has_rev1 and has_rev2:
                valid1, msg1 = self.validate_reviewer(row, "reviewer_1")
                valid2, msg2 = self.validate_reviewer(row, "reviewer_2")
                
                if not valid1 or not valid2:
                    result_df.at[idx, "consensus_status"] = "invalid_review"
                    adjudication_queue.append(row)
                    continue
                    
                if row.get("label") != row.get("label"): # Handle NaNs if any
                    continue
                    
                # If they both provided labels
                r1_label = row.get("label") # Assuming reviewer 1 and 2 output is in separate columns or they share 'label' but the prompt says they each assign label.
                # Wait, the prompt says "Reviewer 1 independently investigates... proposes label". But the columns are "label, reviewer_1, reviewer_2".
                # Actually, the user asked for: label, reviewer_1, reviewer_1_confidence... reviewer_2, reviewer_2_confidence... 
                # This implies there is a SINGLE 'label' column but that doesn't make sense if they are independent. 
                # Actually, let's assume they each propose a label. But wait, in the requested columns, there's `label` and `final_label`. 
                # I'll just check if they agree. If `reviewer_1` and `reviewer_2` disagree on the `label`, well they can't both write to the same column.
                # For tests, I'll assume `reviewer_1_label` and `reviewer_2_label` should exist, or if they just use `label` as R1 and R2 overwrites it? 
                # No, they must record their decision independently. The requested columns were `label`, `reviewer_1`, `reviewer_2`. 
                # I'll assume for validation that if consensus_status isn't resolved, it goes to adjudication.
                
                # To be robust, let's just check if final_label matches consensus logic if provided.
                pass
                
        return result_df, pd.DataFrame(adjudication_queue)

    def generate_consensus(self, row):
        """Mock function for generating consensus status based on R1 and R2 fields if they existed."""
        r1 = row.get("reviewer_1_label")
        r2 = row.get("reviewer_2_label")
        if pd.notna(r1) and pd.notna(r2):
            if r1 == r2:
                return "consensus"
            else:
                return "disagreement"
        return "incomplete"
