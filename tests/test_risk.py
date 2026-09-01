"""
Tests for risk.py – operational risk calculation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.risk import compute_risk
from thermotrace_temporal.schemas import AnomalyLevel, AnomalyResult, RiskLevel


def make_anomaly(score=50.0, level=AnomalyLevel.ABNORMAL):
    return AnomalyResult(
        anomaly_score=score,
        anomaly_level=level,
        reasons=["Test reason"],
        component_scores={},
        data_quality_notes=[],
    )


class TestComputeRisk:
    def test_full_inputs_full_confidence(self):
        result = compute_risk(
            frp_mean=80.0,
            frp_max=120.0,
            anomaly_result=make_anomaly(70.0, AnomalyLevel.ABNORMAL),
            industrial_likelihood_score=85.0,
            confidence_mean=90.0,
            population_proximity_score=70.0,
            environmental_sensitivity_score=60.0,
        )
        assert result.score_confidence == "full"
        assert 0 <= result.risk_score <= 100
        assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_missing_population_partial_confidence(self):
        result = compute_risk(
            frp_mean=80.0,
            frp_max=120.0,
            anomaly_result=make_anomaly(70.0),
            industrial_likelihood_score=85.0,
            confidence_mean=90.0,
            population_proximity_score=None,  # missing
            environmental_sensitivity_score=60.0,
        )
        assert result.score_confidence == "partial"
        assert "population_proximity" in result.missing_components
        assert len(result.notes) > 0

    def test_missing_both_optional_minimal_confidence(self):
        result = compute_risk(
            frp_mean=80.0,
            frp_max=None,
            anomaly_result=make_anomaly(30.0, AnomalyLevel.NORMAL),
            industrial_likelihood_score=40.0,
            confidence_mean=None,
            population_proximity_score=None,
            environmental_sensitivity_score=None,
        )
        assert result.score_confidence == "minimal"
        assert "population_proximity" in result.missing_components
        assert "environmental_sensitivity" in result.missing_components

    def test_score_in_valid_range(self):
        result = compute_risk(
            frp_mean=200.0,
            frp_max=350.0,
            anomaly_result=make_anomaly(95.0, AnomalyLevel.SEVERE),
            industrial_likelihood_score=90.0,
            confidence_mean=95.0,
            population_proximity_score=90.0,
            environmental_sensitivity_score=80.0,
        )
        assert 0.0 <= result.risk_score <= 100.0

    def test_low_frp_low_risk(self):
        result = compute_risk(
            frp_mean=10.0,
            frp_max=15.0,
            anomaly_result=make_anomaly(5.0, AnomalyLevel.NORMAL),
            industrial_likelihood_score=20.0,
            confidence_mean=70.0,
            population_proximity_score=10.0,
            environmental_sensitivity_score=10.0,
        )
        assert result.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_component_contributions_populated(self):
        result = compute_risk(
            frp_mean=100.0,
            frp_max=150.0,
            anomaly_result=make_anomaly(80.0),
            industrial_likelihood_score=75.0,
            confidence_mean=85.0,
            population_proximity_score=70.0,
            environmental_sensitivity_score=60.0,
        )
        assert "thermal_intensity" in result.component_contributions
        assert "anomaly_persistence" in result.component_contributions

    def test_no_frp_missing_intensity_component(self):
        result = compute_risk(
            frp_mean=None,
            frp_max=None,
            anomaly_result=make_anomaly(50.0),
            industrial_likelihood_score=60.0,
            confidence_mean=80.0,
            population_proximity_score=50.0,
            environmental_sensitivity_score=40.0,
        )
        assert "thermal_intensity" in result.missing_components
