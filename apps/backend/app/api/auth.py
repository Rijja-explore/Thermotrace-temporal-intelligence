"""
Authentication & Authorization API for ThermoTrace Satellite GeoAI Command Center.
Provides defense-grade clearance tokens, analyst personas, and audit trail logs.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

# ─── PRE-CONFIGURED DEMO PERSONAS ───
DEMO_PERSONAS = [
    {
        "user_id": "AL-001",
        "username": "dr_mehta",
        "name": "Dr. Rijja Mehta",
        "email": "r.mehta@thermotrace.gov.in",
        "role": "Lead Thermal Intelligence Analyst",
        "badge": "AL",
        "clearance_level": "Level 4 — Orbital Top Secret",
        "clearance_code": "SEC-CLR-L4-ORBITAL",
        "agency": "ISRO / GeoAI Space Applications Centre",
        "station": "SAC Ahmedabad / Command Terminal 01",
        "permissions": [
            "events:verify",
            "events:reclassify",
            "satellite:tasking",
            "model:retrain",
            "what_if:simulate",
            "emergency:override",
            "reports:export"
        ],
        "avatar_gradient": "linear-gradient(135deg, #43D9E8 0%, #1D4ED8 100%)",
        "is_active": True,
        "last_login": "2026-09-06T08:34:12Z"
    },
    {
        "user_id": "JS-002",
        "username": "capt_sharma",
        "name": "Capt. Rajesh Sharma",
        "email": "r.sharma@jamnagar.ril.in",
        "role": "Chief Safety Officer — Jamnagar Complex",
        "badge": "JS",
        "clearance_level": "Level 2 — Plant Operations",
        "clearance_code": "SEC-CLR-L2-FACILITY",
        "agency": "Reliance Petroleum & Petrochemical Operations",
        "station": "Jamnagar Mega Refinery Emergency Ops Cell",
        "permissions": [
            "facility:read",
            "facility:telemetry",
            "alerts:acknowledge",
            "what_if:simulate",
            "mitigation:sop_execute",
            "reports:export"
        ],
        "avatar_gradient": "linear-gradient(135deg, #FFB547 0%, #EA580C 100%)",
        "is_active": True,
        "last_login": "2026-09-06T06:15:40Z"
    },
    {
        "user_id": "EV-003",
        "username": "priya_nair",
        "name": "Priya Nair",
        "email": "p.nair@cpcb.nic.in",
        "role": "Senior Environmental Compliance Auditor",
        "badge": "EV",
        "clearance_level": "Level 3 — Environmental Regulatory",
        "clearance_code": "SEC-CLR-L3-REGULATORY",
        "agency": "Central Pollution Control Board (CPCB / MoEFCC)",
        "station": "CPCB Headquarters, New Delhi — Air Quality Directorate",
        "permissions": [
            "events:read",
            "facility:audit",
            "violations:file",
            "what_if:simulate",
            "reports:export"
        ],
        "avatar_gradient": "linear-gradient(135deg, #4FD18B 0%, #059669 100%)",
        "is_active": True,
        "last_login": "2026-09-05T16:48:22Z"
    },
    {
        "user_id": "DM-004",
        "username": "vikram_singh",
        "name": "Vikramaditya Singh",
        "email": "v.singh@ndrf.gov.in",
        "role": "Disaster Response Liaison Officer",
        "badge": "DM",
        "clearance_level": "Level 3 — Emergency Response",
        "clearance_code": "SEC-CLR-L3-NDRF",
        "agency": "National Disaster Response Force (NDRF)",
        "station": "8th Battalion NDRF — Regional Emergency Command",
        "permissions": [
            "events:read",
            "alerts:dispatch",
            "evacuation:zone_calc",
            "what_if:simulate",
            "emergency:override",
            "reports:export"
        ],
        "avatar_gradient": "linear-gradient(135deg, #FF5C6C 0%, #B91C1C 100%)",
        "is_active": True,
        "last_login": "2026-09-05T19:22:05Z"
    }
]

AUDIT_LOGS = [
    {
        "timestamp": "2026-09-06T08:34:12Z",
        "user_id": "AL-001",
        "actor": "Dr. Rijja Mehta",
        "action": "AUTH_LOGIN_SUCCESS",
        "ip": "10.14.88.23 (NRSC Hyderabad Secure Gateway)",
        "status": "AUTHORIZED",
        "details": "Biometric 2FA challenge verified against ISRO Keycloak directory"
    },
    {
        "timestamp": "2026-09-06T06:15:40Z",
        "user_id": "JS-002",
        "actor": "Capt. Rajesh Sharma",
        "action": "AUTH_LOGIN_SUCCESS",
        "ip": "172.16.4.110 (Jamnagar Complex Secure Intranet)",
        "status": "AUTHORIZED",
        "details": "Plant hardware security token authenticated"
    },
    {
        "timestamp": "2026-09-05T22:11:04Z",
        "user_id": "SYSTEM",
        "actor": "Satellite Downlink Daemon",
        "action": "TOKEN_ROTATION",
        "ip": "127.0.0.1 (Localhost)",
        "status": "AUTOMATED",
        "details": "Rotated MODIS & VIIRS telemetry ingest credentials"
    }
]

class LoginRequest(BaseModel):
    username_or_email: str
    password: Optional[str] = None
    role_id: Optional[str] = None
    use_2fa_simulation: bool = True

class SessionResponse(BaseModel):
    token: str
    user: Dict[str, Any]
    session_expires_at: str
    authorized_permissions: List[str]


@router.get("/personas")
async def list_personas():
    """Retrieve available pre-configured demo personas."""
    return {
        "total": len(DEMO_PERSONAS),
        "personas": DEMO_PERSONAS
    }


@router.post("/login", response_model=SessionResponse)
async def login(req: LoginRequest):
    """Authenticate via persona ID, username, or email."""
    target_persona = None
    
    if req.role_id:
        target_persona = next((p for p in DEMO_PERSONAS if p["user_id"] == req.role_id), None)
    
    if not target_persona and req.username_or_email:
        query = req.username_or_email.lower().strip()
        target_persona = next(
            (p for p in DEMO_PERSONAS if p["username"].lower() == query or p["email"].lower() == query),
            None
        )

    # Fallback to first persona if none matches for smooth demo capability
    if not target_persona:
        target_persona = {
            "user_id": "CUSTOM-099",
            "username": req.username_or_email.split("@")[0] or "custom_analyst",
            "name": req.username_or_email.split("@")[0].title() if "@" in req.username_or_email else "Custom Operational Analyst",
            "email": req.username_or_email if "@" in req.username_or_email else f"{req.username_or_email}@thermotrace.gov.in",
            "role": "Operational Thermal Analyst",
            "badge": "OA",
            "clearance_level": "Level 2 — Operational",
            "clearance_code": "SEC-CLR-L2-CUSTOM",
            "agency": "Regional GeoAI Surveillance Unit",
            "station": "Web Command Terminal",
            "permissions": ["events:read", "facility:read", "what_if:simulate", "reports:export"],
            "avatar_gradient": "linear-gradient(135deg, #A78BFA 0%, #6D28D9 100%)",
            "is_active": True,
            "last_login": datetime.utcnow().isoformat() + "Z"
        }

    # Record audit log
    AUDIT_LOGS.insert(0, {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": target_persona["user_id"],
        "actor": target_persona["name"],
        "action": "AUTH_LOGIN_SUCCESS",
        "ip": "Client Remote Browser Terminal",
        "status": "AUTHORIZED",
        "details": "Authenticated via ThermoTrace GeoAI Session Gateway"
    })

    return SessionResponse(
        token=f"tt_token_{target_persona['user_id']}_{int(datetime.utcnow().timestamp())}",
        user=target_persona,
        session_expires_at="2026-09-07T00:00:00Z",
        authorized_permissions=target_persona["permissions"]
    )


@router.get("/audit-logs")
async def get_audit_logs():
    """Retrieve recent security & clearance audit trail logs."""
    return {
        "total": len(AUDIT_LOGS),
        "logs": AUDIT_LOGS[:20]
    }


@router.get("/me")
async def current_user(token: Optional[str] = None):
    """Verify active token and return current analyst profile."""
    # Defaults to Dr. Mehta for seamless demonstration
    return DEMO_PERSONAS[0]
