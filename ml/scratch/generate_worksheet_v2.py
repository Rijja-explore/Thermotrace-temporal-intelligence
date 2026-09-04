import pandas as pd

# Load pilot features
feat = pd.read_parquet('ml/data/candidate_events_pilot_001_features.parquet')

# Desired context columns (if they exist)
ctx_cols = [
    'centroid_lat', 'centroid_lon', 'start_time', 'end_time', 
    'max_frp_mw', 'duration_hours', 'detection_count', 
    'distance_to_facility_km', 'events_previous_30d',
    'forest_fraction_1km', 'cropland_fraction_1km'
]

available_ctx = [c for c in ctx_cols if c in feat.columns]

# Create new worksheet structure
rows = []
for idx, row in feat.iterrows():
    # Base dictionary from context
    base = {c: row[c] for c in available_ctx}
    base['event_id'] = row['event_id']
    
    # Add Reviewer 1 row
    r1 = base.copy()
    r1['reviewer_id'] = 'reviewer_1'
    r1['label'] = ''
    r1['label_confidence'] = ''
    r1['evidence_urls'] = ''
    r1['evidence_summary'] = ''
    r1['reviewer_notes'] = ''
    r1['review_complete'] = 'FALSE'
    rows.append(r1)
    
    # Add Reviewer 2 row
    r2 = base.copy()
    r2['reviewer_id'] = 'reviewer_2'
    r2['label'] = ''
    r2['label_confidence'] = ''
    r2['evidence_urls'] = ''
    r2['evidence_summary'] = ''
    r2['reviewer_notes'] = ''
    r2['review_complete'] = 'FALSE'
    rows.append(r2)

ws_df = pd.DataFrame(rows)

# Reorder columns to put reviewer fields first, context later
rev_cols = ['event_id', 'reviewer_id', 'label', 'label_confidence', 'evidence_urls', 'evidence_summary', 'reviewer_notes', 'review_complete']
final_cols = rev_cols + available_ctx
ws_df = ws_df[final_cols]

ws_df.to_csv('ml/data/pilot_001_reviewer_worksheet_v2.csv', index=False)
print("Generated v2 worksheet with", len(ws_df), "rows.")
