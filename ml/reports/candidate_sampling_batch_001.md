# Candidate Sampling Batch 001 Report

**Target**: Provide 300-500 candidate events for human labeling.

## Overview
- **Candidate events**: 350
- **Source events**: 996,891
- **Sampling seed**: 42

## Strata Results
The sampling algorithm successfully retrieved candidates from the following target strata:
- `high_frp_no_facility`: 50
- `low_frp_near_facility`: 50
- `recurrent_weak_context`: 50
- `forest_near_infra`: 50
- `cropland_near_infra`: 50
- `isolated_high_confidence`: 50
- `random_baseline`: 50

*Note: The `persistent_non_industrial` stratum returned 0 valid candidates from the source dataset in this batch based on the 2.0hr / 0.1 built-up thresholds, indicating this combination is rare in this specific region/period.*

## Geographic Coverage
A localized grid capping strategy (`spatial_grid`) was applied, allowing a maximum of 3 candidates per 1x1 degree spatial grid cell per stratum. This successfully prevented the candidate batch from being geographically dominated by a single massive recurrent source (e.g., a single persistent gas flare).

## Schema Security
- Leakage features (e.g., `baseline_risk_score`, `events_local_1km`) have been **excluded** from the candidate feature Parquet.
- The CSV file for human reviewers contains explicit columns for consensus tracking and independent evidence URLs.

## Model Training Status
Model training is **NOT STARTED** and remains blocked solely by the absence of verified semantic labels.
