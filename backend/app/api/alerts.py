"""
Alerts API — generated from event data based on risk thresholds.
"""
from fastapi import APIRouter, Query
from typing import Optional
from .events import _get_all_events, _filter_by_region

router = APIRouter()


def _generate_alerts(events: list) -> list:
    """Generate alert objects from event data based on risk thresholds."""
    alerts = []
    for ev in events:
        risk = ev.get("scores", {}).get("operational_risk", 0)
        confidence = ev.get("classification", {}).get("confidence", 0)
        deviation = ev.get("temporal_features", {}).get("deviation_sigma", 0)

        severity = "low"
        if risk >= 80 or deviation >= 10:
            severity = "critical"
        elif risk >= 60 or deviation >= 3:
            severity = "high"
        elif risk >= 40:
            severity = "medium"

        if severity in ("critical", "high", "medium"):
            reasons = []
            if risk >= 80:
                reasons.append(f"Operational risk {risk}%")
            if deviation >= 3:
                reasons.append(f"Baseline deviation {deviation:.1f}σ")
            if ev.get("status") == "critical_alert":
                reasons.append("Flagged as critical")
            if not reasons:
                reasons.append(f"Risk score {risk}%")

            alerts.append({
                "alert_id": f"ALT-{ev['event_id']}",
                "event_id": ev["event_id"],
                "severity": severity,
                "title": ev.get("classification", {}).get("class", "Thermal Anomaly"),
                "location": ev.get("facility_context", {}).get("name", "Unknown"),
                "lat": ev.get("geometry", {}).get("lat"),
                "lon": ev.get("geometry", {}).get("lon"),
                "operational_risk": risk,
                "confidence": confidence,
                "reasons": reasons,
                "status": ev.get("status", "unknown"),
                "timestamp": ev.get("time_window", {}).get("start", ""),
            })

    # Sort: critical first, then high, then medium
    order = {"critical": 0, "high": 1, "medium": 2}
    alerts.sort(key=lambda a: (order.get(a["severity"], 3), -a["operational_risk"]))
    return alerts


@router.get("/")
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter: critical, high, medium"),
    region: str = Query("India", description="Region filter: India, Global, or All"),
    limit: int = Query(50, le=200),
):
    """List active alerts derived from event risk analysis. Defaults to India region."""
    events = _filter_by_region(_get_all_events(), region)
    alerts = _generate_alerts(events)

    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]

    return {
        "total": len(alerts),
        "critical_count": len([a for a in alerts if a["severity"] == "critical"]),
        "high_count": len([a for a in alerts if a["severity"] == "high"]),
        "medium_count": len([a for a in alerts if a["severity"] == "medium"]),
        "alerts": alerts[:limit],
        "region": region,
    }
