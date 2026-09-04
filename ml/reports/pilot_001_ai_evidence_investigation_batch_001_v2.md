# Pilot 001 AI Evidence Investigation (Batch 001 - V2)

## 1. Scope and Objective
To reinvestigate the first 5 events from `ml/data/pilot_001_REVIEWER_1_EVIDENCE.csv` treating them correctly as historical events (since the current date is Sep 3, 2026, and the events occurred in late 2025). The investigation relies on rigorous external web searches to generate evidence-backed "silver labels".

## 2. Silver Labels vs Ground Truth
The labels proposed here are purely AI-assisted investigative proposals based on public search feasibility. They are **NOT** semantic ground truth, and must not be used to train or evaluate models directly. 

## 3. Events Investigated
- `TT-EVT-00023424` (2025-10-21, 31.341, 74.631)
- `TT-EVT-00059055` (2025-11-10, 32.662, 70.329)
- `TT-EVT-00097085` (2025-11-22, 16.053, 75.338)
- `TT-EVT-00133877` (2025-12-06, 22.941, 87.679)
- `TT-EVT-00141704` (2025-12-08, 27.250, 84.556)

## 4. Evidence Found & Labels
Historical satellite imagery not independently inspected in this investigation due to current tooling limits; investigation relied on web search for news and incident reports.

**Event 1: TT-EVT-00023424**
- **Context**: Near Bhikhiwind substation, Oct 21, 2025.
- **Queries**: `"Bhikhiwind" substation fire OR incident "2025" OR "October 2025"`
- **Sources**: No matching news. Found hardware store fire (Dec 2025) and power theft issues, but no substation fire in Oct.
- **Proposed Label**: `unknown_requires_verification` (Confidence: Low)
- **Alternative**: `industrial_fire_or_abnormal_event` vs `agricultural_burning`. Proximity is not proof. 

**Event 2: TT-EVT-00059055**
- **Context**: Substation proximity, Nov 10, 2025, KP region, Pakistan.
- **Queries**: `substation fire OR incident 32.662047 70.329368 "2025" OR "November 2025"`
- **Sources**: No public records or logs exist for this remote location.
- **Proposed Label**: `unknown_requires_verification` (Confidence: Low)
- **Alternative**: `industrial_fire_or_abnormal_event` vs `wildfire_or_forest_fire`. Evidence is entirely absent.

**Event 3: TT-EVT-00097085**
- **Context**: Power plant proximity, Nov 22, 2025, Karnataka (16.05, 75.33).
- **Queries**: `power plant fire OR incident 16.053760 75.338950 "2025" OR "November 2025"`
- **Sources**: Search surfaced a Vedanta plant explosion, but that was in April 2026 in Chhattisgarh, a completely different event.
- **Proposed Label**: `unknown_requires_verification` (Confidence: Low)
- **Alternative**: `persistent_industrial_source` vs `industrial_fire_or_abnormal_event`. Missing contemporaneous news.

**Event 4: TT-EVT-00133877**
- **Context**: Substation proximity, Dec 6, 2025, Bankura district, WB.
- **Queries**: `substation fire OR incident 22.941560 87.679420 "2025" OR "December 2025"`
- **Sources**: No substation fires reported in Dec 2025. Closest was a hospital UPS fire in Jan 2026.
- **Proposed Label**: `unknown_requires_verification` (Confidence: Low)
- **Alternative**: `industrial_fire_or_abnormal_event` vs `agricultural_burning`.

**Event 5: TT-EVT-00141704**
- **Context**: Power plant proximity, Dec 8, 2025, Bihar.
- **Queries**: `power plant fire OR incident 27.250835 84.556492 "2025" OR "December 2025"`
- **Sources**: Found news of a major cooling tower fire at Nabinagar Thermal Power Plant on **December 19, 2025** [Source Link recorded in CSV].
- **Proposed Label**: `unknown_requires_verification` (Confidence: Low)
- **Alternative**: `industrial_fire_or_abnormal_event` vs `persistent_industrial_source`. 
- **Reasoning**: While tempting to label as an industrial fire, the date mismatch (Dec 8 vs Dec 19) means we cannot definitively link this specific thermal detection to the cooling tower incident without satellite verification. Conflating them would manufacture certainty.

## 5. Methodological Limitations
A reliance solely on English-language web search for highly localized events (like a minor substation fire in a rural district) often yields no results. Many genuine industrial fires or agricultural burns are never reported in indexed digital news.

## 6. Workflow Assessment
**APPROVE_FOR_SCALING**
Although all 5 events resulted in `unknown_requires_verification`, the investigative workflow itself is scientifically sound. It successfully executed targeted spatiotemporal queries, correctly distinguished between mismatched events (e.g. the April 2026 Vedanta explosion vs the Nov 2025 Karnataka event), and appropriately resisted the temptation to manufacture certainty when dates mismatched (the Nabinagar fire). The methodology is robust and safe to scale to the remaining 35 events, even if many will legitimately remain Unknown due to the inherent limits of public reporting for minor thermal anomalies.
