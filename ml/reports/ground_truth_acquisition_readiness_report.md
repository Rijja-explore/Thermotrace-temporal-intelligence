# Ground Truth Acquisition Readiness Report

## Current Verified Labels
- **persistent_industrial_source**: 0
- **industrial_fire_or_abnormal_event**: 0
- **wildfire_or_forest_fire**: 0
- **agricultural_burning**: 0
- **mining_or_other_industrial_activity**: 0
*(Note: 'unknown_requires_verification' is an epistemic state, not a semantic label)*

## Current Invalid/Non-Ground-Truth Records
- **AI-assisted only / unresolved**: 5
- **heuristic/context only**: 0
- **unreviewed**: 40
- **unresolved conflicts**: 0
- **conflicting**: 0

## Acquisition Coverage (Batch 002 Planned)
- **Total Candidates**: 100
- **HIGH_PRIORITY**: 50
- **RANDOM_CONTROL**: 20
- **FACILITY_MATCHED_LOW_PRIORITY**: 15
- **HIGH_FRP_UNMATCHED**: 15

## Selection Bias Diagnostics
The acquisition batch is deterministically stratified. If only high-priority events were labelled, the classifier would learn a distorted conditional distribution (bias). By enforcing a sampling strategy that includes `RANDOM_CONTROL` and `FACILITY_MATCHED_LOW_PRIORITY`, the ground-truth pipeline actively protects against selection bias.

## Training Readiness
`TRAINING_BLOCKED_NO_VERIFIED_GROUND_TRUTH`

Supervised semantic training is scientifically blocked because the exact verified-label counts across all taxonomy classes are 0. No fake labels or heuristic proxies have been injected.
