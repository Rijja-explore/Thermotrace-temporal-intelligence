"""
Tests for temporal_features.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.temporal_features import extract_temporal_features, compute_spatial_stability
from conftest import make_obs, make_obs_list
import numpy as np


class TestExtractTemporalFeatures:
    def test_empty_observations_returns_zeros(self):
        result = extract_temporal_features([], analysis_end=datetime(2026, 1, 15))
        assert result.window_7d.detection_count == 0
        assert result.window_30d.detection_count == 0
        assert result.window_90d.detection_count == 0

    def test_detections_in_window_counted(self):
        end = datetime(2026, 1, 15)
        # 5 observations, each 1 day apart, all within 7-day window
        obs = make_obs_list(5, base_dt=datetime(2026, 1, 10), interval_hours=24)
        result = extract_temporal_features(obs, analysis_end=end)
        assert result.window_7d.detection_count == 5

    def test_detections_outside_window_not_counted(self):
        end = datetime(2026, 1, 15)
        # Observation 30 days before analysis_end should be in 30d/90d but not 7d
        obs_old = [make_obs("OLD", dt=datetime(2026, 1, 1))]
        obs_recent = [make_obs("NEW", dt=datetime(2026, 1, 14))]
        result = extract_temporal_features(obs_old + obs_recent, analysis_end=end)
        # Only the recent one is in the 7-day window
        assert result.window_7d.detection_count == 1
        assert result.window_30d.detection_count == 2

    def test_frp_statistics_correct(self):
        end = datetime(2026, 1, 15)
        obs = [
            make_obs("A", dt=datetime(2026, 1, 14), frp=100.0),
            make_obs("B", dt=datetime(2026, 1, 13), frp=200.0),
        ]
        result = extract_temporal_features(obs, analysis_end=end)
        tw = result.window_7d
        assert tw.frp_mean == pytest.approx(150.0, rel=1e-2)
        assert tw.frp_max == 200.0
        assert tw.frp_min == 100.0

    def test_persistence_ratio_calculation(self):
        end = datetime(2026, 1, 15, 23, 59, 59)
        # 3 active days in 7-day window
        obs = [
            make_obs("D1", dt=datetime(2026, 1, 13, 8)),
            make_obs("D2", dt=datetime(2026, 1, 14, 8)),
            make_obs("D3", dt=datetime(2026, 1, 15, 8)),
        ]
        result = extract_temporal_features(obs, analysis_end=end)
        # persistence_ratio = active_days / monitored_days = 3/7
        assert result.window_7d.active_days == 3
        assert result.window_7d.persistence_ratio == pytest.approx(3 / 7, rel=1e-2)

    def test_missing_frp_handled_safely(self):
        end = datetime(2026, 1, 15)
        obs = [make_obs("NOFRP", dt=datetime(2026, 1, 14), frp=None)]
        result = extract_temporal_features(obs, analysis_end=end)
        assert result.window_7d.frp_mean is None
        assert result.window_7d.frp_max is None

    def test_day_night_distribution(self):
        end = datetime(2026, 1, 15)
        obs_day = make_obs("DAY", dt=datetime(2026, 1, 14, 12, 0))  # noon UTC
        obs_night = make_obs("NIGHT", dt=datetime(2026, 1, 14, 1, 0))   # 1am UTC
        result = extract_temporal_features([obs_day, obs_night], analysis_end=end)
        tw = result.window_7d
        assert tw.day_count == 1
        assert tw.night_count == 1

    def test_all_windows_populated(self):
        end = datetime(2026, 1, 15)
        obs = make_obs_list(5, base_dt=datetime(2025, 11, 1), interval_hours=24 * 10)
        result = extract_temporal_features(obs, analysis_end=end)
        assert result.window_7d is not None
        assert result.window_30d is not None
        assert result.window_90d is not None

    def test_pandas_timestamp_and_tz_strings(self):
        import pandas as pd
        end = datetime(2026, 1, 15)
        obs = [
            make_obs("TS1", dt=pd.Timestamp("2026-01-14T10:00:00Z")),
            make_obs("TS2", dt=datetime(2026, 1, 13, 12, 0)),
        ]
        result = extract_temporal_features(obs, analysis_end=end)
        assert result.window_7d.detection_count == 2


class TestSpatialStability:
    def test_single_point_max_stability(self):
        lats = np.array([19.123])
        lons = np.array([73.456])
        result = compute_spatial_stability(lats, lons)
        assert result.stability_score == 100.0
        assert result.mean_distance_km == 0.0

    def test_very_spread_points_low_stability(self):
        lats = np.array([0.0, 30.0, -30.0])
        lons = np.array([0.0, 60.0, -60.0])
        result = compute_spatial_stability(lats, lons)
        assert result.stability_score < 30.0
        assert result.mean_distance_km > 2.0

    def test_cluster_close_points_high_stability(self):
        # Points within 100m of each other
        lats = np.array([19.1230, 19.1231, 19.1229])
        lons = np.array([73.4560, 73.4561, 73.4559])
        result = compute_spatial_stability(lats, lons)
        assert result.stability_score >= 90.0

    def test_empty_points_returns_zero_score(self):
        result = compute_spatial_stability(np.array([]), np.array([]))
        assert result.stability_score == 0.0


class TestFacilityFingerprint:
    def test_build_facility_fingerprint_with_non_standard_timestamps(self):
        from thermotrace_temporal.facility_fingerprint import build_facility_fingerprint
        obs = make_obs_list(5, base_dt=datetime(2026, 1, 1), interval_hours=24)
        for o in obs:
            o.timestamp_utc = timedelta(days=5)  # Timedelta object without .dt.hour
        fp = build_facility_fingerprint("FAC_TEST", obs)
        assert fp.observation_count == 5
        assert fp.normal_active_hours is not None

    def test_temporal_features_with_non_standard_timestamps(self):
        obs = make_obs_list(5, base_dt=datetime(2026, 1, 1), interval_hours=24)
        for o in obs:
            o.timestamp_utc = timedelta(days=5)
        res = extract_temporal_features(obs, analysis_end=datetime(2026, 1, 15))
        assert res.window_7d is not None
