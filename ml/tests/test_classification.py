import pytest
import pandas as pd
import numpy as np
from src.classification.features import validate_features, validate_dataframe, ABLATION_GROUPS
from src.classification.models import LogisticRegressionWrapper, RandomForestWrapper, HybridClassifier
from src.classification.baseline import ThermalOnlyBaseline, RuleBasedBaseline
from src.classification.prediction import fail_prediction
from src.classification.evidence import EvidenceRecord, EvidenceType
from src.classification.evaluation import calculate_metrics
from src.classification.calibration import Calibrator
from src.classification.splits import unseen_facility_split

def test_feature_validation_accepted():
    valid = validate_features(['max_frp_mw', 'events_previous_7d'])
    assert len(valid) == 2

def test_feature_validation_synthetic_risk_rejected():
    with pytest.raises(ValueError, match="rejected: explicitly excluded or identifier field"):
        validate_features(['baseline_risk_score'])

def test_feature_validation_future_leaky_rejected():
    with pytest.raises(ValueError, match="rejected: explicitly excluded or identifier field"):
        validate_features(['events_local_7d'])

def test_feature_validation_unknown_rejected():
    with pytest.raises(ValueError, match="rejected: unknown/unregistered feature column"):
        validate_features(['random_fake_feature'])

def test_feature_validation_identifier_rejected():
    with pytest.raises(ValueError, match="rejected: explicitly excluded or identifier field"):
        validate_features(['nearest_facility_id'])

def test_evidence_semantics_news_failed():
    rec = EvidenceRecord(
        source_type="news",
        source_url="http://fake.url",
        source_name="News",
        publication_or_acquisition_time="2025",
        event_time="2025",
        independent_of_firms=True,
        independently_verified=False, # Search failed / not verified
        provenance_status="UNVERIFIED",
        notes="news search failed"
    )
    assert rec.evidence_type == EvidenceType.UNVERIFIED_EXTERNAL_CLAIM

def test_evidence_semantics_firms():
    rec = EvidenceRecord(
        source_type="firms",
        source_url="local",
        source_name="FIRMS",
        publication_or_acquisition_time="2025",
        event_time="2025",
        independent_of_firms=False,
        independently_verified=False,
        provenance_status="LOCAL"
    )
    assert rec.evidence_type == EvidenceType.OBSERVATION

def test_evidence_semantics_verified():
    rec = EvidenceRecord(
        source_type="report",
        source_url="http://gov.in",
        source_name="Gov",
        publication_or_acquisition_time="2025",
        event_time="2025",
        independent_of_firms=True,
        independently_verified=True,
        provenance_status="VERIFIED"
    )
    assert rec.evidence_type == EvidenceType.SEMANTIC_EVIDENCE

def test_evaluation_metrics_math():
    y_true = ["wildfire_or_forest_fire", "agricultural_burning", "agricultural_burning", "unknown_requires_verification"]
    y_pred = ["wildfire_or_forest_fire", "agricultural_burning", "wildfire_or_forest_fire", "unknown_requires_verification"]
    labels = ["wildfire_or_forest_fire", "agricultural_burning", "unknown_requires_verification"]
    
    y_probs = np.array([
        [0.9, 0.1, 0.0],
        [0.2, 0.8, 0.0],
        [0.6, 0.4, 0.0],
        [0.1, 0.1, 0.8]
    ])
    
    metrics = calculate_metrics(y_true, y_pred, y_probs=y_probs, labels=labels)
    # Agricultural burning: 1 true pos, 1 false neg => recall 0.5
    assert metrics["recall"]["agricultural_burning"] == 0.5
    # Wildfire: 1 true pos, 1 false pos => precision 0.5
    assert metrics["precision"]["wildfire_or_forest_fire"] == 0.5
    assert "brier_score" in metrics

def test_evaluation_metrics_failures():
    with pytest.raises(ValueError, match="empty"):
        calculate_metrics([], [])
    with pytest.raises(ValueError, match="Mismatched lengths"):
        calculate_metrics(["wildfire_or_forest_fire"], ["wildfire_or_forest_fire", "wildfire_or_forest_fire"])
    with pytest.raises(ValueError, match="Invalid label"):
        calculate_metrics(["fake_label"], ["fake_label"], labels=["wildfire_or_forest_fire"])
    
    y_true = ["wildfire_or_forest_fire"]
    y_pred = ["wildfire_or_forest_fire"]
    labels = ["wildfire_or_forest_fire"]
    y_probs = np.array([[0.5, 0.6]]) # Does not sum to 1
    with pytest.raises(ValueError, match="columns do not match"):
        calculate_metrics(y_true, y_pred, y_probs=y_probs, labels=labels)

def test_calibration_failure():
    cal = Calibrator()
    with pytest.raises(ValueError, match="NO_VERIFIED_GROUND_TRUTH"):
        cal.fit([[0.5]], ["unknown_requires_verification"])

@pytest.mark.SOFTWARE_SMOKE_TEST_ONLY
def test_model_wrappers_smoke():
    model = LogisticRegressionWrapper(skip_verification=True)
    X = [[1.0], [2.0]]
    y = ["wildfire_or_forest_fire", "agricultural_burning"]
    model.fit(X, y)
    preds = model.predict(X)
    assert len(preds) == 2

def test_rule_based_classifier_rules():
    from src.classification.baseline import RuleBasedClassifier
    clf = RuleBasedClassifier(skip_verification=True)

    # 1. Persistent Industrial Source
    evt1 = {"event_id": "EVT1", "distance_to_facility_km": 0.5, "active_days_previous_30d": 15.0}
    c1 = clf.predict_event(evt1)
    assert c1.predicted_label == "persistent_industrial_source"

    # 2. Facility Proximity Alone DOES NOT trigger industrial classification -> unknown_requires_verification
    evt_fac_only = {"event_id": "EVT_FAC", "distance_to_facility_km": 0.5, "active_days_previous_30d": 0.0}
    c_fac = clf.predict_event(evt_fac_only)
    assert c_fac.predicted_label == "unknown_requires_verification"

    # 3. Abnormal Industrial Event
    evt2 = {"event_id": "EVT2", "near_refinery": True, "max_frp_mw": 200.0}
    c2 = clf.predict_event(evt2)
    assert c2.predicted_label == "industrial_fire_or_abnormal_event"

    # 4. Mining Activity
    evt3 = {"event_id": "EVT3", "near_mine": True, "distance_to_facility_km": 1.0}
    c3 = clf.predict_event(evt3)
    assert c3.predicted_label == "mining_or_other_industrial_activity"

    # 5. Wildfire
    evt4 = {"event_id": "EVT4", "forest_fraction_1km": 0.8, "distance_to_facility_km": 10.0}
    c4 = clf.predict_event(evt4)
    assert c4.predicted_label == "wildfire_or_forest_fire"

    # 6. Agricultural Burning
    evt5 = {"event_id": "EVT5", "cropland_fraction_1km": 0.7, "active_days_previous_30d": 1.0, "distance_to_facility_km": 5.0}
    c5 = clf.predict_event(evt5)
    assert c5.predicted_label == "agricultural_burning"

    # 7. Insufficient evidence -> unknown_requires_verification
    evt_weak = {"event_id": "EVT_WEAK", "max_frp_mw": 10.0}
    c_weak = clf.predict_event(evt_weak)
    assert c_weak.predicted_label == "unknown_requires_verification"

def test_hybrid_classifier_combination():
    from src.classification.baseline import RuleBasedClassifier
    rule_clf = RuleBasedClassifier(skip_verification=True)
    hybrid_clf = HybridClassifier(rule_classifier=rule_clf, skip_verification=True)
    
    evt = {"event_id": "EVT_HYB", "forest_fraction_1km": 0.8, "distance_to_facility_km": 10.0}
    contract = hybrid_clf.predict_event(evt)
    assert contract.predicted_label == "wildfire_or_forest_fire"
    assert contract.model_version == "HYBRID_V1"
    # Probabilities sum to 1
    assert pytest.approx(sum(contract.class_probabilities.values()), 1e-5) == 1.0

def test_industrial_precision_and_fp_reduction():
    from src.classification.evaluation import calculate_industrial_precision, calculate_false_positive_reduction
    y_true = ["wildfire_or_forest_fire", "persistent_industrial_source", "agricultural_burning"]
    base_preds = ["wildfire_or_forest_fire", "wildfire_or_forest_fire", "wildfire_or_forest_fire"]
    model_preds = ["wildfire_or_forest_fire", "persistent_industrial_source", "agricultural_burning"]

    ind_prec = calculate_industrial_precision(y_true, model_preds)
    assert ind_prec == 1.0 # 1 TP, 0 FP on industrial classes

    fp_red = calculate_false_positive_reduction(y_true, base_preds, model_preds, target_class="wildfire_or_forest_fire")
    assert fp_red == 1.0 # Baseline had 2 FPs, model had 0 FPs -> 100% reduction

