"""
Tests for pipeline.py – end-to-end pipeline integration.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.pipeline import analyze_event, analyze_facility


def obs_dict(obs_id, lat=19.123, lon=73.456, ts="2026-01-15T08:00:00Z",
             frp=50.0, confidence=90.0, facility_id="FAC-001",
             facility_type="refinery", facility_distance_km=0.5,
             landcover_class="industrial"):
    return {
        "observation_id": obs_id,
        "latitude": lat,
        "longitude": lon,
        "timestamp_utc": ts,
        "frp": frp,
        "confidence": confidence,
        "facility_id": facility_id,
        "facility_type": facility_type,
        "facility_distance_km": facility_distance_km,
        "landcover_class": landcover_class,
        "satellite": "NOAA-20",
        "sensor": "VIIRS",
        "source": "TEST",
    }


def make_historical(n=20, frp_mean=45.0, base_ts="2025-11-"):
    obs = []
    for i in range(n):
        day = 1 + (i % 28)
        month = 11 + (i // 28)
        ts = f"2025-{month:02d}-{day:02d}T08:00:00Z"
        obs.append(obs_dict(f"HIST-{i:03d}", ts=ts, frp=frp_mean + (i % 5)))
    return obs


class TestAnalyzeEvent:
    def test_empty_observations_returns_output(self):
        result = analyze_event([], historical_observations=[],
                               current_period_start=datetime(2026, 1, 15))
        assert "event_id" in result
        assert result["anomaly"]["level"] == "unknown"

    def test_single_observation_completes(self):
        obs = [obs_dict("SINGLE")]
        result = analyze_event(obs, historical_observations=[],
                               current_period_start=datetime(2026, 1, 15))
        assert "event_id" in result
        assert "anomaly" in result
        assert "industrial_likelihood" in result
        assert "operational_risk" in result
        assert "alert" in result

    def test_full_pipeline_with_history(self):
        current_obs = [obs_dict(f"CUR-{i:03d}", ts=f"2026-01-{15+i}T08:00:00Z", frp=150.0)
                       for i in range(5)]
        hist = make_historical(n=30, frp_mean=45.0)
        result = analyze_event(
            current_obs,
            historical_observations=hist,
            current_period_start=datetime(2026, 1, 15),
        )
        assert result["baseline"]["available"] is True
        assert result["baseline"]["frp_mean"] is not None
        assert result["deviation"]["frp_deviation_percent"] is not None

    def test_output_has_metadata(self):
        obs = [obs_dict("META-001")]
        result = analyze_event(obs)
        meta = result.get("metadata", {})
        assert "engine_version" in meta
        assert "config_version" in meta
        assert "analysis_timestamp" in meta

    def test_output_is_json_serialisable(self):
        import json
        obs = [obs_dict("JSON-001")]
        result = analyze_event(obs, historical_observations=make_historical())
        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 100

    def test_missing_facility_handled(self):
        obs = [obs_dict("NOFAC-001", facility_id=None, facility_type=None,
                        facility_distance_km=None)]
        result = analyze_event(obs)
        # Should not crash
        assert "industrial_likelihood" in result
        il = result["industrial_likelihood"]
        assert any("facility" in m.lower() for m in il.get("missing_evidence", []))

    def test_insufficient_history_explicit(self):
        obs = [obs_dict("SPARSE-001")]
        result = analyze_event(obs, historical_observations=[],
                               current_period_start=datetime(2026, 1, 15))
        assert result["baseline"]["available"] is False
        assert result["baseline"]["history_quality"] == "insufficient"

    def test_high_frp_generates_alert(self):
        current_obs = [obs_dict(f"HIGH-{i}", ts=f"2026-01-{13+i}T08:00:00Z", frp=250.0)
                       for i in range(5)]
        hist = make_historical(n=30, frp_mean=45.0)
        result = analyze_event(
            current_obs,
            historical_observations=hist,
            current_period_start=datetime(2026, 1, 13),
        )
        # High FRP vs low baseline should trigger anomaly
        assert result["anomaly"]["score"] > 30

    def test_natural_fire_scenario(self):
        """Natural fire: no facility, forest landcover, moving location."""
        obs = [
            obs_dict(f"NAT-{i}", lat=15.0 + i * 0.03, lon=76.0 + i * 0.03,
                     ts=f"2026-01-13T{8+i:02d}:00:00Z", frp=400.0,
                     facility_id=None, facility_type=None,
                     facility_distance_km=20.0, landcover_class="forest")
            for i in range(4)
        ]
        result = analyze_event(obs, historical_observations=[],
                               current_period_start=datetime(2026, 1, 13))
        il = result["industrial_likelihood"]
        # Natural fire should score lower on industrial likelihood
        # (especially with forest landcover and no facility)
        assert il["score"] < 70


class TestAnalyzeFacility:
    def test_facility_split_correct(self):
        """Historical vs current observations should be split at current_period_start."""
        hist = [obs_dict(f"H{i}", ts=f"2025-12-{1+i:02d}T08:00:00Z", frp=45.0) for i in range(10)]
        current = [obs_dict(f"C{i}", ts=f"2026-01-{15+i}T08:00:00Z", frp=120.0) for i in range(3)]
        all_obs = hist + current
        result = analyze_facility(
            facility_id="FAC-001",
            all_observations=all_obs,
            current_period_start=datetime(2026, 1, 15),
        )
        assert result["baseline"]["available"] is True
        assert result["baseline"]["history_quality"] in ("good", "moderate", "poor")
