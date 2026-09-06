# Independent Dual-Human Annotation Protocol: Pilot V2 Reliability Sample

## 1. Overview & Objective

This document defines the binding operational protocol for the independent dual-human annotation of the frozen 30-record Pilot V2 reliability sample (`blind_annotator_1.json` and `blind_annotator_2.json`).

The objective is to measure empirical human inter-annotator agreement (raw agreement and Cohen's $\kappa$) and establish high-integrity human ground truth for Thermotrace thermal-intelligence event classification.

---

## 2. Core Blinding & Independence Directives

1. **Independent Work**: Annotator A and Annotator B must complete their respective packets (`blind_annotator_1.json` and `blind_annotator_2.json`) entirely independently.
2. **Zero Communication**: Annotators must **NOT** discuss specific thermal events, features, coordinates, or tentative class choices before both annotation packets are submitted.
3. **Zero AI Assistance**: Annotators must **NOT** consult model predictions, AI-assisted pre-labels, synthetic risk scores, or heuristic rules. All pre-labels have been stripped from the blind packets.
4. **Zero Cross-Inference**: Annotators must **NOT** attempt to guess or infer how the other annotator evaluated any event.
5. **Preservation of Record Identity**: Annotators must **NOT** alter, reorder, or delete `event_id`, `latitude`, `longitude`, `timestamp`, or `source_features` fields.

---

## 3. Canonical Six-Class Taxonomy Definitions

Annotators must classify each of the 30 thermal events into exactly **one** of the following six canonical taxonomy classes:

1. **`agricultural_burning`**:
   - Crop residue burning, stubble clearing, or controlled agricultural fires.
   - Typically characterized by high cropland fraction (`cropland_fraction_1km > 0.5`), low forest fraction, short duration (`duration_hours <= 6.0`), and non-persistent previous active days (`active_days_previous_30d < 3.0`).

2. **`mining_or_other_industrial_activity`**:
   - Surface mining, open-cast excavation, quarrying, flaring, or heavy industrial operations.
   - Typically characterized by proximity to mines/quarries (`near_mine = True`, `near_quarry = True`, or `distance_to_facility_km < 5.0`), low forest fraction, and moderate/high previous active days.

3. **`persistent_industrial_source`**:
   - Continuous thermal emission sources such as power plants, steel mills, cement kilns, or refineries.
   - Characterized by high temporal persistence (`active_days_previous_30d >= 10.0`, high `events_previous_30d`), close proximity to industrial facilities (`distance_to_facility_km < 2.0`), and low forest cover.

4. **`unknown_requires_verification`**:
   - Ambiguous or low-signal thermal detections where observational features are insufficient to assign a specific physical cause.
   - Used when features do not cleanly match any specific industrial, agricultural, or wildfire pattern.

5. **`wildfire_or_forest_fire`**:
   - Vegetation fires in forest, timber, or dense woodland areas.
   - Characterized by high forest cover (`forest_fraction_1km > 0.4`), high fire radiative power (`max_frp_mw`), longer duration, and distance from industrial infrastructure.

6. **`industrial_fire_or_abnormal_event`**:
   - Accidental industrial fires, warehouse blazes, refinery explosions, or emergency shutdown flaring.
   - Characterized by high thermal intensity (`max_frp_mw`) at an industrial location without long-term temporal persistence prior to the event.

---

## 4. Completed Annotation Schema & Submission Instructions

For each of the 30 records, the annotator must populate the following fields in their output JSON array:

- **`event_id`**: String matching the input record `event_id` exactly (e.g. `"TT-EVT-00046063"`).
- **`assigned_label`**: Exactly one of the six canonical taxonomy strings listed above.
- **`confidence`**: Integer rating `1` (lowest confidence / ambiguous) to `5` (highest confidence / certain), or rating string (`"low"`, `"medium"`, `"high"`).
- **`notes`**: Optional free-text notes detailing key visual or feature rationale for the decision.
- **`annotator_id`**: String identifier for the annotator (e.g. `"annotator_1"` or `"annotator_2"`).

### Example Valid Annotated Record:
```json
{
  "event_id": "TT-EVT-00046063",
  "assigned_label": "agricultural_burning",
  "confidence": 4,
  "notes": "High cropland fraction (0.90) and low active days (12d/30d), no nearby quarry.",
  "annotator_id": "annotator_1"
}
```

---

## 5. Next Steps Post-Submission

1. **Automated Validation**: Upon submission, `validate_human_reliability_annotations.py` will verify that all 30 records are present, correctly formatted, and non-duplicate.
2. **Empirical Agreement Calculation**: `reliability_analysis.py` will compute raw percent agreement and Cohen's $\kappa$.
3. **Disagreement Export**: `export_disagreements` will extract any record where Annotator A $\neq$ Annotator B.
4. **Adjudication**: An independent lead annotator will adjudicate any disagreement records to form the final ground-truth dataset (`adjudicate_reliability_annotations.py`).
