"""
Tests for alerts.py – alert generation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.alerts import generate_alert
from thermotrace_temporal.schemas import (
    AlertPriority,
    AlertStatus,
    AlertType,
    AnomalyLevel,
    AnomalyResult,
    IndustrialLikelihood,
    OperationalRisk,
    RiskLevel,
)


def make_anomaly(score=50.0, level=AnomalyLevel.ABNORMAL, reasons=None):
    return AnomalyResult(
        anomaly_score=score,
        anomaly_level=level,
        reasons=reasons or ["Test reason"],
        component_scores={},
        data_quality_notes=[],
    )


def make_il(score=70.0, requires_v=False):
    return IndustrialLikelihood(
        score=score,
        requires_verification=requires_v,
        component_scores={},
        evidence_for=[],
        evidence_against=[],
        missing_evidence=[],
    )


def make_risk(score=60.0, level=RiskLevel.HIGH):
    return OperationalRisk(
        risk_score=score,
        risk_level=level,
        score_confidence="full",
        available_components=["thermal_intensity"],
        missing_components=[],
        component_contributions={"thermal_intensity": score},
        notes=[],
    )


class TestGenerateAlert:
    def test_high_risk_abnormal_generates_critical_or_high_alert(self):
        result = generate_alert(
            event_id="TT-EVENT-TEST",
            facility_id="FAC-001",
            anomaly_result=make_anomaly(85.0, AnomalyLevel.SEVERE),
            risk_result=make_risk(85.0, RiskLevel.CRITICAL),
            industrial_likelihood=make_il(90.0),
        )
        assert result.priority in (AlertPriority.CRITICAL, AlertPriority.HIGH)
        assert result.alert_type == AlertType.ABNORMAL_INCREASE

    def test_normal_activity_no_alert(self):
        result = generate_alert(
            event_id="TT-EVENT-NORM",
            facility_id="FAC-001",
            anomaly_result=make_anomaly(10.0, AnomalyLevel.NORMAL),
            risk_result=make_risk(20.0, RiskLevel.LOW),
            industrial_likelihood=make_il(40.0),
        )
        assert result.priority in (AlertPriority.NONE, AlertPriority.LOW)

    def test_requires_verification_generates_verification_alert(self):
        result = generate_alert(
            event_id="TT-EVENT-VER",
            facility_id=None,
            anomaly_result=make_anomaly(0.0, AnomalyLevel.UNKNOWN),
            risk_result=make_risk(10.0, RiskLevel.LOW),
            industrial_likelihood=make_il(30.0, requires_v=True),
        )
        assert result.alert_type == AlertType.UNKNOWN_REQUIRES_VERIFICATION
        assert "verification" in result.recommended_action.lower()

    def test_alert_has_required_fields(self):
        result = generate_alert(
            event_id="TT-EVENT-FIELDS",
            facility_id="FAC-002",
            anomaly_result=make_anomaly(70.0, AnomalyLevel.ABNORMAL),
            risk_result=make_risk(65.0, RiskLevel.HIGH),
            industrial_likelihood=make_il(75.0),
        )
        assert result.alert_id.startswith("TT-ALERT-")
        assert result.status == AlertStatus.NEW
        assert result.created_at is not None
        assert result.recommended_action != ""
        assert result.reason != ""

    def test_new_event_flag_generates_new_event_alert(self):
        result = generate_alert(
            event_id="TT-EVENT-NEW",
            facility_id="FAC-003",
            anomaly_result=make_anomaly(25.0, AnomalyLevel.NORMAL),
            risk_result=make_risk(30.0, RiskLevel.LOW),
            industrial_likelihood=make_il(65.0),
            is_new_event=True,
        )
        assert result.alert_type in (AlertType.NEW_INDUSTRIAL_EVENT, AlertType.PERSISTENT_SOURCE, AlertType.UNKNOWN_REQUIRES_VERIFICATION)

    def test_alert_scores_match_inputs(self):
        result = generate_alert(
            event_id="TT-EVENT-SCORES",
            facility_id="FAC-001",
            anomaly_result=make_anomaly(72.3, AnomalyLevel.ABNORMAL),
            risk_result=make_risk(58.1, RiskLevel.MEDIUM),
            industrial_likelihood=make_il(81.5),
        )
        assert result.anomaly_score == pytest.approx(72.3, rel=0.01)
        assert result.risk_score == pytest.approx(58.1, rel=0.01)
        assert result.industrial_likelihood == pytest.approx(81.5, rel=0.01)
