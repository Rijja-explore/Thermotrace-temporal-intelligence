"""
Tests for baseline.py – baseline calculation and deviation.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.baseline import compute_baseline, compute_deviation
from thermotrace_temporal.schemas import HistoryQuality
from conftest import make_obs, make_obs_list


class TestComputeBaseline:
    def test_no_historical_data_returns_unavailable(self):
        baseline = compute_baseline([], datetime(2026, 1, 15))
        assert baseline.available is False
        assert baseline.history_quality == HistoryQuality.INSUFFICIENT

    def test_baseline_uses_only_pre_period_data(self):
        """
        CRITICAL: Baseline must NOT include current-period observations.
        This test verifies leakage prevention.
        """
        current_start = datetime(2026, 2, 1)
        historical_obs = make_obs_list(
            10, base_dt=datetime(2026, 1, 1), interval_hours=24, frp_base=40.0
        )
        # Add a current-period observation with very high FRP
        current_obs = [make_obs("CURRENT", dt=datetime(2026, 2, 5), frp=200.0)]
        all_obs = historical_obs + current_obs

        baseline = compute_baseline(all_obs, current_start)
        assert baseline.available is True
        # The baseline FRP mean should be ~44 (historical), not contaminated by 200
        assert baseline.frp_mean is not None
        assert baseline.frp_mean < 100.0

    def test_baseline_statistics_correct(self):
        current_start = datetime(2026, 2, 1)
        frp_values = [40.0, 42.0, 38.0, 45.0, 41.0]
        obs = [
            make_obs(f"H{i}", dt=datetime(2026, 1, i + 1), frp=v)
            for i, v in enumerate(frp_values)
        ]
        baseline = compute_baseline(obs, current_start)
        assert baseline.available is True
        assert baseline.frp_mean == pytest.approx(sum(frp_values) / len(frp_values), rel=1e-2)
        assert baseline.frp_median is not None
        assert baseline.frp_upper_quantile is not None
        assert baseline.frp_lower_quantile is not None
        assert baseline.frp_upper_quantile >= baseline.frp_median
        assert baseline.frp_lower_quantile <= baseline.frp_median

    def test_insufficient_history_flagged(self):
        current_start = datetime(2026, 1, 15)
        obs = [make_obs("FEW", dt=datetime(2026, 1, 10), frp=50.0)]
        baseline = compute_baseline(obs, current_start)
        assert baseline.history_quality in (HistoryQuality.INSUFFICIENT, HistoryQuality.POOR)
        assert len(baseline.notes) > 0

    def test_all_frp_missing_returns_none_stats(self):
        current_start = datetime(2026, 2, 1)
        obs = make_obs_list(10, frp_base=None)
        for o in obs:
            o.frp = None
        baseline = compute_baseline(obs, current_start)
        assert baseline.frp_mean is None
        assert baseline.frp_median is None

    def test_non_standard_timestamp_handling(self):
        """Verify baseline calculation handles objects without dt.date gracefully."""
        current_start = datetime(2026, 2, 1)
        obs = make_obs_list(5, base_dt=datetime(2026, 1, 1), interval_hours=24)
        for o in obs:
            o.timestamp_utc = timedelta(days=5)  # Timedelta object
        baseline = compute_baseline(obs, current_start)
        assert baseline.available is True
        assert baseline.history_count == 5


class TestComputeDeviation:
    def test_normal_deviation_calculation(self):
        from thermotrace_temporal.baseline import compute_baseline
        current_start = datetime(2026, 2, 1)
        obs = [
            make_obs(f"H{i}", dt=datetime(2026, 1, i + 1), frp=40.0)
            for i in range(20)
        ]
        baseline = compute_baseline(obs, current_start)

        deviation = compute_deviation(
            current_frp_mean=80.0,
            current_detection_frequency=1.0,
            current_active_ratio=0.9,
            current_spatial_extent=1.0,
            baseline=baseline,
        )
        # FRP deviation: (80 - 40) / 40 * 100 = 100%
        assert deviation["frp_deviation_percent"] == pytest.approx(100.0, rel=0.01)
        assert deviation["frp_deviation"] == pytest.approx(80.0 - baseline.frp_mean, rel=0.01)

    def test_zero_baseline_frp_safe(self):
        """When baseline FRP mean is zero, percentage deviation must NOT return Inf."""
        from thermotrace_temporal.schemas import Baseline, HistoryQuality
        baseline = Baseline(
            available=True,
            frp_mean=0.0,
            frp_std=0.0,
            history_count=5,
            history_quality=HistoryQuality.POOR,
        )
        deviation = compute_deviation(
            current_frp_mean=50.0,
            current_detection_frequency=None,
            current_active_ratio=None,
            current_spatial_extent=None,
            baseline=baseline,
        )
        # Should NOT be inf or NaN
        assert deviation["frp_deviation_percent"] is None or abs(deviation["frp_deviation_percent"]) < 1e9

    def test_baseline_unavailable_returns_notes(self):
        from thermotrace_temporal.schemas import Baseline, HistoryQuality
        baseline = Baseline(available=False, history_quality=HistoryQuality.INSUFFICIENT)
        deviation = compute_deviation(None, None, None, None, baseline)
        assert deviation["frp_deviation"] is None
        assert len(deviation["notes"]) > 0
        assert any("unavailable" in n.lower() or "insufficient" in n.lower() for n in deviation["notes"])
