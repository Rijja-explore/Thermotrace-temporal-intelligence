"""
Tests for clustering.py – thermal event clustering.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.clustering import cluster_observations, validate_observations
from thermotrace_temporal.schemas import Observation
from conftest import make_obs, make_obs_list


class TestValidateObservations:
    def test_valid_observations_pass(self):
        raw = [
            {
                "observation_id": "OBS-001",
                "latitude": 19.123,
                "longitude": 73.456,
                "timestamp_utc": "2026-01-15T08:00:00Z",
                "frp": 45.0,
                "confidence": 90.0,
                "facility_id": "FAC-001",
                "facility_type": "refinery",
                "facility_distance_km": 0.5,
                "landcover_class": "industrial",
            }
        ]
        valid, rejected = validate_observations(raw)
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_invalid_timestamp_rejected(self):
        raw = [
            {
                "observation_id": "OBS-BAD",
                "latitude": 19.0,
                "longitude": 73.0,
                "timestamp_utc": "NOT_A_DATE",
            }
        ]
        valid, rejected = validate_observations(raw)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_duplicate_ids_rejected(self):
        raw = [
            {"observation_id": "DUP", "latitude": 10.0, "longitude": 10.0, "timestamp_utc": "2026-01-15T08:00:00Z"},
            {"observation_id": "DUP", "latitude": 11.0, "longitude": 11.0, "timestamp_utc": "2026-01-15T09:00:00Z"},
        ]
        valid, rejected = validate_observations(raw)
        assert len(valid) == 1
        assert len(rejected) == 1
        assert "duplicate" in rejected[0]["reason"]

    def test_missing_optional_fields_allowed(self):
        raw = [
            {
                "observation_id": "MIN-001",
                "latitude": 10.0,
                "longitude": 10.0,
                "timestamp_utc": "2026-01-15T08:00:00Z",
                # frp, confidence, facility_id, etc. all missing
            }
        ]
        valid, rejected = validate_observations(raw)
        assert len(valid) == 1
        assert valid[0].frp is None
        assert valid[0].facility_id is None

    def test_empty_input(self):
        valid, rejected = validate_observations([])
        assert valid == []
        assert rejected == []


class TestClusterObservations:
    def test_single_observation_creates_one_event(self):
        obs = [make_obs("SINGLE-001")]
        events = cluster_observations(obs)
        assert len(events) == 1
        assert events[0].observation_count == 1

    def test_empty_input_returns_empty(self):
        events = cluster_observations([])
        assert events == []

    def test_close_observations_cluster_together(self):
        """Observations close in space and time should form one cluster."""
        obs = [
            make_obs("A", lat=19.123, lon=73.456, dt=datetime(2026, 1, 15, 8, 0)),
            make_obs("B", lat=19.124, lon=73.457, dt=datetime(2026, 1, 15, 10, 0)),
            make_obs("C", lat=19.122, lon=73.455, dt=datetime(2026, 1, 15, 14, 0)),
        ]
        events = cluster_observations(obs)
        # All three should be in one cluster
        assert len(events) == 1
        assert events[0].observation_count == 3

    def test_temporally_separated_observations_form_separate_events(self):
        """Same location but months apart must NOT cluster together."""
        obs = [
            make_obs("JAN", lat=19.123, lon=73.456, dt=datetime(2026, 1, 15, 8, 0)),
            make_obs("APR", lat=19.123, lon=73.456, dt=datetime(2026, 4, 15, 8, 0)),
        ]
        events = cluster_observations(obs)
        assert len(events) == 2

    def test_spatially_separated_observations_form_separate_events(self):
        """Observations far apart in space should form separate events."""
        obs = [
            make_obs("INDIA", lat=19.123, lon=73.456, dt=datetime(2026, 1, 15, 8, 0)),
            make_obs("KENYA", lat=-1.286, lon=36.817, dt=datetime(2026, 1, 15, 9, 0)),
        ]
        events = cluster_observations(obs)
        assert len(events) == 2

    def test_event_has_required_fields(self):
        obs = make_obs_list(3)
        events = cluster_observations(obs)
        assert len(events) >= 1
        e = events[0]
        assert e.event_id.startswith("TT-EVENT-")
        assert e.centroid_latitude is not None
        assert e.centroid_longitude is not None
        assert e.start_time <= e.end_time
        assert e.observation_count == len(e.observation_ids)
        assert e.duration_hours >= 0
        assert e.spatial_extent_km >= 0

    def test_duplicate_observations_handled(self):
        obs = [make_obs("DUP-CLUST")] * 3
        # Validate first to deduplicate
        raw_dicts = [o.model_dump() for o in obs]
        for d in raw_dicts:
            d["timestamp_utc"] = d["timestamp_utc"].isoformat()
        valid, _ = validate_observations(raw_dicts)
        events = cluster_observations(valid)
        assert len(events) == 1  # Only one unique observation

    def test_missing_frp_observations_cluster(self):
        """Observations with missing FRP should still cluster."""
        obs = [
            make_obs("NOFRP-1", frp=None, dt=datetime(2026, 1, 15, 8, 0)),
            make_obs("NOFRP-2", frp=None, dt=datetime(2026, 1, 15, 10, 0)),
        ]
        events = cluster_observations(obs)
        assert len(events) >= 1
        # FRP stats should be None
        assert events[0].frp_mean is None
