"""
alerts.py – Alert generation engine.

Produces structured alerts based on anomaly, risk, and industrial likelihood scores.
Each alert includes a recommended analyst action.

Alert types:
  NEW_INDUSTRIAL_EVENT         – First detection or recently-started event
  PERSISTENT_SOURCE            – Long-running stable industrial source
  ABNORMAL_INCREASE            – Activity significantly above baseline
  HIGH_OPERATIONAL_RISK        – High/critical risk regardless of type
  UNKNOWN_REQUIRES_VERIFICATION – Insufficient evidence to classify
  NONE                         – No action required (normal activity)

Alert priorities: LOW, MEDIUM, HIGH, CRITICAL, NONE

Recommendations are framed as analyst workflow suggestions.
The system does NOT issue legal, regulatory, or emergency-response directives.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from .schemas import (
    Alert,
    AlertPriority,
    AlertStatus,
    AlertType,
    AnomalyLevel,
    AnomalyResult,
    IndustrialLikelihood,
    OperationalRisk,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Recommended action templates
# -----------------------------------------------------------------------
_ACTIONS = {
    "high_risk_abnormal": (
        "Prioritise analyst verification. Review satellite imagery, event timeline, and "
        "supporting context evidence before escalating."
    ),
    "abnormal_only": (
        "Flag for analyst review. Activity is significantly above the historical baseline; "
        "verify whether this represents a genuine operational change or data artefact."
    ),
    "high_risk_only": (
        "Analyst review recommended. Risk score is elevated; confirm industrial context and "
        "verify supporting evidence before further action."
    ),
    "persistent_normal": (
        "Continue monitoring. Current activity is consistent with historical facility behaviour. "
        "No immediate action required."
    ),
    "requires_verification": (
        "Analyst verification required. Evidence is insufficient or conflicting. "
        "Review raw imagery and cross-reference with facility records before drawing conclusions."
    ),
    "unknown": (
        "Analyst verification required. Insufficient or conflicting evidence prevents automated "
        "classification. Review raw data and contextual sources."
    ),
    "new_event": (
        "New thermal event detected near industrial facility. Monitor for persistence and verify "
        "with available satellite imagery."
    ),
    "normal": (
        "No action required. Activity is within established norms."
    ),
}


def generate_alert(
    event_id: str,
    facility_id: Optional[str],
    anomaly_result: AnomalyResult,
    risk_result: OperationalRisk,
    industrial_likelihood: IndustrialLikelihood,
    is_new_event: bool = False,
    config=None,
) -> Alert:
    """
    Generate an alert from anomaly, risk, and industrial likelihood results.

    Parameters
    ----------
    event_id : str
    facility_id : str | None
    anomaly_result : AnomalyResult
    risk_result : OperationalRisk
    industrial_likelihood : IndustrialLikelihood
    is_new_event : bool
        True if this event has not appeared in previous analysis cycles.
    config : Config, optional (unused – reserved for future threshold configuration)

    Returns
    -------
    Alert
    """
    anomaly_score = anomaly_result.anomaly_score
    anomaly_level = anomaly_result.anomaly_level
    risk_score = risk_result.risk_score
    risk_level = risk_result.risk_level
    il_score = industrial_likelihood.score
    requires_v = industrial_likelihood.requires_verification

    # -----------------------------------------------------------------------
    # Determine alert type and priority
    # -----------------------------------------------------------------------
    alert_type: AlertType
    priority: AlertPriority
    reason: str
    recommended_action: str

    # Case 1: Unknown / insufficient evidence
    if anomaly_level == AnomalyLevel.UNKNOWN or requires_v:
        alert_type = AlertType.UNKNOWN_REQUIRES_VERIFICATION
        priority = AlertPriority.MEDIUM
        reason = (
            "Insufficient or conflicting evidence to classify this event. "
            "Analyst verification is required."
        )
        recommended_action = _ACTIONS["requires_verification"]

    # Case 2: Critical/High risk regardless of anomaly
    elif risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH) and anomaly_level in (
        AnomalyLevel.SEVERE, AnomalyLevel.ABNORMAL
    ):
        alert_type = AlertType.ABNORMAL_INCREASE
        priority = AlertPriority.CRITICAL if risk_level == RiskLevel.CRITICAL else AlertPriority.HIGH
        reason = (
            f"Activity is {anomaly_level.value.upper()} (score {anomaly_score:.0f}) with "
            f"{risk_level.value.upper()} operational risk (score {risk_score:.0f}). "
            f"Industrial likelihood: {il_score:.0f}."
        )
        recommended_action = _ACTIONS["high_risk_abnormal"]

    elif risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
        alert_type = AlertType.HIGH_OPERATIONAL_RISK
        priority = AlertPriority.HIGH
        reason = (
            f"Operational risk is {risk_level.value.upper()} (score {risk_score:.0f}). "
            f"Anomaly level: {anomaly_level.value}."
        )
        recommended_action = _ACTIONS["high_risk_only"]

    # Case 3: Severe/Abnormal anomaly
    elif anomaly_level == AnomalyLevel.SEVERE:
        alert_type = AlertType.ABNORMAL_INCREASE
        priority = AlertPriority.HIGH
        reason = (
            f"Severe anomaly detected (score {anomaly_score:.0f}). "
            f"Activity is significantly above historical baseline. "
            f"Industrial likelihood: {il_score:.0f}."
        )
        recommended_action = _ACTIONS["abnormal_only"]

    elif anomaly_level == AnomalyLevel.ABNORMAL:
        alert_type = AlertType.ABNORMAL_INCREASE
        priority = AlertPriority.MEDIUM
        reason = (
            f"Anomalous activity detected (score {anomaly_score:.0f}). "
            f"Activity is above historical baseline. Risk: {risk_level.value}."
        )
        recommended_action = _ACTIONS["abnormal_only"]

    # Case 4: New event
    elif is_new_event and il_score >= 50:
        alert_type = AlertType.NEW_INDUSTRIAL_EVENT
        priority = AlertPriority.MEDIUM
        reason = (
            f"New industrial thermal event detected near facility. "
            f"Industrial likelihood: {il_score:.0f}. Anomaly: {anomaly_level.value}."
        )
        recommended_action = _ACTIONS["new_event"]

    # Case 5: Normal activity
    elif anomaly_level == AnomalyLevel.NORMAL:
        alert_type = AlertType.PERSISTENT_SOURCE if il_score >= 60 else AlertType.NONE
        priority = AlertPriority.LOW if alert_type != AlertType.NONE else AlertPriority.NONE
        reason = (
            "Activity is within historical norms. "
            f"Industrial likelihood: {il_score:.0f}. Anomaly score: {anomaly_score:.0f}."
        )
        recommended_action = _ACTIONS["persistent_normal"]

    # Case 6: Watch
    else:
        alert_type = AlertType.UNKNOWN_REQUIRES_VERIFICATION
        priority = AlertPriority.LOW
        reason = (
            f"Activity is at WATCH level (score {anomaly_score:.0f}). "
            "Monitor for escalation."
        )
        recommended_action = _ACTIONS["requires_verification"]

    alert = Alert(
        alert_id=f"TT-ALERT-{uuid.uuid4().hex[:8].upper()}",
        event_id=event_id,
        facility_id=facility_id,
        alert_type=alert_type,
        priority=priority,
        reason=reason,
        risk_score=round(risk_score, 2),
        anomaly_score=round(anomaly_score, 2),
        industrial_likelihood=round(il_score, 2),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        recommended_action=recommended_action,
        status=AlertStatus.NEW,
    )

    logger.info(
        "Alert generated: type=%s priority=%s event=%s",
        alert_type.value, priority.value, event_id,
    )
    return alert
