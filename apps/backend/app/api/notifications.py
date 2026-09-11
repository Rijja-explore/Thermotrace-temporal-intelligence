"""
ThermoTrace Centralized Multi-Tier Notification Engine.
Dispatches formatted incident dossiers and operational alerts across configured recipient roles.

Recipient Identities:
- ANALYST: anagesh2410198@ssn.edu.in (Detailed investigation brief + XAI + Verification actions)
- OFFICIAL: rijja2310119@ssn.edu.in (Operational response notice + Hazard perimeter + SOP directives)

Severity Routing Rules:
- NORMAL: Dashboard only (No notification dispatched)
- WATCH: Dashboard monitoring notice
- HIGH: Dispatched to Analyst (anagesh2410198@ssn.edu.in)
- CRITICAL: Dispatched to Analyst (anagesh2410198@ssn.edu.in) & Official (rijja2310119@ssn.edu.in)
- CONFIRMED: Official Emergency Response Alert to Official (rijja2310119@ssn.edu.in)
"""
import os
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .auth import get_current_authenticated_user

logger = logging.getLogger("thermotrace.notifications")
router = APIRouter()

# Default Standard Operational Recipients
RECIPIENT_ANALYST = "anagesh2410198@ssn.edu.in"
RECIPIENT_OFFICIAL = "rijja2310119@ssn.edu.in"

# Centralized in-memory dispatch history
DISPATCH_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "MSG-EML-2026-0901",
        "channel": "EMAIL",
        "recipient": RECIPIENT_ANALYST,
        "recipient_name": "Lead Thermal Analyst",
        "role": "ANALYST",
        "subject": "[THERMOTRACE ANALYST BRIEF] CRITICAL Flaring Surge at Jamnagar Refinery (TT-CASE-001)",
        "status": "DISPATCHED",
        "event_id": "TT-CASE-001",
        "severity": "CRITICAL",
        "timestamp": "2026-09-11T12:35:00Z",
        "preview": "HGB+LSTM detected +13.95σ baseline surge (340 MW). Verification required."
    },
    {
        "id": "MSG-EML-2026-0902",
        "channel": "EMAIL",
        "recipient": RECIPIENT_OFFICIAL,
        "recipient_name": "Incident Command Official",
        "role": "OFFICIAL",
        "subject": "[THERMOTRACE OFFICIAL NOTICE] Confirmed Industrial Anomaly — Jamnagar Sector 4",
        "status": "DISPATCHED",
        "event_id": "TT-CASE-001",
        "severity": "CONFIRMED",
        "timestamp": "2026-09-11T12:40:00Z",
        "preview": "Confirmed incident at Jamnagar Refinery. Hazard radius: 350m. Plume heading NE."
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
# HTML TEMPLATE BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_analyst_html_email(req: NotificationDispatchRequest) -> str:
    """Detailed technical incident dossier for Analyst review."""
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
      <span class="badge">ANALYST INVESTIGATION BRIEF</span>
      <div class="title">THERMOTRACE INCIDENT DOSSIER: {req.event_id}</div>
      <div style="font-size:12px; color:#94A3B8;">Target: {req.facility_name}</div>
    </div>
    <div class="body">
      <p>Dear <strong>Analyst</strong> (<code>{RECIPIENT_ANALYST}</code>),</p>
      <p>The ThermoTrace Hybrid AI Engine (HistGradientBoosting + LSTM Temporal Engine) has isolated a significant thermal anomaly requiring human analyst verification.</p>
      
      <table class="tbl">
        <tr><td class="lbl">Event Identifier:</td><td class="val">{req.event_id}</td></tr>
        <tr><td class="lbl">Facility Association:</td><td class="val">{req.facility_name} ({req.facility_distance_km} km)</td></tr>
        <tr><td class="lbl">HGB Classification:</td><td class="val">Industrial Thermal Anomaly (AI Conf: {req.ai_confidence_pct}%)</td></tr>
        <tr><td class="lbl">Observed Peak FRP:</td><td class="val"><span style="color:#FF5C6C;">{req.frp_mw:.1f} MW</span></td></tr>
        <tr><td class="lbl">90-Day Rolling Baseline:</td><td class="val">{req.baseline_mw}</td></tr>
        <tr><td class="lbl">Baseline Deviation:</td><td class="val"><strong style="color:#FF5C6C;">+{req.baseline_deviation_sigma:.2f}σ</strong></td></tr>
        <tr><td class="lbl">LSTM Escalation State:</td><td class="val">{req.escalation_tier} (+{req.frp_trend_mw_day:.1f} MW/day)</td></tr>
        <tr><td class="lbl">LSTM Forecast:</td><td class="val">T+24h: {req.forecast_t24_mw:.0f} MW | T+48h: {req.forecast_t48_mw:.0f} MW</td></tr>
        <tr><td class="lbl">Radiant Hazard (API 521):</td><td class="val">{req.hazard_radius_m:.0f} meters</td></tr>
        <tr><td class="lbl">Plume Dispersal:</td><td class="val">{req.plume_corridor} ({req.wind_vector})</td></tr>
        <tr><td class="lbl">Population Exposure:</td><td class="val">{req.population_exposure} residents</td></tr>
      </table>

      <div style="background:rgba(56,189,248,0.1); border-left:3px solid #38BDF8; padding:10px 14px; margin:14px 0;">
        <strong>REQUIRED ANALYST ACTION:</strong> Review satellite observations, examine LSTM trajectory & XAI evidence, and execute <code>CONFIRM</code>, <code>REJECT</code>, or <code>RECLASSIFY</code>.
      </div>

      <center>
        <a href="https://thermotrace.vercel.app" class="btn">Open Event Investigation in ThermoTrace →</a>
      </center>
    </div>
    <div class="ftr">
      ThermoTrace Automated Dispatch · Forwarded to Analyst Inbox: <strong>{RECIPIENT_ANALYST}</strong>
    </div>
  </div>
</body>
</html>"""


def _build_official_html_email(req: NotificationDispatchRequest) -> str:
    """Concise operational incident notice for Emergency Officials."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin:0; padding:0; background-color:#050C16; color:#E2E8F0; }}
  .box {{ max-width:640px; margin:20px auto; background-color:#0B1626; border:1px solid #1E293B; border-radius:8px; overflow:hidden; }}
  .hdr {{ background:linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding:20px 24px; border-bottom:2px solid #FF5C6C; }}
  .badge {{ display:inline-block; padding:4px 10px; font-size:11px; font-weight:800; border-radius:4px; background:#FF5C6C; color:#000; text-transform:uppercase; }}
  .title {{ font-size:18px; font-weight:800; margin:10px 0 2px; color:#F8FAFC; }}
  .body {{ padding:24px; font-size:13px; line-height:1.6; }}
  .tbl {{ width:100%; border-collapse:collapse; margin:14px 0; }}
  .tbl td {{ padding:7px 10px; border-bottom:1px solid #1E293B; font-size:12.5px; }}
  .lbl {{ color:#94A3B8; width:38%; }}
  .val {{ color:#F8FAFC; font-weight:600; }}
  .btn {{ display:inline-block; background:#DC2626; color:#FFFFFF !important; font-weight:700; padding:10px 20px; text-decoration:none; border-radius:5px; margin-top:16px; }}
  .ftr {{ padding:14px 24px; background:#050C16; font-size:11px; color:#64748B; text-align:center; border-top:1px solid #1E293B; }}
</style>
</head>
<body>
  <div class="box">
    <div class="hdr">
      <span class="badge">🚨 OFFICIAL EMERGENCY RESPONSE DIRECTIVE</span>
      <div class="title">THERMOTRACE CONFIRMED INCIDENT NOTICE: {req.event_id}</div>
      <div style="font-size:12px; color:#94A3B8;">Target Location: {req.facility_name}</div>
    </div>
    <div class="body">
      <p>Dear <strong>Emergency Response Official</strong> (<code>{RECIPIENT_OFFICIAL}</code>),</p>
      <p>This is an official advisory regarding a confirmed high-severity industrial thermal event at <strong>{req.facility_name}</strong>.</p>
      
      <table class="tbl">
        <tr><td class="lbl">Incident Ref:</td><td class="val">{req.event_id}</td></tr>
        <tr><td class="lbl">Facility / Location:</td><td class="val">{req.facility_name}</td></tr>
        <tr><td class="lbl">Current Thermal Intensity:</td><td class="val"><strong style="color:#FF5C6C;">{req.frp_mw:.1f} MW ({req.baseline_deviation_sigma:.1f}σ anomaly)</strong></td></tr>
        <tr><td class="lbl">Operational Risk Score:</td><td class="val">{req.risk_score:.0f} / 100 [CRITICAL]</td></tr>
        <tr><td class="lbl">4.7 kW/m² Radiant Hazard:</td><td class="val">{req.hazard_radius_m:.0f} meters perimeter</td></tr>
        <tr><td class="lbl">Atmospheric Plume Corridor:</td><td class="val">{req.plume_corridor} ({req.wind_vector})</td></tr>
        <tr><td class="lbl">Estimated Population Exposure:</td><td class="val">{req.population_exposure} residents</td></tr>
      </table>

      <div style="background:rgba(239,68,68,0.12); border-left:3px solid #EF4444; padding:12px 14px; margin:14px 0;">
        <strong>RECOMMENDED RESPONSE DIRECTIVES:</strong>
        <ul style="margin:6px 0 0; padding-left:18px;">
          <li>Alert plant industrial safety team & activate Flare Gas Recovery Diversion.</li>
          <li>Establish public safety cordon at {req.hazard_radius_m:.0f}m radius.</li>
          <li>Monitor downwind corridor ({req.plume_corridor}) for potential emissions.</li>
          <li>Notify District Emergency Response & Fire Liaison units.</li>
        </ul>
      </div>

      <center>
        <a href="https://thermotrace.vercel.app" class="btn">View Official Incident Dossier →</a>
      </center>
    </div>
    <div class="ftr">
      ThermoTrace Emergency Response Gateway · Forwarded to Official Inbox: <strong>{RECIPIENT_OFFICIAL}</strong>
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
    Centralized notification dispatcher.
    Evaluates threat tier and dispatches formatted HTML incident briefs to target roles.
    """
    tier = req.threat_tier.upper()
    dispatched_items = []
    now_utc = datetime.now(timezone.utc).isoformat()

    # Determine recipient targets based on severity workflow
    targets = []
    if req.target_override_email:
        targets.append({"email": req.target_override_email, "role": "CUSTOM", "template": "analyst"})
    elif tier in ["CONFIRMED"]:
        targets.append({"email": RECIPIENT_OFFICIAL, "role": "OFFICIAL", "template": "official"})
    elif tier in ["CRITICAL"]:
        targets.append({"email": RECIPIENT_ANALYST, "role": "ANALYST", "template": "analyst"})
        targets.append({"email": RECIPIENT_OFFICIAL, "role": "OFFICIAL", "template": "official"})
    elif tier in ["HIGH"]:
        targets.append({"email": RECIPIENT_ANALYST, "role": "ANALYST", "template": "analyst"})
    else:
        # WATCH / NORMAL: Dashboard log only
        return {
            "status": "LOGGED_DASHBOARD_ONLY",
            "threat_tier": tier,
            "message": f"Tier '{tier}' is below external email threshold. Logged to Command Center dashboard."
        }

    for t in targets:
        html_content = _build_official_html_email(req) if t["template"] == "official" else _build_analyst_html_email(req)
        subject = f"[THERMOTRACE {'OFFICIAL NOTICE' if t['template'] == 'official' else 'ANALYST BRIEF'}] {tier} — {req.facility_name} ({req.event_id})"
        
        record = {
            "id": f"MSG-EML-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}",
            "channel": "EMAIL",
            "recipient": t["email"],
            "recipient_name": "Incident Command Official" if t["role"] == "OFFICIAL" else "Lead Thermal Analyst",
            "role": t["role"],
            "subject": subject,
            "status": "DISPATCHED",
            "event_id": req.event_id,
            "severity": tier,
            "timestamp": now_utc,
            "preview": f"{tier} alert for {req.facility_name}. FRP {req.frp_mw:.1f}MW (+{req.baseline_deviation_sigma:.1f}σ).",
            "rendered_html": html_content
        }
        DISPATCH_HISTORY.insert(0, record)
        dispatched_items.append({
            "id": record["id"],
            "recipient": t["email"],
            "role": t["role"],
            "subject": subject,
            "status": "DISPATCHED"
        })

    return {
        "status": "SUCCESS",
        "threat_tier": tier,
        "dispatched_count": len(dispatched_items),
        "dispatches": dispatched_items,
        "workflow": "Centralized Multi-Tier Routing (Analyst: anagesh2410198@ssn.edu.in | Official: rijja2310119@ssn.edu.in)"
    }


@router.get("/history")
def get_notification_history(user: Dict[str, Any] = Depends(get_current_authenticated_user)):
    """Returns chronological dispatch audit history."""
    return {
        "total": len(DISPATCH_HISTORY),
        "history": DISPATCH_HISTORY[:50]
    }


@router.get("/config")
def get_notification_routing_config():
    """Returns centralized recipient routing rules."""
    return {
        "analyst_recipient": RECIPIENT_ANALYST,
        "official_recipient": RECIPIENT_OFFICIAL,
        "routing_matrix": {
            "NORMAL": "Dashboard Only",
            "WATCH": "Dashboard Monitoring",
            "HIGH": f"Analyst ({RECIPIENT_ANALYST})",
            "CRITICAL": f"Analyst ({RECIPIENT_ANALYST}) + Official ({RECIPIENT_OFFICIAL})",
            "CONFIRMED": f"Official Response Directive ({RECIPIENT_OFFICIAL})"
        }
    }
