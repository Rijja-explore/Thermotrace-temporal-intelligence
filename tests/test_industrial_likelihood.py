"""
Tests for industrial_likelihood.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thermotrace_temporal.industrial_likelihood import score_industrial_likelihood


class TestIndustrialLikelihood:
    def test_strong_industrial_evidence_high_score(self):
        result = score_industrial_likelihood(
            facility_distance_km=0.3,
            facility_type="refinery",
            persistence_ratio=0.85,
            landcover_class="industrial",
            spatial_stability_score=95.0,
            detection_frequency=1.5,
            sensor_count=2,
            observation_count=30,
        )
        assert result.score >= 70
        assert len(result.evidence_for) > 0

    def test_natural_landcover_lowers_score(self):
        result_natural = score_industrial_likelihood(
            facility_distance_km=0.5,
            facility_type="refinery",
            persistence_ratio=0.8,
            landcover_class="forest",
            spatial_stability_score=50.0,
            detection_frequency=0.5,
            sensor_count=1,
            observation_count=10,
        )
        result_industrial = score_industrial_likelihood(
            facility_distance_km=0.5,
            facility_type="refinery",
            persistence_ratio=0.8,
            landcover_class="industrial",
            spatial_stability_score=50.0,
            detection_frequency=0.5,
            sensor_count=1,
            observation_count=10,
        )
        assert result_natural.score < result_industrial.score
        assert len(result_natural.evidence_against) > 0

    def test_missing_facility_lowers_score(self):
        result = score_industrial_likelihood(
            facility_distance_km=None,
            facility_type=None,
            persistence_ratio=0.5,
            landcover_class="industrial",
            spatial_stability_score=60.0,
            detection_frequency=0.5,
            sensor_count=1,
            observation_count=10,
        )
        # Missing facility = missing evidence
        assert any("facility proximity" in m.lower() for m in result.missing_evidence)

    def test_missing_landcover_neutral(self):
        result = score_industrial_likelihood(
            facility_distance_km=0.5,
            facility_type="refinery",
            persistence_ratio=0.7,
            landcover_class=None,
            spatial_stability_score=70.0,
            detection_frequency=0.8,
            sensor_count=2,
            observation_count=20,
        )
        assert any("land" in m.lower() for m in result.missing_evidence)

    def test_requires_verification_when_evidence_weak(self):
        result = score_industrial_likelihood(
            facility_distance_km=15.0,  # very far
            facility_type=None,
            persistence_ratio=0.05,   # very sparse
            landcover_class="forest",
            spatial_stability_score=10.0,
            detection_frequency=0.1,
            sensor_count=1,
            observation_count=2,
        )
        assert result.requires_verification is True

    def test_score_in_valid_range(self):
        result = score_industrial_likelihood(
            facility_distance_km=0.5,
            facility_type="refinery",
            persistence_ratio=0.7,
            landcover_class="industrial",
            spatial_stability_score=80.0,
            detection_frequency=1.0,
            sensor_count=3,
            observation_count=50,
        )
        assert 0.0 <= result.score <= 100.0

    def test_component_scores_returned(self):
        result = score_industrial_likelihood(
            facility_distance_km=0.5,
            facility_type="refinery",
            persistence_ratio=0.7,
            landcover_class="industrial",
            spatial_stability_score=80.0,
            detection_frequency=1.0,
            sensor_count=2,
            observation_count=30,
        )
        assert "facility_proximity" in result.component_scores
        assert "persistence" in result.component_scores
        assert "landcover" in result.component_scores
        assert "spatial_stability" in result.component_scores

    def test_single_observation_penalised(self):
        result = score_industrial_likelihood(
            facility_distance_km=0.5,
            facility_type="refinery",
            persistence_ratio=0.1,
            landcover_class="industrial",
            spatial_stability_score=90.0,
            detection_frequency=0.03,
            sensor_count=1,
            observation_count=1,
        )
        # Single observation: evidence against temporal pattern
        assert any("single" in e.lower() for e in result.evidence_against)
