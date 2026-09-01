"""
risk.py – Operational risk calculation engine.

Computes operational risk separately from industrial likelihood.

Risk components (weights in config/weights.yaml):
  thermal_intensity         25% – FRP level relative to intensity bands
  anomaly_persistence       25% – anomaly score + persistence contribution
  population_proximity      20% – population exposure (OPTIONAL INPUT)
  environmental_sensitivity 15% – environmental sensitivity (OPTIONAL INPUT)
  classification_confidence 15% – confidence of detection and classification

IMPORTANT DESIGN PRINCIPLES:
- If population or environmental sensitivity data is NOT available,
  the engine explicitly degrades and reports missing_components.
- score_confidence reflects how complete the risk picture is:
    "full"    – all components available
    "partial" – some optional components missing
    "minimal" – most components missing
- No NaN or Inf values are returned in the output.
- Risk is NOT proof of an industrial incident.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from .config_loader import Config, get_config
from .schemas import AnomalyResult, OperationalRisk, RiskLevel

logger = logging.getLogger(__name__)


def compute_risk(
    frp_mean: Optional[float],
    frp_max: Optional[float],
    anomaly_result: AnomalyResult,
    industrial_likelihood_score: float,
    confidence_mean: Optional[float],
    population_proximity_score: Optional[float],       # 0–100, None if unavailable
    environmental_sensitivity_score: Optional[float],  # 0–100, None if unavailable
    config: Optional[Config] = None,
) -> OperationalRisk:
    """
    Compute operational risk score.

    Parameters
    ----------
    frp_mean : float | None
        Mean FRP for current period (MW).
    frp_max : float | None
        Peak FRP for current period (MW).
    anomaly_result : AnomalyResult
        Output from anomaly detection engine.
    industrial_likelihood_score : float
        Industrial likelihood score (0–100).
    confidence_mean : float | None
        Mean detection confidence (0–100).
    population_proximity_score : float | None
        Pre-calculated population exposure score (0–100).
        None if this layer is not available.
    environmental_sensitivity_score : float | None
        Pre-calculated environmental sensitivity score (0–100).
        None if this layer is not available.
    config : Config, optional

    Returns
    -------
    OperationalRisk
    """
    cfg = config or get_config()

    # Weights
    w = cfg.weights.get("operational_risk", {})
    w_intensity: float = w.get("thermal_intensity_weight", 0.25)
    w_anomaly: float = w.get("anomaly_persistence_weight", 0.25)
    w_pop: float = w.get("population_proximity_weight", 0.20)
    w_env: float = w.get("environmental_sensitivity_weight", 0.15)
    w_conf: float = w.get("classification_confidence_weight", 0.15)

    # FRP intensity bands
    frp_bands = cfg.get_threshold("risk", "frp_intensity", default={})
    frp_low_max: float = frp_bands.get("low_max", 50)
    frp_med_max: float = frp_bands.get("medium_max", 150)
    frp_high_max: float = frp_bands.get("high_max", 300)

    available_components: list[str] = []
    missing_components: list[str] = []
    contributions: dict[str, float] = {}
    notes: list[str] = []

    # -----------------------------------------------------------------------
    # Component 1: Thermal Intensity (25%)
    # -----------------------------------------------------------------------
    # Use FRP mean; fall back to max if mean unavailable
    frp_ref = frp_mean if frp_mean is not None else frp_max

    if frp_ref is None:
        intensity_score = 0.0
        missing_components.append("thermal_intensity")
        notes.append("FRP data unavailable – thermal intensity component missing.")
    else:
        available_components.append("thermal_intensity")
        if frp_ref <= frp_low_max:
            intensity_score = 25.0 + 25.0 * (frp_ref / frp_low_max)
        elif frp_ref <= frp_med_max:
            intensity_score = 50.0 + 30.0 * (frp_ref - frp_low_max) / (frp_med_max - frp_low_max)
        elif frp_ref <= frp_high_max:
            intensity_score = 80.0 + 15.0 * (frp_ref - frp_med_max) / (frp_high_max - frp_med_max)
        else:
            intensity_score = 95.0 + min(5.0, (frp_ref - frp_high_max) / frp_high_max * 5.0)

    intensity_score = float(np.clip(intensity_score, 0.0, 100.0))
    contributions["thermal_intensity"] = round(intensity_score, 2)

    # -----------------------------------------------------------------------
    # Component 2: Anomaly + Persistence (25%)
    # -----------------------------------------------------------------------
    # Combine anomaly score with industrial likelihood for a risk context
    from .schemas import AnomalyLevel
    anomaly_s = float(anomaly_result.anomaly_score)
    # Boost if anomaly is severe
    if anomaly_result.anomaly_level == AnomalyLevel.SEVERE:
        anomaly_bonus = 10.0
    elif anomaly_result.anomaly_level == AnomalyLevel.ABNORMAL:
        anomaly_bonus = 5.0
    else:
        anomaly_bonus = 0.0

    anomaly_pers_score = float(np.clip(anomaly_s + anomaly_bonus, 0.0, 100.0))
    available_components.append("anomaly_persistence")
    contributions["anomaly_persistence"] = round(anomaly_pers_score, 2)

    # -----------------------------------------------------------------------
    # Component 3: Population Proximity (20%)
    # -----------------------------------------------------------------------
    if population_proximity_score is None:
        pop_score = 0.0
        missing_components.append("population_proximity")
        notes.append(
            "Population proximity layer unavailable – this component is missing from the risk score "
            "(requires_verification). The score is partial."
        )
    else:
        pop_score = float(np.clip(population_proximity_score, 0.0, 100.0))
        available_components.append("population_proximity")

    contributions["population_proximity"] = round(pop_score, 2)

    # -----------------------------------------------------------------------
    # Component 4: Environmental Sensitivity (15%)
    # -----------------------------------------------------------------------
    if environmental_sensitivity_score is None:
        env_score = 0.0
        missing_components.append("environmental_sensitivity")
        notes.append(
            "Environmental sensitivity layer unavailable – this component is missing from the risk score "
            "(requires_verification). The score is partial."
        )
    else:
        env_score = float(np.clip(environmental_sensitivity_score, 0.0, 100.0))
        available_components.append("environmental_sensitivity")

    contributions["environmental_sensitivity"] = round(env_score, 2)

    # -----------------------------------------------------------------------
    # Component 5: Classification Confidence (15%)
    # -----------------------------------------------------------------------
    if confidence_mean is None:
        conf_score = 50.0  # treat as moderate when unknown
        notes.append("Detection confidence data unavailable – using neutral default.")
    else:
        conf_score = float(np.clip(confidence_mean, 0.0, 100.0))
    available_components.append("classification_confidence")
    contributions["classification_confidence"] = round(conf_score, 2)

    # -----------------------------------------------------------------------
    # Weighted composite (adjust weights to account for missing components)
    # -----------------------------------------------------------------------
    # Available weight pairs
    weight_map = {
        "thermal_intensity": w_intensity,
        "anomaly_persistence": w_anomaly,
        "population_proximity": w_pop,
        "environmental_sensitivity": w_env,
        "classification_confidence": w_conf,
    }
    total_available_weight = sum(
        wt for comp, wt in weight_map.items()
        if comp in available_components
    )
    if total_available_weight == 0:
        total_available_weight = 1.0

    composite = sum(
        contributions[comp] * weight_map[comp]
        for comp in available_components
        if comp in contributions
    ) / total_available_weight

    # Incorporate industrial likelihood as a multiplier context
    # Higher industrial likelihood → risk score stays; lower → mild dampening
    il_factor = 0.5 + 0.5 * (industrial_likelihood_score / 100.0)
    composite = composite * il_factor

    risk_score = round(float(np.clip(composite, 0.0, 100.0)), 2)

    # Confidence level
    n_missing = len(missing_components)
    if n_missing == 0:
        score_confidence = "full"
    elif n_missing <= 1:
        score_confidence = "partial"
    else:
        score_confidence = "minimal"

    # Risk level
    risk_cfg = cfg.get_threshold("risk", "levels", default={})
    low_max = risk_cfg.get("low_max", 30)
    med_max = risk_cfg.get("medium_max", 55)
    high_max = risk_cfg.get("high_max", 80)

    if risk_score <= low_max:
        risk_level = RiskLevel.LOW
    elif risk_score <= med_max:
        risk_level = RiskLevel.MEDIUM
    elif risk_score <= high_max:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL

    logger.info("Risk score=%.1f level=%s confidence=%s", risk_score, risk_level.value, score_confidence)

    return OperationalRisk(
        risk_score=risk_score,
        risk_level=risk_level,
        score_confidence=score_confidence,
        available_components=available_components,
        missing_components=missing_components,
        component_contributions=contributions,
        notes=notes,
    )
