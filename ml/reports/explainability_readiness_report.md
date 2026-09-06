# Explainability & Investigation Evidence Readiness Report

## Overview
The Explainability and Investigation Evidence Layer provides strict, typed structures designed to output human-readable contexts and explanations without incorrectly fabricating model confidence, importance scores, or causality on untrained datasets. 

> [!IMPORTANT]
> Current explanations describe observed/contextual evidence only. They are not explanations of a trained semantic classifier because no validated semantic model currently exists.

## 1. Observation Layer
The `ObservationSummarizer` deterministically translates ThermoTrace feature observations into factual descriptions.
- **Factual Restraint**: Outputs are strictly limited to facts (e.g. "Maximum observed FRP was 42.7 MW" or "Event is near OSM-mapped factory").
- **Causal Protection**: The system explicitly avoids words like "caused," "proves," "industrial fire," or "wildfire."
- **Leakage Blocked**: Synthetics (`baseline_risk_score`) and future-leaky properties (`events_local_7d`) are completely rejected by the `validate_features` governance hook.

## 2. Semantic Evidence Layer
Separated mathematically from mere observations via the `ExplanationType.SEMANTIC_EVIDENCE` flag. As documented in `evidence.py`, an external claim only graduates to Semantic Evidence if it is independently verified and possesses strict provenance. For the current deployment environment (which lacks independent verification loops), this array defaults to empty.

## 3. Model Explanation Layer
`ModelExplanationInterface` exists as an architectural placeholder that explicitly refuses to operate when the `ModelLifecycleState` is `NOT_TRAINED`. This prevents accidental exposure of fabricated importance scalars or SHAP values. 

## 4. Confidence Semantics
Confidence has been formally disaggregated in the `PredictionContract` to ensure semantic clarity:
1. `model_confidence`: Future probability scores derived from valid calibrations (currently `None`).
2. `evidence_confidence`: Human/reviewer scores appended to semantic evidence (currently `None`).
3. `data_quality`: Enum classifying the underlying raw satellite inputs.

## 5. Verification States
The pipeline assigns explicit states dictating investigator workflows. Currently, the untrained prediction fallback guarantees:
`VerificationState.MODEL_NOT_AVAILABLE`

## Final Verdict
The codebase structures safely bridge the raw observables into a JSON-compliant investigation evidence panel while firmly resisting hallucinations of capability.

**EXPLAINABILITY_LAYER_READY**
