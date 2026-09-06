"""
evidence.py – Evidence bundle assembler.

Aggregates evidence_for, evidence_against, and missing_evidence from all
module outputs into a single EvidenceBundle for the canonical output.

Also exposes get_temporal_features() – the feature interface for Person 2.
"""

from __future__ import annotations

from typing import Optional

from .schemas import (
    AnomalyResult,
    Baseline,
    EvidenceBundle,
    IndustrialLikelihood,
    OperationalRisk,
    TemporalFeatures,
)


def assemble_evidence(
    temporal_features: TemporalFeatures,
    baseline: Baseline,
    anomaly_result: AnomalyResult,
    industrial_likelihood: IndustrialLikelihood,
    risk_result: OperationalRisk,
    observation_count: int,
    facility_distance_km: Optional[float],
    facility_type: Optional[str],
    landcover_class: Optional[str],
) -> EvidenceBundle:
    """
    Assemble all evidence from module outputs into one EvidenceBundle.
    De-duplicates entries across modules.
    """
    evidence_for: list[str] = []
    evidence_against: list[str] = []
    missing_evidence: list[str] = []

    # -----------------------------------------------------------------------
    # From industrial likelihood (already computed per-signal)
    # -----------------------------------------------------------------------
    evidence_for.extend(industrial_likelihood.evidence_for)
    evidence_against.extend(industrial_likelihood.evidence_against)
    missing_evidence.extend(industrial_likelihood.missing_evidence)

    # -----------------------------------------------------------------------
    # From anomaly results
    # -----------------------------------------------------------------------
    for r in anomaly_result.reasons:
        if "within historical norms" in r or "within" in r.lower():
            evidence_against.append(f"[Anomaly] {r}")
        else:
            evidence_for.append(f"[Anomaly] {r}")

    for note in anomaly_result.data_quality_notes:
        missing_evidence.append(f"[Anomaly] {note}")

    # -----------------------------------------------------------------------
    # From baseline
    # -----------------------------------------------------------------------
    for note in baseline.notes:
        missing_evidence.append(f"[Baseline] {note}")

    # -----------------------------------------------------------------------
    # From risk
    # -----------------------------------------------------------------------
    for note in risk_result.notes:
        missing_evidence.append(f"[Risk] {note}")

    # -----------------------------------------------------------------------
    # Observation count evidence
    # -----------------------------------------------------------------------
    tw30 = temporal_features.window_30d
    if tw30.detection_count > 0:
        evidence_for.append(
            f"{tw30.detection_count} thermal detections in the 30-day analysis window."
        )
    if tw30.frp_mean:
        evidence_for.append(
            f"Mean FRP = {tw30.frp_mean:.1f} MW in 30-day window."
        )

    # -----------------------------------------------------------------------
    # Deduplicate
    # -----------------------------------------------------------------------
    def dedup(lst: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    return EvidenceBundle(
        evidence_for=dedup(evidence_for),
        evidence_against=dedup(evidence_against),
        missing_evidence=dedup(missing_evidence),
    )


# -----------------------------------------------------------------------
# Person 2 Feature Interface
# -----------------------------------------------------------------------

def get_temporal_features(
    temporal_features: TemporalFeatures,
    anomaly_result: AnomalyResult,
    industrial_likelihood: IndustrialLikelihood,
    baseline: Baseline,
    facility_distance_km: Optional[float] = None,
    landcover_class: Optional[str] = None,
) -> dict:
    """
    Return a flat feature dictionary for Person 2's ML classifier.

    Feature names are stable and documented in docs/FEATURE_CONTRACT.md.
    All values are float or None. None indicates the feature is unavailable.

    Parameters
    ----------
    temporal_features : TemporalFeatures
    anomaly_result : AnomalyResult
    industrial_likelihood : IndustrialLikelihood
    baseline : Baseline
    facility_distance_km : float | None
    landcover_class : str | None

    Returns
    -------
    dict[str, float | None]
        Flat feature dictionary keyed by feature name.
    """
    tw7 = temporal_features.window_7d
    tw30 = temporal_features.window_30d
    tw90 = temporal_features.window_90d

    features: dict = {
        # --- Persistence (7/30/90d) ---
        "persistence_ratio_7d": tw7.persistence_ratio,
        "persistence_ratio_30d": tw30.persistence_ratio,
        "persistence_ratio_90d": tw90.persistence_ratio,
        "active_days_7d": tw7.active_days,
        "active_days_30d": tw30.active_days,
        "active_days_90d": tw90.active_days,

        # --- Duration ---
        "duration_hours_7d": tw7.duration_hours_total,
        "duration_hours_30d": tw30.duration_hours_total,
        "duration_hours_90d": tw90.duration_hours_total,

        # --- FRP statistics (30d primary window) ---
        "frp_mean_7d": tw7.frp_mean,
        "frp_mean_30d": tw30.frp_mean,
        "frp_mean_90d": tw90.frp_mean,
        "frp_median_30d": tw30.frp_median,
        "frp_max_30d": tw30.frp_max,
        "frp_min_30d": tw30.frp_min,
        "frp_std_30d": tw30.frp_std,
        "frp_p90_30d": tw30.frp_p90,
        "frp_p95_30d": tw30.frp_p95,

        # --- Spatial stability ---
        "spatial_extent_km_30d": tw30.spatial_extent_km,
        "spatial_stability_score_30d": tw30.spatial_stability_score,

        # --- Detection frequency ---
        "detection_frequency_7d": tw7.detection_frequency,
        "detection_frequency_30d": tw30.detection_frequency,
        "detection_frequency_90d": tw90.detection_frequency,
        "days_since_last_detection": tw30.days_since_last_detection,

        # --- Baseline deviation ---
        "baseline_frp_mean": baseline.frp_mean,
        "baseline_frp_std": baseline.frp_std,
        "baseline_detection_frequency": baseline.detection_frequency,
        "baseline_available": 1.0 if baseline.available else 0.0,

        # --- Anomaly score ---
        "anomaly_score": anomaly_result.anomaly_score,
        "anomaly_level_encoded": _encode_anomaly_level(anomaly_result.anomaly_level.value),

        # --- Industrial likelihood ---
        "industrial_likelihood_score": industrial_likelihood.score,
        "il_facility_proximity_score": industrial_likelihood.component_scores.get("facility_proximity"),
        "il_persistence_score": industrial_likelihood.component_scores.get("persistence"),
        "il_landcover_score": industrial_likelihood.component_scores.get("landcover"),
        "il_spatial_stability_score": industrial_likelihood.component_scores.get("spatial_stability"),
        "il_temporal_score": industrial_likelihood.component_scores.get("temporal"),
        "il_sensor_agreement_score": industrial_likelihood.component_scores.get("sensor_agreement"),

        # --- Facility proximity ---
        "facility_distance_km": facility_distance_km,

        # --- Land cover (encoded) ---
        "landcover_class_encoded": _encode_landcover(landcover_class),

        # --- Day/night distribution ---
        "day_detection_ratio_30d": _safe_ratio(tw30.day_count, tw30.detection_count),
        "night_detection_ratio_30d": _safe_ratio(tw30.night_count, tw30.detection_count),
        "weekend_detection_ratio_30d": _safe_ratio(tw30.weekend_count, tw30.detection_count),
    }

    return features


def _encode_anomaly_level(level: str) -> float:
    """Encode anomaly level as ordinal float."""
    mapping = {"normal": 0.0, "watch": 1.0, "abnormal": 2.0, "severe": 3.0, "unknown": -1.0}
    return mapping.get(level.lower(), -1.0)


def _encode_landcover(lc: Optional[str]) -> Optional[float]:
    """Encode land cover as ordinal: industrial=1, natural=0, unknown=None."""
    if lc is None:
        return None
    lc_lower = lc.lower().strip()
    industrial = {"industrial", "urban", "built-up", "commercial", "refinery", "factory",
                  "power_plant", "mining", "port", "warehouse"}
    natural = {"forest", "shrubland", "grassland", "savanna", "cropland",
               "wetland", "water", "bare", "tundra", "snow"}
    if lc_lower in industrial:
        return 1.0
    if lc_lower in natural:
        return 0.0
    return 0.5  # ambiguous


def _safe_ratio(numerator: int, denominator: int) -> Optional[float]:
    """Safely compute numerator/denominator, returning None if denominator == 0."""
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)
