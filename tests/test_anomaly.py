"""
Tests for anomaly.py – anomaly detection.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.anomaly import detect_anomaly
from thermotrace_temporal.schemas import AnomalyLevel, Baseline, HistoryQuality


def make_baseline(frp_mean=40.0, frp_std=5.0, frp_upper_q=55.0, freq=0.5):
    return Baseline(
        available=True,
        frp_mean=frp_mean,
        frp_median=frp_mean,
        frp_std=frp_std,
        frp_upper_quantile=frp_upper_q,
        frp_lower_quantile=frp_mean - 10,
        detection_frequency=freq,
        active_days_ratio=0.5,
        history_count=30,
        history_quality=HistoryQuality.GOOD,
    )


def make_deviation(frp_pct=0.0, freq_pct=0.0, active_dev=0.0, spatial_dev=0.0):
    return {
        "frp_deviation": frp_pct * 40.0 / 100,
        "frp_deviation_percent": frp_pct,
        "frequency_deviation": freq_pct * 0.5 / 100,
        "frequency_deviation_percent": freq_pct,
        "active_day_deviation": active_dev,
        "spatial_deviation": spatial_dev,
        "notes": [],
    }


class TestDetectAnomaly:
    def test_normal_activity_returns_normal_level(self):
        baseline = make_baseline(frp_mean=40.0, frp_std=5.0)
        deviation = make_deviation(frp_pct=5.0, freq_pct=10.0)
        result = detect_anomaly(
            current_frp_mean=42.0,
            current_frp_max=50.0,
            current_detection_frequency=0.52,
            current_active_ratio=0.5,
            current_spatial_extent=0.5,
            current_duration_hours=10.0,
            baseline=baseline,
            deviation=deviation,
        )
        assert result.anomaly_level == AnomalyLevel.NORMAL
        assert 0 <= result.anomaly_score <= 100

    def test_high_frp_triggers_abnormal(self):
        baseline = make_baseline(frp_mean=40.0, frp_std=5.0, frp_upper_q=55.0)
        # Current FRP = 3+ sigma above baseline
        deviation = make_deviation(frp_pct=150.0, freq_pct=100.0)
        result = detect_anomaly(
            current_frp_mean=100.0,
            current_frp_max=180.0,
            current_detection_frequency=1.0,
            current_active_ratio=0.9,
            current_spatial_extent=0.5,
            current_duration_hours=48.0,
            baseline=baseline,
            deviation=deviation,
        )
        assert result.anomaly_level in (AnomalyLevel.ABNORMAL, AnomalyLevel.SEVERE)
        assert result.anomaly_score > 50

    def test_unavailable_baseline_returns_unknown(self):
        baseline = Baseline(available=False, history_quality=HistoryQuality.INSUFFICIENT)
        deviation = {"frp_deviation_percent": None, "frequency_deviation_percent": None,
                     "active_day_deviation": None, "spatial_deviation": None, "notes": []}
        result = detect_anomaly(
            current_frp_mean=50.0,
            current_frp_max=60.0,
            current_detection_frequency=0.5,
            current_active_ratio=0.5,
            current_spatial_extent=0.5,
            current_duration_hours=10.0,
            baseline=baseline,
            deviation=deviation,
        )
        assert result.anomaly_level == AnomalyLevel.UNKNOWN
        assert len(result.data_quality_notes) > 0

    def test_anomaly_reasons_populated(self):
        baseline = make_baseline(frp_mean=40.0, frp_std=4.0, frp_upper_q=52.0)
        deviation = make_deviation(frp_pct=200.0, freq_pct=120.0, active_dev=0.4)
        result = detect_anomaly(
            current_frp_mean=120.0,
            current_frp_max=200.0,
            current_detection_frequency=1.1,
            current_active_ratio=0.9,
            current_spatial_extent=3.5,
            current_duration_hours=72.0,
            baseline=baseline,
            deviation=deviation,
        )
        assert len(result.reasons) > 0

    def test_score_in_valid_range(self):
        baseline = make_baseline()
        deviation = make_deviation()
        result = detect_anomaly(
            current_frp_mean=40.0,
            current_frp_max=50.0,
            current_detection_frequency=0.5,
            current_active_ratio=0.5,
            current_spatial_extent=0.5,
            current_duration_hours=5.0,
            baseline=baseline,
            deviation=deviation,
        )
        assert 0.0 <= result.anomaly_score <= 100.0

    def test_missing_current_frp_handled(self):
        baseline = make_baseline()
        deviation = make_deviation()
        result = detect_anomaly(
            current_frp_mean=None,
            current_frp_max=None,
            current_detection_frequency=0.5,
            current_active_ratio=0.5,
            current_spatial_extent=0.5,
            current_duration_hours=5.0,
            baseline=baseline,
            deviation=deviation,
        )
        # Should not crash; data quality note should be present
        assert len(result.data_quality_notes) > 0

    def test_component_scores_populated(self):
        baseline = make_baseline()
        deviation = make_deviation(frp_pct=50.0, freq_pct=60.0)
        result = detect_anomaly(
            current_frp_mean=60.0,
            current_frp_max=80.0,
            current_detection_frequency=0.75,
            current_active_ratio=0.6,
            current_spatial_extent=1.0,
            current_duration_hours=20.0,
            baseline=baseline,
            deviation=deviation,
        )
        assert "frp_deviation" in result.component_scores
        assert "frequency_deviation" in result.component_scores
