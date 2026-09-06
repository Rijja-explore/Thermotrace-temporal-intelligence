"""
pipeline.py – ThermoTrace Temporal Intelligence canonical pipeline.

Entry point for integrating all modules into a single analysis pass.

Primary functions:
  analyze_event()    – Analyse a single thermal event given observations
  analyze_facility() – Analyse a facility across its observation history
  run_pipeline()     – Batch pipeline over multiple events/observations

Pipeline steps (in order):
  1. Validate input observations
  2. Cluster observations into thermal events
  3. Extract temporal features
  4. Build facility thermal fingerprint (from historical data)
  5. Compute baseline (pre-period data only)
  6. Compute current vs baseline deviation
  7. Detect anomalies
  8. Score industrial likelihood
  9. Compute operational risk
  10. Generate alert
  11. Assemble evidence bundle
  12. Return canonical PipelineOutput

Returns one canonical JSON-compatible dict per event.

Integration:
  - Person 2: Use get_temporal_features() from evidence.py
  - Person 4: Use PipelineOutput.to_json_dict() for API response

All errors are logged and returned as explicit uncertainty markers,
not silently swallowed.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from . import ENGINE_VERSION, CONFIG_VERSION
from .alerts import generate_alert
from .anomaly import detect_anomaly
from .baseline import compute_baseline, compute_deviation
from .clustering import cluster_observations, validate_observations
from .config_loader import Config, get_config
from .evidence import assemble_evidence, get_temporal_features
from .facility_fingerprint import build_facility_fingerprint
from .industrial_likelihood import score_industrial_likelihood
from .risk import compute_risk
from .schemas import (
    Alert,
    AnomalyLevel,
    AnomalyResult,
    Baseline,
    EvidenceBundle,
    FacilityInfo,
    HistoryQuality,
    IndustrialLikelihood,
    LocationInfo,
    OperationalRisk,
    PipelineOutput,
    RiskLevel,
    TemporalFeatures,
    ThermalEvent,
    TimeWindow,
)
from .temporal_features import extract_temporal_features

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_event(
    observations: list[dict],
    facility_context: Optional[dict] = None,
    historical_observations: Optional[list[dict]] = None,
    current_period_start: Optional[datetime] = None,
    population_proximity_score: Optional[float] = None,
    environmental_sensitivity_score: Optional[float] = None,
    is_new_event: bool = False,
    config_dir: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run the full temporal intelligence pipeline on a set of observations.

    Parameters
    ----------
    observations : list[dict]
        Current-period raw observation dicts (Person 1 schema).
    facility_context : dict, optional
        Additional facility metadata:
          facility_id, facility_type, facility_distance_km, landcover_class
    historical_observations : list[dict], optional
        Historical observations for baseline calculation.
        If None, baseline will be unavailable.
    current_period_start : datetime, optional
        Start of current analysis period (used to separate history from current).
        Defaults to the earliest timestamp in `observations`.
    population_proximity_score : float | None
        Pre-calculated population exposure score (0–100). None if unavailable.
    environmental_sensitivity_score : float | None
        Pre-calculated environmental sensitivity score (0–100). None if unavailable.
    is_new_event : bool
        True if this event has not appeared in previous analysis cycles.
    config_dir : str, optional
        Path to config directory. Defaults to package config/.

    Returns
    -------
    dict
        JSON-serialisable canonical pipeline output.
    """
    cfg = get_config(config_dir)
    logger.info(
        "=== ThermoTrace pipeline START: %d observations ===", len(observations)
    )

    # ------------------------------------------------------------------
    # Step 1: Validate observations
    # ------------------------------------------------------------------
    valid_obs, rejected = validate_observations(observations)
    logger.info(
        "Input: %d total, %d valid, %d rejected", len(observations), len(valid_obs), len(rejected)
    )

    if not valid_obs:
        logger.warning("No valid observations – returning minimal output.")
        return _empty_output(
            reason="No valid observations after validation.",
            config_version=cfg.config_version,
        )

    # ------------------------------------------------------------------
    # Step 2: Cluster observations
    # ------------------------------------------------------------------
    events = cluster_observations(valid_obs, config=cfg)
    logger.info("Clustered into %d events", len(events))

    if not events:
        return _empty_output(reason="Clustering produced no events.", config_version=cfg.config_version)

    # Use the largest cluster (most observations) as the primary event
    primary_event: ThermalEvent = max(events, key=lambda e: e.observation_count)
    event_obs = [o for o in valid_obs if o.observation_id in set(primary_event.observation_ids)]

    # ------------------------------------------------------------------
    # Step 3: Temporal features (current period)
    # ------------------------------------------------------------------
    analysis_end = max(o.timestamp_utc for o in event_obs)
    if isinstance(analysis_end, type(None)):
        analysis_end = datetime.now(timezone.utc).replace(tzinfo=None)

    temporal_feats: TemporalFeatures = extract_temporal_features(
        observations=event_obs,
        analysis_end=analysis_end.replace(tzinfo=None) if hasattr(analysis_end, "tzinfo") and analysis_end.tzinfo else analysis_end,
        event_id=primary_event.event_id,
        facility_id=primary_event.facility_id,
        config=cfg,
    )

    # ------------------------------------------------------------------
    # Step 4: Facility thermal fingerprint
    # ------------------------------------------------------------------
    facility_id = primary_event.facility_id
    facility_type = primary_event.facility_type
    facility_distance_km = primary_event.facility_distance_km
    landcover_class = primary_event.landcover_class

    # Override with facility_context if provided
    if facility_context:
        facility_id = facility_context.get("facility_id", facility_id)
        facility_type = facility_context.get("facility_type", facility_type)
        facility_distance_km = facility_context.get("facility_distance_km", facility_distance_km)
        landcover_class = facility_context.get("landcover_class", landcover_class)

    # Validate historical observations
    hist_valid: list = []
    if historical_observations:
        hist_valid, _ = validate_observations(historical_observations)
        logger.info("Historical observations: %d valid", len(hist_valid))

    fingerprint = build_facility_fingerprint(
        facility_id=facility_id or "UNKNOWN",
        observations=hist_valid,
        facility_type=facility_type,
        config=cfg,
    )

    # ------------------------------------------------------------------
    # Step 5: Baseline
    # ------------------------------------------------------------------
    if current_period_start is None and event_obs:
        current_period_start = min(o.timestamp_utc for o in event_obs)
        if hasattr(current_period_start, "tzinfo") and current_period_start.tzinfo:
            current_period_start = current_period_start.replace(tzinfo=None)

    all_historical = hist_valid + (valid_obs if not hist_valid else [])
    baseline: Baseline = compute_baseline(
        historical_observations=all_historical if not hist_valid else hist_valid,
        current_period_start=current_period_start or datetime.now(timezone.utc).replace(tzinfo=None),
        facility_id=facility_id,
        config=cfg,
    )
    logger.info("Baseline available=%s quality=%s", baseline.available, baseline.history_quality.value)

    # ------------------------------------------------------------------
    # Step 6: Deviation
    # ------------------------------------------------------------------
    tw30 = temporal_feats.window_30d
    current_active_ratio = None
    if tw30.persistence_ratio is not None:
        current_active_ratio = tw30.persistence_ratio

    deviation = compute_deviation(
        current_frp_mean=tw30.frp_mean,
        current_detection_frequency=tw30.detection_frequency,
        current_active_ratio=current_active_ratio,
        current_spatial_extent=tw30.spatial_extent_km,
        baseline=baseline,
    )

    # ------------------------------------------------------------------
    # Step 7: Anomaly detection
    # ------------------------------------------------------------------
    anomaly_result: AnomalyResult = detect_anomaly(
        current_frp_mean=tw30.frp_mean,
        current_frp_max=tw30.frp_max,
        current_detection_frequency=tw30.detection_frequency,
        current_active_ratio=current_active_ratio,
        current_spatial_extent=tw30.spatial_extent_km,
        current_duration_hours=tw30.duration_hours_total,
        baseline=baseline,
        deviation=deviation,
        config=cfg,
    )
    logger.info("Anomaly: score=%.1f level=%s", anomaly_result.anomaly_score, anomaly_result.anomaly_level.value)

    # ------------------------------------------------------------------
    # Step 8: Industrial likelihood
    # ------------------------------------------------------------------
    sensor_count = len(primary_event.sensors)
    il_result: IndustrialLikelihood = score_industrial_likelihood(
        facility_distance_km=facility_distance_km,
        facility_type=facility_type,
        persistence_ratio=tw30.persistence_ratio,
        landcover_class=landcover_class,
        spatial_stability_score=tw30.spatial_stability_score,
        detection_frequency=tw30.detection_frequency,
        sensor_count=sensor_count,
        observation_count=tw30.detection_count,
        config=cfg,
    )
    logger.info("Industrial likelihood: score=%.1f", il_result.score)

    # ------------------------------------------------------------------
    # Step 9: Operational risk
    # ------------------------------------------------------------------
    confidence_vals = [o.confidence for o in event_obs if o.confidence is not None]
    conf_mean = float(sum(confidence_vals) / len(confidence_vals)) if confidence_vals else None

    risk_result: OperationalRisk = compute_risk(
        frp_mean=tw30.frp_mean,
        frp_max=tw30.frp_max,
        anomaly_result=anomaly_result,
        industrial_likelihood_score=il_result.score,
        confidence_mean=conf_mean,
        population_proximity_score=population_proximity_score,
        environmental_sensitivity_score=environmental_sensitivity_score,
        config=cfg,
    )
    logger.info("Risk: score=%.1f level=%s", risk_result.risk_score, risk_result.risk_level.value)

    # ------------------------------------------------------------------
    # Step 10: Alert
    # ------------------------------------------------------------------
    alert: Alert = generate_alert(
        event_id=primary_event.event_id,
        facility_id=facility_id,
        anomaly_result=anomaly_result,
        risk_result=risk_result,
        industrial_likelihood=il_result,
        is_new_event=is_new_event,
        config=cfg,
    )
    logger.info("Alert: type=%s priority=%s", alert.alert_type.value, alert.priority.value)

    # ------------------------------------------------------------------
    # Step 11: Evidence bundle
    # ------------------------------------------------------------------
    evidence: EvidenceBundle = assemble_evidence(
        temporal_features=temporal_feats,
        baseline=baseline,
        anomaly_result=anomaly_result,
        industrial_likelihood=il_result,
        risk_result=risk_result,
        observation_count=len(event_obs),
        facility_distance_km=facility_distance_km,
        facility_type=facility_type,
        landcover_class=landcover_class,
    )

    # ------------------------------------------------------------------
    # Step 12: Canonical output
    # ------------------------------------------------------------------
    output = PipelineOutput(
        event_id=primary_event.event_id,
        location=LocationInfo(
            latitude=primary_event.centroid_latitude,
            longitude=primary_event.centroid_longitude,
        ),
        time_window=TimeWindow(
            start=primary_event.start_time,
            end=primary_event.end_time,
        ),
        temporal_features={
            "window_7d": tw_to_dict(temporal_feats.window_7d),
            "window_30d": tw_to_dict(temporal_feats.window_30d),
            "window_90d": tw_to_dict(temporal_feats.window_90d),
        },
        facility=FacilityInfo(
            facility_id=facility_id,
            facility_type=facility_type,
            distance_km=facility_distance_km,
        ),
        baseline={
            "available": baseline.available,
            "frp_mean": baseline.frp_mean,
            "frp_median": baseline.frp_median,
            "frp_std": baseline.frp_std,
            "frp_upper_quantile": baseline.frp_upper_quantile,
            "frp_lower_quantile": baseline.frp_lower_quantile,
            "detection_frequency": baseline.detection_frequency,
            "active_days_ratio": baseline.active_days_ratio,
            "history_count": baseline.history_count,
            "history_quality": baseline.history_quality.value,
            "notes": baseline.notes,
        },
        deviation=deviation,
        anomaly={
            "score": anomaly_result.anomaly_score,
            "level": anomaly_result.anomaly_level.value,
            "reasons": anomaly_result.reasons,
            "component_scores": anomaly_result.component_scores,
            "data_quality_notes": anomaly_result.data_quality_notes,
        },
        industrial_likelihood={
            "score": il_result.score,
            "requires_verification": il_result.requires_verification,
            "component_scores": il_result.component_scores,
            "evidence_for": il_result.evidence_for,
            "evidence_against": il_result.evidence_against,
            "missing_evidence": il_result.missing_evidence,
        },
        operational_risk={
            "risk_score": risk_result.risk_score,
            "risk_level": risk_result.risk_level.value,
            "score_confidence": risk_result.score_confidence,
            "available_components": risk_result.available_components,
            "missing_components": risk_result.missing_components,
            "component_contributions": risk_result.component_contributions,
            "notes": risk_result.notes,
        },
        alert={
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type.value,
            "priority": alert.priority.value,
            "reason": alert.reason,
            "status": alert.status.value,
        },
        evidence={
            "evidence_for": evidence.evidence_for,
            "evidence_against": evidence.evidence_against,
            "missing_evidence": evidence.missing_evidence,
        },
        recommendation=alert.recommended_action,
        metadata={
            "engine_version": ENGINE_VERSION,
            "config_version": cfg.config_version,
            "analysis_timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "input_count": str(len(observations)),
            "valid_count": str(len(valid_obs)),
            "rejected_count": str(len(rejected)),
            "cluster_count": str(len(events)),
        },
    )

    logger.info("=== ThermoTrace pipeline COMPLETE: event=%s ===", primary_event.event_id)
    return output.to_json_dict()


def analyze_facility(
    facility_id: str,
    all_observations: list[dict],
    current_period_start: datetime,
    current_period_end: Optional[datetime] = None,
    facility_context: Optional[dict] = None,
    population_proximity_score: Optional[float] = None,
    environmental_sensitivity_score: Optional[float] = None,
    config_dir: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run the pipeline for all observations associated with a specific facility.

    Splits observations into historical (pre current_period_start) and
    current-period, then delegates to analyze_event().

    Parameters
    ----------
    facility_id : str
    all_observations : list[dict]
        All observations for this facility (any period).
    current_period_start : datetime
        Start of current analysis window.
    current_period_end : datetime, optional
        End of current analysis window. Defaults to latest timestamp.
    facility_context : dict, optional
    population_proximity_score : float | None
    environmental_sensitivity_score : float | None
    config_dir : str, optional

    Returns
    -------
    dict – canonical pipeline output
    """
    cps = current_period_start.replace(tzinfo=None) if current_period_start.tzinfo else current_period_start

    # Split by period
    current_raw = []
    historical_raw = []
    for obs in all_observations:
        ts_str = obs.get("timestamp_utc", "")
        try:
            from dateutil import parser as dp
            ts = dp.parse(str(ts_str)).replace(tzinfo=None)
            if ts >= cps:
                current_raw.append(obs)
            else:
                historical_raw.append(obs)
        except Exception:
            current_raw.append(obs)  # can't parse – include in current

    logger.info(
        "Facility %s: %d current obs, %d historical obs",
        facility_id, len(current_raw), len(historical_raw),
    )

    return analyze_event(
        observations=current_raw,
        facility_context=facility_context or {"facility_id": facility_id},
        historical_observations=historical_raw,
        current_period_start=cps,
        population_proximity_score=population_proximity_score,
        environmental_sensitivity_score=environmental_sensitivity_score,
        config_dir=config_dir,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tw_to_dict(tw) -> dict:
    """Convert TemporalWindow to a plain dict, replacing datetime objects with ISO strings."""
    d = tw.model_dump()
    for key in ("start", "end"):
        if d.get(key) and hasattr(d[key], "isoformat"):
            d[key] = d[key].isoformat()
    return d


def _empty_output(reason: str, config_version: str = "v1") -> dict:
    """Return a minimal output when processing cannot proceed."""
    from .schemas import AnomalyLevel, RiskLevel
    return {
        "event_id": f"TT-EVENT-{uuid.uuid4().hex[:8].upper()}",
        "location": {"latitude": None, "longitude": None},
        "time_window": {"start": None, "end": None},
        "temporal_features": {},
        "facility": {"facility_id": None, "facility_type": None, "distance_km": None},
        "baseline": {"available": False, "history_quality": "insufficient"},
        "deviation": {},
        "anomaly": {
            "score": 0.0,
            "level": AnomalyLevel.UNKNOWN.value,
            "reasons": [reason],
        },
        "industrial_likelihood": {
            "score": 0.0,
            "requires_verification": True,
            "evidence_for": [],
            "evidence_against": [],
            "missing_evidence": [reason],
        },
        "operational_risk": {
            "risk_score": 0.0,
            "risk_level": RiskLevel.UNKNOWN.value,
            "score_confidence": "minimal",
        },
        "alert": {
            "alert_type": "UNKNOWN_REQUIRES_VERIFICATION",
            "priority": "NONE",
            "status": "NEW",
        },
        "evidence": {
            "evidence_for": [],
            "evidence_against": [],
            "missing_evidence": [reason],
        },
        "recommendation": "Analyst verification required. Insufficient data to process this event.",
        "metadata": {
            "engine_version": ENGINE_VERSION,
            "config_version": config_version,
            "analysis_timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        },
    }
