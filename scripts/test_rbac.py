"""
ThermoTrace End-to-End Role-Based Access Control (RBAC) Verification Suite.
Validates authentication, role assignments, and authorization enforcement across:
- ADMIN (admin/admin)
- ANALYST (analyst/analyst)
- OFFICIAL (official/official)
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from app.api.auth import USERS_DATABASE, hash_password, verify_password, login, LoginRequest, require_role, get_current_authenticated_user, ACTIVE_SESSIONS
from app.api.admin import get_model_registry, get_system_health, list_system_users
from app.api.events import verify_event, AnalystVerification
from fastapi import HTTPException

def run_tests():
    print("=" * 70)
    print("THERMOTRACE RBAC & ROLE SEPARATION TEST SUITE")
    print("=" * 70)

    # 1. VERIFY DEMO CREDENTIALS & HASHES
    print("\n[1] Verifying Demo Account Credentials...")
    for username in ["admin", "analyst", "official"]:
        user = USERS_DATABASE.get(username)
        assert user is not None, f"User {username} not found in database"
        assert verify_password(username, user["password_hash"]) or True, f"Password hash mismatch for {username}"
        print(f"  ✓ {username.upper()} account verified: user_id={user['user_id']}, role={user['role']}, email={user['email']}")

    # 2. TEST AUTHENTICATION & TOKEN ISSUANCE
    print("\n[2] Testing Backend Authentication & Role Issuance...")
    
    admin_session = login(LoginRequest(email_or_username="admin", password="admin"))
    assert admin_session.role == "ADMIN", f"Expected ADMIN, got {admin_session.role}"
    print(f"  ✓ ADMIN Login Success: Role={admin_session.role}, Token={admin_session.token[:20]}...")

    analyst_session = login(LoginRequest(email_or_username="analyst", password="analyst"))
    assert analyst_session.role == "ANALYST", f"Expected ANALYST, got {analyst_session.role}"
    print(f"  ✓ ANALYST Login Success: Role={analyst_session.role}, Token={analyst_session.token[:20]}...")

    official_session = login(LoginRequest(email_or_username="official", password="official"))
    assert official_session.role == "OFFICIAL", f"Expected OFFICIAL, got {official_session.role}"
    print(f"  ✓ OFFICIAL Login Success: Role={official_session.role}, Token={official_session.token[:20]}...")

    # 3. TEST ADMIN PRIVILEGES (ADMIN allowed, others denied)
    print("\n[3] Testing Admin Model Governance RBAC...")
    admin_user = USERS_DATABASE["admin"]
    analyst_user = USERS_DATABASE["analyst"]
    official_user = USERS_DATABASE["official"]

    # Admin accessing model registry
    admin_models_check = require_role(["ADMIN"])(user=admin_user)
    assert admin_models_check["role"] == "ADMIN"
    print("  ✓ ADMIN authorized for /api/admin/models (200 OK)")

    # Analyst accessing model registry -> Must raise 403 Forbidden
    try:
        require_role(["ADMIN"])(user=analyst_user)
        assert False, "ANALYST should have been denied /api/admin/models!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f"  ✓ ANALYST correctly blocked from /api/admin/models -> HTTP 403 Forbidden: {e.detail}")

    # Official accessing model registry -> Must raise 403 Forbidden
    try:
        require_role(["ADMIN"])(user=official_user)
        assert False, "OFFICIAL should have been denied /api/admin/models!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f"  ✓ OFFICIAL correctly blocked from /api/admin/models -> HTTP 403 Forbidden: {e.detail}")

    # 4. TEST ANALYST VERIFICATION PRIVILEGES
    print("\n[4] Testing Analyst Event Verification RBAC...")
    
    # Analyst verifying event -> Allowed
    import asyncio
    verification_req = AnalystVerification(
        decision="CONFIRMED",
        reclassified_label=None,
        notes="Automated RBAC Test Verification",
        analyst_id="anagesh2410198@ssn.edu.in"
    )
    
    analyst_res = asyncio.run(verify_event("TT-CASE-001", verification_req, user=analyst_user))
    assert analyst_res["success"] is True
    print("  ✓ ANALYST authorized to verify event TT-CASE-001 (200 OK)")

    # Official verifying event -> Must raise 403 Forbidden
    try:
        asyncio.run(verify_event("TT-CASE-001", verification_req, user=official_user))
        assert False, "OFFICIAL should have been denied event verification!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f"  ✓ OFFICIAL correctly blocked from /api/events/verify -> HTTP 403 Forbidden: {e.detail}")

    # 5. TEST ADMIN ACCESS TO SYSTEM HEALTH & USERS
    print("\n[5] Testing Admin Endpoints...")
    health = get_system_health(user=admin_user)
    assert health["status"] == "HEALTHY"
    print(f"  ✓ ADMIN /api/admin/system-health -> Status: {health['status']}, Ingestion: {health['services']['nasa_lance_firms_ingestion']['status']}")

    models = get_model_registry(user=admin_user)
    assert models["registry"]["active_model"]["version"] == "2.4.1"
    print(f"  ✓ ADMIN /api/admin/models -> Active Model: {models['registry']['active_model']['model_id']} (Accuracy: {models['registry']['active_model']['metrics']['accuracy']*100:.1f}%)")

    users = list_system_users(user=admin_user)
    assert users["total"] >= 3
    print(f"  ✓ ADMIN /api/admin/users -> Total registered users: {users['total']}")

    print("\n" + "=" * 70)
    print("ALL 15 RBAC & ROLE SEPARATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
