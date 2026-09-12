"""
ThermoTrace Centralized Notification & Mail Engine.
Dispatches full intelligence dossiers and operational alerts to thermotrace.india@gmail.com.
"""
import os
import json
import logging
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .auth import get_current_authenticated_user

logger = logging.getLogger("thermotrace.notifications")
router = APIRouter()

# Single Official Destination Email
THERMOTRACE_CENTRAL_EMAIL = "thermotrace.india@gmail.com"

SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "user": os.getenv("SMTP_USER", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "from_email": os.getenv("SMTP_FROM", "thermotrace.india@gmail.com"),
}

def _send_real_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
    """Attempts to send a real email via configured SMTP environment credentials."""
    user = SMTP_CONFIG.get("user")
    pwd = SMTP_CONFIG.get("password")
    if not user or not pwd:
        logger.info(f"[Demo Mail Mode] SMTP credentials not set. Report logged to dispatch ledger for {to_email}.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_CONFIG["from_email"]
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=5) as server:
            server.starttls()
            server.login(user, pwd)
            server.sendmail(SMTP_CONFIG["from_email"], [to_email], msg.as_string())
        logger.info(f"✓ Real SMTP email successfully delivered to {to_email}")
        return True
    except Exception as e:
        logger.warning(f"SMTP dispatch attempt to {to_email} encountered error: {e}")
        return False

# Centralized in-memory dispatch history
DISPATCH_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "MSG-EML-2026-0901",
        "channel": "EMAIL",
        "recipient": THERMOTRACE_CENTRAL_EMAIL,
        "recipient_name": "ThermoTrace Central Intelligence Feed",
        "role": "ANALYST",
        "subject": "[THERMOTRACE DOSSIER] CRITICAL Flaring Surge at Jamnagar Refinery (TT-CASE-001)",
        "status": "DISPATCHED",
        "event_id": "TT-CASE-001",
        "severity": "CRITICAL",
        "timestamp": "2026-09-12T00:00:00Z",
        "preview": "HGB+LSTM detected +13.95σ baseline surge (340 MW). Complete dossier generated."
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
# MODELS & SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class NotificationDispatchRequest(BaseModel):
    event_id: str = "TT-CASE-001"
    facility_name: str = "Jamnagar Mega Refinery Complex"
    facility_distance_km: float = 0.18
    frp_mw: float = 340.0
    baseline_mw: str = "82 ± 18.5 MW"
    baseline_deviation_sigma: float = 13.95
    escalation_tier: str = "CRITICAL_ESCALATION"
    frp_trend_mw_day: float = 42.5
    forecast_t24_mw: float = 374.0
    forecast_t48_mw: float = 400.0
    ai_confidence_pct: float = 94.0
    threat_tier: str = "CRITICAL"  # NORMAL, WATCH, HIGH, CRITICAL, CONFIRMED
    risk_score: float = 84.0
    hazard_radius_m: float = 350.0
    plume_corridor: str = "8.6 km NE"
    wind_vector: str = "25 km/h SW (210°)"
    population_exposure: int = 123
    custom_notes: Optional[str] = None
    target_override_email: Optional[str] = None


class NotificationRecord(BaseModel):
    id: str
    channel: str
    recipient: str
    recipient_name: str
    role: str
    subject: str
    status: str
    event_id: str
    severity: str
    timestamp: str
    preview: str


# ═══════════════════════════════════════════════════════════════════════════════
# HTML TEMPLATE BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_thermotrace_html_email(req: NotificationDispatchRequest) -> str:
    """Comprehensive executive intelligence dossier sent on approval."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin:0; padding:0; background-color:#050C16; color:#E2E8F0; }}
  .box {{ max-width:640px; margin:20px auto; background-color:#0B1626; border:1px solid #1E293B; border-radius:8px; overflow:hidden; }}
  .hdr {{ background:linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding:20px 24px; border-bottom:2px solid #38BDF8; }}
  .badge {{ display:inline-block; padding:4px 10px; font-size:11px; font-weight:800; border-radius:4px; background:#38BDF8; color:#000; text-transform:uppercase; }}
  .title {{ font-size:18px; font-weight:800; margin:10px 0 2px; color:#F8FAFC; }}
  .body {{ padding:24px; font-size:13px; line-height:1.6; }}
  .tbl {{ width:100%; border-collapse:collapse; margin:14px 0; }}
  .tbl td {{ padding:7px 10px; border-bottom:1px solid #1E293B; font-size:12.5px; }}
  .lbl {{ color:#94A3B8; width:38%; }}
  .val {{ color:#F8FAFC; font-weight:600; }}
  .btn {{ display:inline-block; background:#0284C7; color:#FFFFFF !important; font-weight:700; padding:10px 20px; text-decoration:none; border-radius:5px; margin-top:16px; }}
  .ftr {{ padding:14px 24px; background:#050C16; font-size:11px; color:#64748B; text-align:center; border-top:1px solid #1E293B; }}
</style>
</head>
<body>
  <div class="box">
    <div class="hdr">
      <span class="badge">THERMOTRACE · APPROVED INCIDENT DOSSIER</span>
      <div class="title">THERMAL INTELLIGENCE REPORT: {req.event_id}</div>
      <div style="font-size:12px; color:#94A3B8;">Facility Target: {req.facility_name}</div>
    </div>
    <div class="body">
      <p>An authorized ThermoTrace Analyst has reviewed and approved the thermal intelligence dossier for <strong>{req.facility_name}</strong>.</p>
      
      <table class="tbl">
        <tr><td class="lbl">Event Identifier:</td><td class="val">{req.event_id}</td></tr>
        <tr><td class="lbl">Facility Association:</td><td class="val">{req.facility_name} ({req.facility_distance_km} km)</td></tr>
        <tr><td class="lbl">Classification:</td><td class="val">Industrial Thermal Anomaly (AI Confidence: {req.ai_confidence_pct}%)</td></tr>
        <tr><td class="lbl">Observed Peak FRP:</td><td class="val"><span style="color:#FF5C6C; font-weight:700;">{req.frp_mw:.1f} MW</span></td></tr>
        <tr><td class="lbl">Facility Baseline:</td><td class="val">{req.baseline_mw}</td></tr>
        <tr><td class="lbl">Baseline Deviation:</td><td class="val"><strong style="color:#FF5C6C;">+{req.baseline_deviation_sigma:.2f}σ</strong></td></tr>
        <tr><td class="lbl">LSTM Escalation State:</td><td class="val">{req.escalation_tier} (+{req.frp_trend_mw_day:.1f} MW/day)</td></tr>
        <tr><td class="lbl">Trajectory Forecast:</td><td class="val">T+24h: {req.forecast_t24_mw:.0f} MW | T+48h: {req.forecast_t48_mw:.0f} MW</td></tr>
        <tr><td class="lbl">Radiant Hazard (API 521):</td><td class="val">{req.hazard_radius_m:.0f} meters safety perimeter</td></tr>
        <tr><td class="lbl">Gaussian Plume Corridor:</td><td class="val">{req.plume_corridor} ({req.wind_vector})</td></tr>
        <tr><td class="lbl">Population Exposure:</td><td class="val">{req.population_exposure} residents within impact sector</td></tr>
        <tr><td class="lbl">Operational Risk Score:</td><td class="val"><strong style="color:#FF5C6C;">{req.risk_score:.0f} / 100 [{req.threat_tier}]</strong></td></tr>
      </table>

      {f'<div style="background:rgba(56,189,248,0.1); border-left:3px solid #38BDF8; padding:10px 14px; margin:14px 0;"><strong>ANALYST DECISION NOTES:</strong> {req.custom_notes}</div>' if req.custom_notes else ''}

      <div style="background:rgba(239,68,68,0.1); border-left:3px solid #EF4444; padding:10px 14px; margin:14px 0;">
        <strong>RECOMMENDED ACTION:</strong> Engage Flare Gas Recovery (FGRS) diversion, establish {req.hazard_radius_m:.0f}m cordon, and monitor downwind corridor ({req.plume_corridor}).
      </div>

      <center>
        <a href="https://thermotrace.vercel.app" class="btn">View Live Dossier in ThermoTrace Console →</a>
      </center>
    </div>
    <div class="ftr">
      ThermoTrace Automated Intelligence Feed · Dispatched to: <strong>{THERMOTRACE_CENTRAL_EMAIL}</strong>
    </div>
  </div>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/dispatch")
def dispatch_notification(
    req: NotificationDispatchRequest,
    user: Dict[str, Any] = Depends(get_current_authenticated_user)
):
    """
    Dispatches full ThermoTrace report briefing to thermotrace.india@gmail.com.
    """
    tier = req.threat_tier.upper()
    target_email = req.target_override_email or THERMOTRACE_CENTRAL_EMAIL
    now_utc = datetime.now(timezone.utc).isoformat()

    html_content = _build_thermotrace_html_email(req)
    subject = f"[THERMOTRACE REPORT] {tier} — {req.facility_name} ({req.event_id})"

    smtp_sent = _send_real_smtp_email(target_email, subject, html_content)

    record = {
        "id": f"MSG-EML-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}",
        "channel": "EMAIL",
        "recipient": target_email,
        "recipient_name": "ThermoTrace Central Feed",
        "role": "ANALYST",
        "subject": subject,
        "status": "DELIVERED" if smtp_sent else "DISPATCHED_DEMO_MODE",
        "event_id": req.event_id,
        "severity": tier,
        "timestamp": now_utc,
        "preview": f"{tier} dossier for {req.facility_name}. FRP {req.frp_mw:.1f}MW (+{req.baseline_deviation_sigma:.1f}σ).",
        "rendered_html": html_content
    }
    DISPATCH_HISTORY.insert(0, record)

    return {
        "status": "SUCCESS",
        "delivery_status": "DELIVERED" if smtp_sent else "REPORT_GENERATED",
        "threat_tier": tier,
        "recipient": target_email,
        "smtp_sent": smtp_sent,
        "message": f"Report generated and dispatched to {target_email}." if smtp_sent else f"Report generated successfully for {target_email} (Demo Mode log recorded)."
    }


class DirectEmailRequest(BaseModel):
    recipient_email: str = THERMOTRACE_CENTRAL_EMAIL
    recipient_name: Optional[str] = "ThermoTrace Central Feed"
    event_id: str = "TT-CASE-001"
    facility_name: str = "Industrial Facility"
    frp_mw: float = 340.0
    risk_score: float = 85.0
    threat_tier: str = "CRITICAL"
    hazard_radius_m: float = 280.0
    custom_notes: Optional[str] = None


@router.post("/email")
def send_direct_email(req: DirectEmailRequest):
    """Direct email endpoint targeting thermotrace.india@gmail.com."""
    target_email = req.recipient_email or THERMOTRACE_CENTRAL_EMAIL
    dispatch_req = NotificationDispatchRequest(
        event_id=req.event_id,
        facility_name=req.facility_name,
        frp_mw=req.frp_mw,
        risk_score=req.risk_score,
        threat_tier=req.threat_tier,
        hazard_radius_m=req.hazard_radius_m,
        custom_notes=req.custom_notes,
        target_override_email=target_email,
    )
    html_body = _build_thermotrace_html_email(dispatch_req)
    subj = f"[THERMOTRACE {req.threat_tier}] {req.facility_name} ({req.event_id})"
    smtp_sent = _send_real_smtp_email(target_email, subj, html_body)

    record = {
        "id": f"MSG-EML-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}",
        "channel": "EMAIL",
        "recipient": target_email,
        "recipient_name": req.recipient_name or "ThermoTrace Central Feed",
        "role": "DIRECT",
        "subject": subj,
        "status": "DELIVERED" if smtp_sent else "DISPATCHED_DEMO_MODE",
        "event_id": req.event_id,
        "severity": req.threat_tier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "preview": f"Alert for {req.facility_name}. Risk {req.risk_score:.0f}/100.",
        "rendered_html": html_body,
    }
    DISPATCH_HISTORY.insert(0, record)
    return {
        "status": "SUCCESS",
        "message_id": record["id"],
        "recipient": target_email,
        "delivery_status": record["status"],
        "smtp_sent": smtp_sent
    }


@router.get("/history")
def get_notification_history():
    """Returns chronological dispatch audit history."""
    return {
        "total": len(DISPATCH_HISTORY),
        "history": DISPATCH_HISTORY[:50]
    }


@router.get("/config")
def get_notification_routing_config():
    """Returns centralized recipient routing rules."""
    return {
        "central_recipient": THERMOTRACE_CENTRAL_EMAIL,
        "smtp_user": SMTP_CONFIG.get("user") or None,
        "smtp_configured": bool(SMTP_CONFIG.get("user") and SMTP_CONFIG.get("password")),
    }


@router.post("/config")
def update_notification_config(cfg: Dict[str, Any]):
    """Update runtime notification/SMTP settings."""
    if "smtp_user" in cfg and cfg["smtp_user"]:
        SMTP_CONFIG["user"] = cfg["smtp_user"]
    if "smtp_password" in cfg and cfg["smtp_password"]:
        SMTP_CONFIG["password"] = cfg["smtp_password"]
    return {"status": "SUCCESS", "message": "Notification gateway credentials updated"}

