# Pilot 001 Human Review Handoff

## Purpose
The purpose of this pilot is to establish human-labeled semantic ground truth for thermal anomalies independently and test the labeling workflow.

## The Pilot Batch
You are reviewing exactly 40 candidate thermal events. You are provided with contextual evidence (e.g., location, FRP, duration, proximity) within your reviewer spreadsheet.

## Required Independent Review
- You MUST work independently.
- You MUST NOT view the other reviewer's spreadsheet or discuss decisions before completion.

## Your Assignment
1. **File to Open**: 
   - Reviewer 1: Open `ml/data/pilot_001_REVIEWER_1.csv`
   - Reviewer 2: Open `ml/data/pilot_001_REVIEWER_2.csv`
2. **Columns to Fill**:
   - `label`
   - `label_confidence`
   - `evidence_urls`
   - `evidence_summary`
   - `reviewer_notes`
   - `review_complete`

## The Taxonomy (Permitted Labels)
- `persistent_industrial_source`
- `industrial_fire_or_abnormal_event`
- `wildfire_or_forest_fire`
- `agricultural_burning`
- `mining_or_other_industrial_activity`
- `unknown_requires_verification`

## Incomplete vs Unknown
- **Incomplete**: You have not investigated the event. `review_complete` = `FALSE`.
- **Unknown**: You investigated fully, but the available evidence is conflicting or insufficient to assign one of the 5 substantive classes. Record `label` = `unknown_requires_verification` and `review_complete` = `TRUE`.

## Evidence Requirements
You must obtain external evidence (e.g., optical imagery, news, mapping context). Record your reasoning in `evidence_summary` and paste links in `evidence_urls`. 

## Return Procedure
1. Mark `review_complete` = `TRUE` for all 40 rows when finished.
2. Save your file EXACTLY as your original filename (e.g., `pilot_001_REVIEWER_1_COMPLETED.csv`).
3. Return the file to the lead engineer.
