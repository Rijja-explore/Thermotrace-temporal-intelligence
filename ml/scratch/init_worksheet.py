import pandas as pd
from pathlib import Path

# Load candidates
candidates = pd.read_csv('ml/data/candidate_events_batch_001.csv')

# Create reviewer worksheet
cols = [
    "event_id",
    "label",
    "reviewer_1", "reviewer_1_confidence", "reviewer_1_evidence_urls", "reviewer_1_evidence_type", "reviewer_1_notes", "reviewer_1_date",
    "reviewer_2", "reviewer_2_confidence", "reviewer_2_evidence_urls", "reviewer_2_evidence_type", "reviewer_2_notes", "reviewer_2_date",
    "final_label", "final_label_confidence", "consensus_status", "consensus_notes", "final_evidence_urls", "final_evidence_type", "label_date", "label_version"
]

ws = pd.DataFrame(columns=cols)
ws['event_id'] = candidates['event_id']

# Save worksheet
ws.to_csv('ml/data/batch_001_reviewer_worksheet.csv', index=False)

# Adjudication queue initially empty, but we can just touch the file
pd.DataFrame(columns=cols).to_csv('ml/data/batch_001_adjudication_queue.csv', index=False)
