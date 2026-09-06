"""
Alerts API — generated from event data based on risk and anomaly thresholds.
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from .events import _load_all_events

router = APIRouter()

def _generate_alerts(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate alert objects from event data based on risk and anomaly thresholds."""
    alerts = []
    for ev in events:
        eid = ev.get("event_id", "UNKNOWN")
        risk_obj = ev.get("operational_risk", {})
        risk_score = risk_obj.get("risk_score", ev.get("scores", {}).get("operational_risk", 0))
        
        anomaly_obj = ev.get("anomaly", {})
        anomaly_score = anomaly_obj.get("anomaly_score", 0)
        
        alert_obj = ev.get("alert", {})
        alert_type = alert_obj.get("alert_type", "UNKNOWN_REQUIRES_VERIFICATION")
        priority = alert_obj.get("priority", "MEDIUM")
        
        cls_obj = ev.get("classification", {})
        cls_label = cls_obj.get("label", cls_obj.get("class", "Thermal Anomaly"))
        
        fac_obj = ev.get("facility_context", {})
        fac_name = fac_obj.get("nearest_facility_name", fac_obj.get("name", "Unknown Location"))
        
        geom = ev.get("geometry", {})
        lat = geom.get("latitude", geom.get("lat"))
        lon = geom.get("longitude", geom.get("lon"))
        
        time_win = ev.get("time_window", {})
        start_time = time_win.get("start", "")
        
        severity = priority.lower()
        if severity not in ("critical", "high", "medium", "low"):
            if risk_score >= 80 or anomaly_score >= 80:
                severity = "critical"
            elif risk_score >= 50 or anomaly_score >= 50:
                severity = "high"
            elif risk_score >= 30:
                severity = "medium"
            else:
                severity = "low"

        reasons = alert_obj.get("reasons", [])
        if not reasons:
            if risk_score >= 50:
                reasons.append(f"High operational risk score ({risk_score:.1f})")
            if anomaly_score >= 50:
                reasons.append(f"Abnormal thermal activity spike (score {anomaly_score:.1f})")
            if cls_label == "unknown_requires_verification":
                reasons.append("Ambiguous thermal signature requires verification")

        alerts.append({
            "alert_id": f"ALT-{eid}",
            "event_id": eid,
            "severity": severity,
            "title": cls_label.replace("_", " ").title(),
            "location": fac_name,
            "latitude": lat,
            "longitude": lon,
            "operational_risk": risk_score,
            "anomaly_score": anomaly_score,
            "confidence": cls_obj.get("confidence", 0.0),
            "reasons": reasons if reasons else ["System thermal alert threshold reached"],
            "status": ev.get("status", "NEW"),
            "timestamp": start_time,
        })

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda a: (order.get(a["severity"], 4), -a["operational_risk"]))
    return alerts


@router.get("/")
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter: critical, high, medium, low"),
    region: str = Query("All", description="Region filter: India, Global, or All"),
    limit: int = Query(50, le=200),
):
    """List active alerts derived from event risk analysis."""
    events = _load_all_events()
    alerts = _generate_alerts(events)

    if severity:
        alerts = [a for a in alerts if a["severity"].lower() == severity.lower()]

    return {
        "total": len(alerts),
        "critical_count": len([a for a in alerts if a["severity"] == "critical"]),
        "high_count": len([a for a in alerts if a["severity"] == "high"]),
        "medium_count": len([a for a in alerts if a["severity"] == "medium"]),
        "low_count": len([a for a in alerts if a["severity"] == "low"]),
        "alerts": alerts[:limit]
    }
