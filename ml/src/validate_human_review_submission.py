import pandas as pd
import json

class SubmissionValidator:
    def __init__(self, master_ids, reviewer_id):
        self.master_ids = set(master_ids)
        self.reviewer_id = reviewer_id
        self.allowed_labels = [
            "persistent_industrial_source",
            "industrial_fire_or_abnormal_event",
            "wildfire_or_forest_fire",
            "agricultural_burning",
            "mining_or_other_industrial_activity",
            "unknown_requires_verification"
        ]
        
    def validate(self, filepath):
        try:
            df = pd.read_csv(filepath)
        except Exception:
            return "INVALID_SUBMISSION", "Could not read file"
            
        # Structure checks
        if 'event_id' not in df.columns:
            return "INVALID_SUBMISSION", "Missing event_id column"
            
        if len(df) != 40:
            return "INVALID_SUBMISSION", f"Expected exactly 40 rows, found {len(df)}"
            
        if df['event_id'].nunique() != 40:
            return "INVALID_SUBMISSION", "Duplicate event IDs found"
            
        if set(df['event_id']) != self.master_ids:
            return "INVALID_SUBMISSION", "Event IDs do not match the expected pilot set"
            
        if 'reviewer_id' not in df.columns or (df['reviewer_id'] != self.reviewer_id).any():
            return "INVALID_SUBMISSION", f"Invalid or missing reviewer_id (expected {self.reviewer_id})"
            
        if 'review_complete' not in df.columns:
            return "INVALID_SUBMISSION", "Missing review_complete column"
            
        if not df['review_complete'].isin([True, False, 'True', 'False', 'TRUE', 'FALSE']).all():
            return "INVALID_SUBMISSION", "review_complete must be boolean"
            
        # Semantic checks
        incomplete_count = 0
        
        for idx, row in df.iterrows():
            comp = str(row['review_complete']).strip().upper() in ['TRUE', '1']
            
            if not comp:
                incomplete_count += 1
                continue
                
            # If complete, must have label
            label = row.get('label', '')
            if pd.isna(label) or str(label).strip() == '':
                return "INVALID_SUBMISSION", f"Row {idx} is marked complete but missing label"
                
            if str(label).strip() not in self.allowed_labels:
                return "INVALID_SUBMISSION", f"Row {idx} has invalid label: {label}"
                
            # Evidence checks
            ev_sum = row.get('evidence_summary', '')
            if pd.isna(ev_sum) or str(ev_sum).strip() == '':
                return "INVALID_SUBMISSION", f"Row {idx} is marked complete but missing evidence_summary"
                
            if str(label).strip() != 'unknown_requires_verification':
                ev_url = row.get('evidence_urls', '')
                if pd.isna(ev_url) or str(ev_url).strip() == '':
                    return "INVALID_SUBMISSION", f"Row {idx} is non-unknown but missing evidence_urls"
                    
            # Confidence
            conf = row.get('label_confidence', '')
            if pd.isna(conf) or str(conf).strip() == '':
                return "INVALID_SUBMISSION", f"Row {idx} is marked complete but missing label_confidence"
                
        if incomplete_count > 0:
            return "INCOMPLETE_SUBMISSION", f"{incomplete_count} rows are marked incomplete"
            
        return "VALID_COMPLETED_SUBMISSION", "All 40 rows complete and structurally valid"
