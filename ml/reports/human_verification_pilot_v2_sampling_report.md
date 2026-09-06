# Human Verification Pilot V2 — Sampling & Audit Report

## Executive Summary

This report documents the design, sampling methodology, and feature distribution of the **100-event Human Verification Pilot V2** (`pilot_v2`). The pilot is constructed from the $N=1,500$ candidate pool (`candidate_pool_v1.json`) using deterministic stratified sampling (random seed 42).

> [!IMPORTANT]
> **Scientific Disclaimer & Status Statement:**
> **"Pilot records are prepared for human verification; no human-verified labels exist until annotators complete the assignments."**
> AI-assisted V1 and V2 weak labels are stored separately and must NOT be treated as ground truth or used to train production classifiers or calculate model accuracy/F1.

---

## 1. Population & Sampling Parameters

| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **Total Candidate Population ($N$)** | 1,500 | Filtered candidate pool from 996,891 clustered events |
| **Pilot Sample Size ($n$)** | 100 | Stratified deterministic subset |
| **Random Seed** | `42` | `numpy.random.RandomState(42)` |
| **Double-Annotation Subset** | 30 events | Stratified toward ambiguity, Unknowns, and LOW confidence |
| **Single-Annotation Subset** | 70 events | Primary annotation set for broader coverage |
| **Storage Location** | `ml/data/ground_truth/human_verified/pilot_v2/` | Dedicated provenance area |

---

## 2. Sampling Strata & AI-Assisted V2 Class Breakdown

The 100-event pilot was intentionally sampled across six functional strata to ensure diverse coverage of thermal intensity, land cover, and infrastructure proximity:

| Sampling Stratum / AI V2 Class | Count ($n=100$) | Percentage | AI Confidence Breakdown (HIGH / MED / LOW) |
| :--- | :---: | :---: | :---: |
| **`mining_or_other_industrial_activity`** | 25 | 25.0% | 0 HIGH / 25 MED / 0 LOW |
| **`wildfire_or_forest_fire`** | 24 | 24.0% | 19 HIGH / 5 MED / 0 LOW |
| **`unknown_requires_verification`** | 20 | 20.0% | 0 HIGH / 0 MED / 20 LOW |
| **`agricultural_burning`** | 16 | 16.0% | 15 HIGH / 1 MED / 0 LOW |
| **`persistent_industrial_source`** | 15 | 15.0% | 0 HIGH / 15 MED / 0 LOW |
| **Industrial Fire Candidates** *(High FRP near facilities)* | 7* | 7.0% | Included across classes with max FRP up to 231.8 MW |
| **Total** | **100** | **100.0%** | **34 HIGH / 46 MED / 20 LOW** |

*\*Note: 7 events were intentionally sampled based on extreme thermal intensity (max FRP up to 231.8 MW) and proximity to facilities/built-up land cover as candidate industrial fire / abnormal event cases, even though current weak-label count for industrial fire is zero.*

---

## 3. Double vs. Single Annotation Allocation

To evaluate inter-annotator agreement (Cohen's kappa) without unnecessary labeling overhead, the 100 pilot events are partitioned into:

1. **Double-Annotation Subset ($n=30$)**: Assigned independently to Annotator 1 and Annotator 2 (`annotator_1_assignments.json` & `annotator_2_assignments.json`). Stratified toward:
   - Unknown / LOW confidence cases ($n=10$)
   - Industrial fire candidates with high FRP ($n=5$)
   - Mixed land-cover ambiguity (forest vs cropland) ($n=5$)
   - Industrial vs mining proximity ambiguity ($n=5$)
   - Medium-confidence persistent industrial cases ($n=5$)

2. **Single-Annotation Subset ($n=70$)**: Assigned to Annotator 1 for initial baseline validation.

---

## 4. Geographic & Feature Coverage

### Geographic Coverage
- **Latitude Range**: $6.6978^\circ \text{N}$ to $33.7299^\circ \text{N}$ (spanning southern tip to northern border).
- **Longitude Range**: $68.2003^\circ \text{E}$ to $97.1021^\circ \text{E}$ (spanning western coast to eastern states).

### Feature Boundaries Covered
- **Thermal FRP Range**: $0.46 \text{ MW}$ to $231.83 \text{ MW}$
- **Temporal Active Days (30d)**: $1 \text{ day}$ to $30 \text{ days}$
- **Facility Distance**: $0.05 \text{ km}$ to $999.0 \text{ km}$
- **Land Cover Fractions**: Forest fraction $0.00$ to $0.98$, Cropland fraction $0.00$ to $0.92$, Builtup fraction $0.00$ to $0.85$.

---

## 5. Limitations & Potential Sampling Bias

> [!WARNING]
> **Limitations & Bias Constraints:**
> - **Not Statistically Representative of All India:** The 100-event pilot is an intentional, stratified sample designed for model validation and guideline calibration. It MUST NOT be claimed as a statistically representative sample of all 996,891 thermal detections across India.
> - **Enriched Ambiguity:** The double-annotation subset intentionally oversamples LOW confidence and edge-case candidates to stress-test inter-annotator agreement guidelines.
> - **Weak-Label Precedence:** AI-assisted weak labels are subject to V2 rule heuristics and are provided solely for hypothesis testing.
