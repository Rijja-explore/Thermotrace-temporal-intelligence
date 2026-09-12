"""
ThermoTrace Single-User Analyst Intelligence Platform Verification Suite.
Validates:
- Analyst Authentication (analyst / analyst) -> thermotrace.india@gmail.com
- Unified Access across all intelligence endpoints
- Event Verification & SOP Mitigation Flow
- PDF Generation and Dispatch to thermotrace.india@gmail.com
"""
import sys
import os
import asyncio

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fastapi import HTTPException
from app.api.auth import USERS_DATABASE, login, LoginRequest, require_role, get_current_authenticated_user
from app.api.events import verify_event, AnalystVerification
from app.api.notifications import dispatch_notification, NotificationDispatchRequest
from app.api.reports import dispatch_report_email, EmailReportRequest

def run_tests():
    print("=" * 70)
    print("THERMOTRACE ANALYST PLATFORM & REPORT DISPATCH TEST SUITE")
    print("=" * 70)

    # 1. VERIFY DEMO CREDENTIALS
    print("\n[1] Verifying Single Analyst Account...")
    analyst_user = USERS_DATABASE.get("analyst")
    assert analyst_user is not None, "Analyst user not found in database"
    assert analyst_user["email"] == "thermotrace.india@gmail.com", f"Expected thermotrace.india@gmail.com, got {analyst_user['email']}"
    assert analyst_user["role"] == "ANALYST"
    print(f"  ✓ ANALYST account verified: role={analyst_user['role']}, email={analyst_user['email']}")

    # 2. TEST AUTHENTICATION & TOKEN ISSUANCE
    print("\n[2] Testing Analyst Login...")
    session = login(LoginRequest(email_or_username="analyst", password="analyst"))
    assert session.role == "ANALYST"
    assert session.user["email"] == "thermotrace.india@gmail.com"
    print(f"  ✓ ANALYST Login Success: Role={session.role}, User={session.user['name']}, Token={session.token[:20]}...")

    # Verify invalid accounts are rejected
    try:
        login(LoginRequest(email_or_username="invalid_user", password="wrong_password"))
        assert False, "Non-analyst invalid credentials should be rejected"
    except HTTPException as e:
        assert e.status_code == 401
        print("  ✓ Non-analyst credentials correctly rejected with HTTP 401")

    # 3. TEST ROLE AUTHORIZATION (All authenticated users have access)
    print("\n[3] Testing Unified Platform Authorization...")
    auth_check = require_role(["ANALYST"])(user=analyst_user)
    assert auth_check["role"] == "ANALYST"
    print("  ✓ ANALYST authorized across platform endpoints")

    # 4. TEST ANALYST EVENT VERIFICATION
    print("\n[4] Testing Analyst Event Verification Flow...")
    verification_req = AnalystVerification(
        decision="CONFIRMED",
        reclassified_label=None,
        notes="Automated SIH Verification Test",
        analyst_id="thermotrace.india@gmail.com"
    )
    
    analyst_res = asyncio.run(verify_event("TT-CASE-001", verification_req, user=analyst_user))
    assert analyst_res["success"] is True
    print("  ✓ ANALYST successfully verified event TT-CASE-001 (200 OK)")

    # 5. TEST REPORT DISPATCH TO THERMOTRACE.INDIA@GMAIL.COM
    print("\n[5] Testing PDF Report Generation & Dispatch...")
    report_req = EmailReportRequest(
        target_email="thermotrace.india@gmail.com",
        notes="SIH Demo Approved Incident Dossier"
    )
    
    report_res = asyncio.run(dispatch_report_email("TT-CASE-001", report_req))
    assert report_res["to"] == "thermotrace.india@gmail.com"
    print(f"  ✓ Report dispatch result: {report_res['message']}")
    print(f"  ✓ Delivery status: {report_res.get('delivery_status')}")

    # 6. TEST NOTIFICATION DISPATCH
    print("\n[6] Testing Notification Dispatch Pipeline...")
    notif_req = NotificationDispatchRequest(
        event_id="TT-CASE-001",
        facility_name="Jamnagar Mega Refinery Complex",
        facility_distance_km=0.18,
        frp_mw=340.0,
        baseline_mw="82 ± 18.5 MW",
        baseline_deviation_sigma=13.95,
        threat_tier="CONFIRMED",
        risk_score=84.0,
        hazard_radius_m=350.0,
        plume_corridor="8.6 km NE",
        population_exposure=123,
        recipient_email="thermotrace.india@gmail.com"
    )
    notif_res = dispatch_notification(notif_req, user=analyst_user)
    assert notif_res["status"] == "SUCCESS"
    assert notif_res["recipient"] == "thermotrace.india@gmail.com"
    print(f"  ✓ Notification dispatched to {notif_res['recipient']} (Status: {notif_res['delivery_status']})")

    print("\n" + "=" * 70)
    print("ALL ANALYST WORKFLOW & REPORT DISPATCH TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
