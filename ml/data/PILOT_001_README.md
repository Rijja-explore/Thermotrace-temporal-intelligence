# Pilot 001 Reviewer Instructions

## Overview
This is a **40-event protocol pilot**. Its purpose is to test the human-labeling workflow before committing to the full 350-event batch.

## Protocol
- **Dual Independent Review**: Two reviewers must work completely independently.
- **No Early Peeking**: Neither reviewer should see the other's decisions before submitting their own results.
- **Disagreement is Valid**: Disagreement must be preserved in the final output. Do NOT force a classification just to agree.
- **Evidence Requirement**: Evidence (e.g. imagery URLs) must be recorded for non-unknown assignments.

## The Unknown Class
`unknown_requires_verification` is a completely valid scientific outcome. Use it if evidence is ambiguous, missing, or conflicting. 

## Semantic Taxonomy
1. `persistent_industrial_source`
2. `industrial_fire_or_abnormal_event`
3. `wildfire_or_forest_fire`
4. `agricultural_burning`
5. `mining_or_other_industrial_activity`
6. `unknown_requires_verification`

Pilot results will be used to improve the labeling protocol for the full batch.
