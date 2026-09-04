import sys
import os
import json
import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

# Add ml to path for imports
sys.path.append("ml")

from src.classification.features import APPROVED_FEATURES, EXCLUDED_FEATURES, validate_features
from src.classification.models import HybridClassifier, TAXONOMY_CLASSES
from src.classification.baseline import RuleBasedClassifier
from src.classification.prediction import PredictionContract, PredictionStatus, VerificationState, DataQuality

DEMO_SCENARIOS = [
    {
        "name": "Scenario 1: Persistent Industrial Source",
        "expected_label": "persistent_industrial_source",
        "input_features": {
            "event_id": "DEMO-EVT-001",
            "distance_to_facility_km": 0.3,
            "active_days_previous_30d": 22.0,
            "events_previous_30d": 15.0,
            "near_factory": True,
            "builtup_fraction_1km": 0.65,
            "max_frp_mw": 85.0,
            "duration_hours": 120.0
        }
    },
    {
        "name": "Scenario 2: Industrial Fire / Abnormal Event",
        "expected_label": "industrial_fire_or_abnormal_event",
        "input_features": {
            "event_id": "DEMO-EVT-002",
            "distance_to_facility_km": 0.2,
            "near_refinery": True,
            "max_frp_mw": 250.0,
            "builtup_fraction_1km": 0.55,
            "active_days_previous_30d": 2.0,
            "duration_hours": 8.0
        }
    },
    {
        "name": "Scenario 3: Wildfire / Forest Fire",
        "expected_label": "wildfire_or_forest_fire",
        "input_features": {
            "event_id": "DEMO-EVT-003",
            "forest_fraction_1km": 0.85,
            "distance_to_facility_km": 15.2,
            "spatial_extent_km": 8.5,
            "max_frp_mw": 180.0,
            "natural_land_fraction": 0.92,
            "active_days_previous_30d": 1.0
        }
    },
    {
        "name": "Scenario 4: Agricultural Burning",
        "expected_label": "agricultural_burning",
        "input_features": {
            "event_id": "DEMO-EVT-004",
            "cropland_fraction_1km": 0.78,
            "distance_to_facility_km": 8.4,
            "active_days_previous_30d": 2.0,
            "duration_hours": 3.0,
            "max_frp_mw": 45.0,
            "forest_fraction_1km": 0.05
        }
    },
    {
        "name": "Scenario 5: Mining / Industrial Activity",
        "expected_label": "mining_or_other_industrial_activity",
        "input_features": {
            "event_id": "DEMO-EVT-005",
            "near_mine": True,
            "near_quarry": True,
            "distance_to_facility_km": 1.1,
            "builtup_fraction_1km": 0.25,
            "max_frp_mw": 95.0,
            "active_days_previous_30d": 6.0
        }
    },
    {
        "name": "Scenario 6: Ambiguous / Insufficient Evidence (Unknown)",
        "expected_label": "unknown_requires_verification",
        "input_features": {
            "event_id": "DEMO-EVT-006",
            "max_frp_mw": 12.0,
            "distance_to_facility_km": 12.0,
            "forest_fraction_1km": 0.1,
            "cropland_fraction_1km": 0.1,
            "builtup_fraction_1km": 0.05,
            "active_days_previous_30d": 0.0
        }
    }
]

def run_person2_demo():
    print("=" * 80)
    print("      PERSON 2 — AI/ML CLASSIFIER DEMONSTRATION RUNNER")
    print("=" * 80)
    
    rule_clf = RuleBasedClassifier(skip_verification=True)
    hybrid_clf = HybridClassifier(rule_classifier=rule_clf, skip_verification=True)
    
    passed_assertions = 0
    total_assertions = 0
    unexpected_predictions = 0

    for idx, scenario in enumerate(DEMO_SCENARIOS):
        print(f"\n--- {scenario['name']} ---")
        input_feats = scenario["input_features"]
        
        # 1. Target Leakage Verification: Ensure no label/ground truth field is passed
        for k in input_feats.keys():
            assert k not in EXCLUDED_FEATURES or k == "event_id", f"LEAKAGE DETECTED: {k} is an excluded feature!"
            assert "label" not in k and "risk" not in k, f"LEAKAGE DETECTED: {k} looks like a target label!"
        passed_assertions += 1
        total_assertions += 1
        
        # 2. Run actual Hybrid Classifier
        contract = hybrid_clf.predict_event(input_feats)
        
        # 3. Contract Assertions
        assert isinstance(contract, PredictionContract), "Output does not conform to PredictionContract!"
        assert contract.predicted_label in TAXONOMY_CLASSES, f"Predicted label {contract.predicted_label} not in 6-class taxonomy!"
        assert contract.model_version != "", "Model version is missing!"
        
        prob_sum = sum(contract.class_probabilities.values())
        assert abs(prob_sum - 1.0) < 1e-4, f"Class probabilities do not sum to 1.0 (Sum: {prob_sum})!"
        passed_assertions += 4
        total_assertions += 4

        # 4. Display Outputs
        print(f"Predicted Label    : {contract.predicted_label}")
        print(f"Expected Label     : {scenario['expected_label']}")
        print(f"Model Confidence   : {contract.model_confidence}")
        print(f"Evidence Confidence: {contract.evidence_confidence}")
        print(f"Model Version      : {contract.model_version}")
        print("\nClass Probabilities:")
        for cls, prob in contract.class_probabilities.items():
            print(f"  - {cls:38s}: {prob:.4f}")

        print("\nTop Explanations / Evidence:")
        for exp in contract.explanations:
            print(f"  - [{exp.source}] {exp.description} (Importance: {exp.importance})")

        # 5. Check Expectation Match
        is_expected = contract.predicted_label == scenario['expected_label']
        if is_expected:
            print("\nSTATUS: [EXPECTED FOR DEMO SCENARIO]")
        else:
            print("\nSTATUS: [UNEXPECTED PREDICTION]")
            unexpected_predictions += 1

    print("\n" + "=" * 80)
    print("                     DEMO RUNNER SUMMARY")
    print("=" * 80)
    print(f"Total Scenarios Evaluated  : {len(DEMO_SCENARIOS)}")
    print(f"Contract Assertions Passed : {passed_assertions} / {total_assertions}")
    print(f"Unexpected Predictions     : {unexpected_predictions}")
    print("=" * 80)

if __name__ == "__main__":
    run_person2_demo()
