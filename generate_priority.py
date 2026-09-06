import pandas as pd
import json
import dataclasses
from src.classification.investigation_priority import InvestigationPrioritizer

df = pd.read_parquet('data/processed/features/event_features_v2.parquet')
event_df = df[df['event_id'] == 'TT-EVT-00141704']
event_dict = event_df.iloc[0].to_dict()

sample_df = df.sample(min(100, len(df)), random_state=42)

for group in ['A', 'B', 'C', 'D']:
    model = InvestigationPrioritizer(ablation_group=group)
    model.fit(sample_df)
    res = model.rank_event('TT-EVT-00141704', event_dict)
    
    print(f'=== Ablation Group {group} ===')
    print(f'Priority Score: {res.priority_score}')
    print(f'Priority Tier: {res.priority_tier}')
    print(f'Anomaly Score: {res.diagnostics["anomaly_score"]}')
    print(f'Explanation count: {len(res.explanations)}')

print('--- Canonical JSON Payload for Group D ---')
model = InvestigationPrioritizer(ablation_group='D')
model.fit(sample_df)
res = model.rank_event('TT-EVT-00141704', event_dict)
print(json.dumps(dataclasses.asdict(res), indent=2))
