"""
industrial_likelihood.py – Evidence-based industrial likelihood scoring.

This module computes a transparent, evidence-weighted industrial likelihood
score from multiple observable signals.

IMPORTANT: This score is NOT a machine-learning classification (that is
Person 2's role). It is an evidence accumulation system that:
  - Weighs observable signals according to configurable weights
  - Returns component scores so each contribution is traceable
  - Returns explicit evidence_for and evidence_against lists
  - Returns requires_verification = True when evidence is weak
  - Never claims certainty beyond what the data supports

Component weights (in config/weights.yaml):
  facility_proximity  30% – proximity to known industrial facility
  persistence         25% – recurrent/persistent detection pattern
  landcover           15% – industrial land-cover classification
  spatial_stability   15% – stable spatial footprint
  temporal            10% – temporal pattern (e.g. continuous vs episodic)
  sensor_agreement     5% – multi-sensor corroboration

Person 2 can use this score as one input feature to their ML classifier.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from .config_loader import Config, get_config
from .schemas import IndustrialLikelihood

logger = logging.getLogger(__name__)

_INDUSTRIAL_LANDCOVERS = frozenset({
    "industrial", "urban", "built-up", "commercial", "refinery",
    "factory", "power_plant", "mining", "port", "warehouse",
})

_NATURAL_LANDCOVERS = frozenset({
    "forest", "shrubland", "grassland", "savanna", "cropland",
    "wetland", "water", "bare", "tundra", "snow",
})


def score_industrial_likelihood(
    facility_distance_km: Optional[float],
    facility_type: Optional[str],
    persistence_ratio: Optional[float],
    landcover_class: Optional[str],
    spatial_stability_score: Optional[float],
    detection_frequency: Optional[float],
    sensor_count: int,
    observation_count: int,
    config: Optional[Config] = None,
) -> IndustrialLikelihood:
    """
    Compute industrial likelihood from multiple evidence signals.

    Parameters
    ----------
    facility_distance_km : float | None
        Distance from nearest known industrial facility (km).
    facility_type : str | None
        Type of associated facility (e.g. "refinery").
    persistence_ratio : float | None
        Fraction of monitored days with active detections.
    landcover_class : str | None
        Land-cover class at detection location.
    spatial_stability_score : float | None
        Spatial stability (0–100).
    detection_frequency : float | None
        Detections per day in the window.
    sensor_count : int
        Number of distinct sensors that detected the event.
    observation_count : int
        Total observations in analysis period.
    config : Config, optional

    Returns
    -------
    IndustrialLikelihood
    """
    cfg = config or get_config()

    # Load weights
    w = cfg.weights.get("industrial_likelihood", {})
    w_prox: float = w.get("facility_proximity_weight", 0.30)
    w_pers: float = w.get("persistence_weight", 0.25)
    w_land: float = w.get("landcover_weight", 0.15)
    w_spat: float = w.get("spatial_stability_weight", 0.15)
    w_temp: float = w.get("temporal_weight", 0.10)
    w_sens: float = w.get("sensor_agreement_weight", 0.05)

    # Load proximity thresholds
    prox_cfg = cfg.get_threshold("industrial_likelihood", "proximity", default={})
    very_close_km: float = prox_cfg.get("very_close_km", 1.0)
    close_km: float = prox_cfg.get("close_km", 3.0)
    moderate_km: float = prox_cfg.get("moderate_km", 10.0)

    # Persistence thresholds
    pers_cfg = cfg.get_threshold("industrial_likelihood", "persistence", default={})
    high_pers: float = pers_cfg.get("high_ratio", 0.6)
    med_pers: float = pers_cfg.get("medium_ratio", 0.3)

    evidence_for: list[str] = []
    evidence_against: list[str] = []
    missing_evidence: list[str] = []
    component_scores: dict[str, float] = {}

    # -----------------------------------------------------------------------
    # Component 1: Facility Proximity (30%)
    # -----------------------------------------------------------------------
    if facility_distance_km is None:
        prox_score = 0.0
        missing_evidence.append("Facility proximity data unavailable.")
    elif facility_distance_km <= very_close_km:
        prox_score = 100.0
        evidence_for.append(
            f"Detection is {facility_distance_km:.2f} km from a known industrial facility "
            f"(type: {facility_type or 'unknown'}) – within close range."
        )
    elif facility_distance_km <= close_km:
        prox_score = 75.0 - 25.0 * (facility_distance_km - very_close_km) / (close_km - very_close_km)
        evidence_for.append(
            f"Detection is {facility_distance_km:.2f} km from a known industrial facility "
            f"(type: {facility_type or 'unknown'})."
        )
    elif facility_distance_km <= moderate_km:
        prox_score = 50.0 - 40.0 * (facility_distance_km - close_km) / (moderate_km - close_km)
        evidence_for.append(
            f"Detection is {facility_distance_km:.2f} km from a known industrial facility – moderate proximity."
        )
    else:
        prox_score = 0.0
        evidence_against.append(
            f"Detection is {facility_distance_km:.2f} km from nearest known industrial facility – distant."
        )

    prox_score = float(np.clip(prox_score, 0.0, 100.0))
    component_scores["facility_proximity"] = round(prox_score, 2)

    # -----------------------------------------------------------------------
    # Component 2: Persistence / Recurrence (25%)
    # -----------------------------------------------------------------------
    if persistence_ratio is None:
        pers_score = 0.0
        missing_evidence.append("Persistence ratio unavailable – insufficient observation window.")
    elif persistence_ratio >= high_pers:
        pers_score = 100.0
        evidence_for.append(
            f"High persistence ratio ({persistence_ratio:.2f}) – detections on {persistence_ratio*100:.0f}% "
            "of monitored days, consistent with a continuous industrial source."
        )
    elif persistence_ratio >= med_pers:
        pers_score = 60.0 + 40.0 * (persistence_ratio - med_pers) / (high_pers - med_pers)
        evidence_for.append(
            f"Moderate persistence ratio ({persistence_ratio:.2f}) – recurrent but intermittent detections."
        )
    elif persistence_ratio > 0:
        pers_score = 30.0 * (persistence_ratio / med_pers)
        evidence_against.append(
            f"Low persistence ratio ({persistence_ratio:.2f}) – sporadic detections inconsistent with a "
            "continuous industrial source."
        )
    else:
        pers_score = 0.0
        evidence_against.append("No persistent detections observed in the analysis window.")

    pers_score = float(np.clip(pers_score, 0.0, 100.0))
    component_scores["persistence"] = round(pers_score, 2)

    # -----------------------------------------------------------------------
    # Component 3: Land Cover (15%)
    # -----------------------------------------------------------------------
    if landcover_class is None:
        land_score = 50.0  # neutral when unknown
        missing_evidence.append("Land-cover classification unavailable.")
    else:
        lc_lower = landcover_class.lower().strip()
        if lc_lower in _INDUSTRIAL_LANDCOVERS:
            land_score = 100.0
            evidence_for.append(f"Industrial land-cover context: '{landcover_class}'.")
        elif lc_lower in _NATURAL_LANDCOVERS:
            land_score = 5.0
            evidence_against.append(
                f"Natural land-cover context ('{landcover_class}') argues against industrial source."
            )
        else:
            land_score = 40.0  # neutral/mixed
            missing_evidence.append(
                f"Land-cover class '{landcover_class}' is not definitively industrial or natural."
            )

    component_scores["landcover"] = round(float(np.clip(land_score, 0.0, 100.0)), 2)

    # -----------------------------------------------------------------------
    # Component 4: Spatial Stability (15%)
    # -----------------------------------------------------------------------
    if spatial_stability_score is None:
        spat_score = 0.0
        missing_evidence.append("Spatial stability score unavailable.")
    else:
        spat_score = float(spatial_stability_score)
        if spat_score >= 75:
            evidence_for.append(
                f"High spatial stability score ({spat_score:.0f}/100) – detections cluster at a fixed point, "
                "consistent with a stationary industrial source."
            )
        elif spat_score < 30:
            evidence_against.append(
                f"Low spatial stability ({spat_score:.0f}/100) – spreading pattern inconsistent with a "
                "fixed industrial stack."
            )

    component_scores["spatial_stability"] = round(float(np.clip(spat_score, 0.0, 100.0)), 2)

    # -----------------------------------------------------------------------
    # Component 5: Temporal Behaviour (10%)
    # -----------------------------------------------------------------------
    if detection_frequency is None or observation_count == 0:
        temp_score = 0.0
        missing_evidence.append("Temporal behaviour data insufficient.")
    else:
        # Industrial sources tend to show regular, continuous detections
        # We reward moderate-to-high detection frequency and penalise single-observation events
        if observation_count == 1:
            temp_score = 20.0
            evidence_against.append("Single observation – cannot assess temporal pattern.")
        elif detection_frequency >= 1.0:
            temp_score = 100.0
            evidence_for.append(
                f"High detection frequency ({detection_frequency:.2f}/day) – consistent with an "
                "active industrial source."
            )
        elif detection_frequency >= 0.3:
            temp_score = 65.0
            evidence_for.append(
                f"Moderate detection frequency ({detection_frequency:.2f}/day)."
            )
        else:
            temp_score = 30.0

    component_scores["temporal"] = round(float(np.clip(temp_score, 0.0, 100.0)), 2)

    # -----------------------------------------------------------------------
    # Component 6: Multi-Sensor Agreement (5%)
    # -----------------------------------------------------------------------
    if sensor_count == 0:
        sens_score = 0.0
        missing_evidence.append("Sensor information unavailable.")
    elif sensor_count == 1:
        sens_score = 50.0  # single sensor – neutral
    elif sensor_count >= 2:
        sens_score = 100.0
        evidence_for.append(
            f"Multi-sensor corroboration: {sensor_count} distinct sensor(s) detected the event."
        )
    else:
        sens_score = 0.0

    component_scores["sensor_agreement"] = round(float(np.clip(sens_score, 0.0, 100.0)), 2)

    # -----------------------------------------------------------------------
    # Weighted composite score
    # -----------------------------------------------------------------------
    total_w = w_prox + w_pers + w_land + w_spat + w_temp + w_sens
    if total_w == 0:
        total_w = 1.0

    composite = (
        prox_score * w_prox
        + pers_score * w_pers
        + component_scores["landcover"] * w_land
        + component_scores["spatial_stability"] * w_spat
        + temp_score * w_temp
        + sens_score * w_sens
    ) / total_w

    score = round(float(np.clip(composite, 0.0, 100.0)), 2)

    # Verification flag
    high_thresh = cfg.get_threshold("industrial_likelihood", "high_threshold", default=70)
    requires_verification = (
        score < high_thresh
        or bool(missing_evidence)
        or len(evidence_against) > len(evidence_for)
    )

    logger.info(
        "Industrial likelihood score=%.1f requires_verification=%s",
        score, requires_verification,
    )

    return IndustrialLikelihood(
        score=score,
        requires_verification=requires_verification,
        component_scores=component_scores,
        evidence_for=evidence_for,
        evidence_against=evidence_against,
        missing_evidence=missing_evidence,
    )
