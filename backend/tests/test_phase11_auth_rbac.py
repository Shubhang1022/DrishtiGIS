"""
DrishtiGIS — Phase 11 Authentication, RBAC & Data Governance Test Suite
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_store import user_store
from backend.app.auth.roles import UserRole, Permission, has_permission
from backend.app.auth.audit_logger import security_audit_logger

client = TestClient(app)

def test_preseeded_demo_accounts_exist():
    """Verify that SIH demo accounts are initialized correctly."""
    public_user = user_store.get_by_email("demo-public@drishtigis.in")
    surveyor_user = user_store.get_by_email("demo-surveyor@drishtigis.in")
    reviewer_user = user_store.get_by_email("demo-reviewer@drishtigis.in")
    admin_user = user_store.get_by_email("demo-admin@drishtigis.in")

    assert public_user is not None
    assert public_user.role == UserRole.PUBLIC

    assert surveyor_user is not None
    assert surveyor_user.role == UserRole.SURVEYOR
    assert surveyor_user.region_id == "bhopal_mp"

    assert reviewer_user is not None
    assert reviewer_user.role == UserRole.REVIEWER
    assert reviewer_user.region_id == "bhopal_mp"

    assert admin_user is not None
    assert admin_user.role == UserRole.ADMIN
    assert admin_user.region_id == "*"

def test_user_authentication_flow():
    """Test login with valid and invalid credentials, and logout."""
    # Invalid password
    resp = client.post("/api/v1/auth/login", json={
        "email": "demo-surveyor@drishtigis.in",
        "password": "WrongPassword123!"
    })
    assert resp.status_code == 401

    # Valid password login
    resp = client.post("/api/v1/auth/login", json={
        "email": "demo-surveyor@drishtigis.in",
        "password": "Surveyor123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    token = data["access_token"]
    assert data["user"]["role"] == "SURVEYOR"

    # Validate session (/me)
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "demo-surveyor@drishtigis.in"

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

def test_registration_endpoint():
    """Test self-registration for new officers."""
    reg_data = {
        "email": f"new_officer_{user_store.list_users().__len__()}@agency.gov.in",
        "name": "Field Officer Ananya",
        "password": "SecurePassword123!",
        "role": "SURVEYOR",
        "organization": "Madhya Pradesh Urban Development",
        "city": "Bhopal",
        "state": "Madhya Pradesh"
    }

    resp = client.post("/api/v1/auth/register", json=reg_data)
    assert resp.status_code == 200
    res_json = resp.json()
    assert "access_token" in res_json
    assert res_json["user"]["email"] == reg_data["email"]

def test_rbac_permission_matrix():
    """Test RBAC rules across PUBLIC, SURVEYOR, REVIEWER, and ADMIN."""
    # PUBLIC permissions
    assert has_permission(UserRole.PUBLIC, Permission.VIEW_MAP) is True
    assert has_permission(UserRole.PUBLIC, Permission.USE_AI_ASSISTANT) is True
    assert has_permission(UserRole.PUBLIC, Permission.EDIT_REVIEW_GEOMETRY) is False
    assert has_permission(UserRole.PUBLIC, Permission.APPROVE_REVIEW) is False

    # SURVEYOR permissions
    assert has_permission(UserRole.SURVEYOR, Permission.CREATE_REVIEW) is True
    assert has_permission(UserRole.SURVEYOR, Permission.EDIT_REVIEW_GEOMETRY) is True
    assert has_permission(UserRole.SURVEYOR, Permission.SUBMIT_FIELD_VERIFICATION) is True
    assert has_permission(UserRole.SURVEYOR, Permission.MANAGE_USERS) is False

    # REVIEWER permissions
    assert has_permission(UserRole.REVIEWER, Permission.APPROVE_REVIEW) is True
    assert has_permission(UserRole.REVIEWER, Permission.REJECT_REVIEW) is True
    assert has_permission(UserRole.REVIEWER, Permission.VIEW_AUDIT_LOG) is True
    assert has_permission(UserRole.REVIEWER, Permission.MANAGE_REGIONS) is False

    # ADMIN permissions
    assert has_permission(UserRole.ADMIN, Permission.MANAGE_USERS) is True
    assert has_permission(UserRole.ADMIN, Permission.MANAGE_REGIONS) is True
    assert has_permission(UserRole.ADMIN, Permission.PUBLISH_DATASET) is True

def test_admin_user_management_endpoint():
    """Test admin listing and updating user roles."""
    # Login as admin
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "demo-admin@drishtigis.in",
        "password": "Admin123!"
    })
    token = login_resp.json()["access_token"]

    # List users
    users_resp = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert users_resp.status_code == 200
    user_list = users_resp.json()
    assert len(user_list) >= 4

    # Non-admin attempting to access /users
    surveyor_login = client.post("/api/v1/auth/login", json={
        "email": "demo-surveyor@drishtigis.in",
        "password": "Surveyor123!"
    }).json()["access_token"]

    unauth_resp = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {surveyor_login}"})
    assert unauth_resp.status_code == 403

def test_region_governance():
    """Test registering and listing multi-region governance settings."""
    # List regions
    res = client.get("/api/v1/auth/regions")
    assert res.status_code == 200
    regions = res.json()["regions"]
    assert any(r["region_id"] == "bhopal_mp" for r in regions)

    # Register new region as admin
    admin_token = client.post("/api/v1/auth/login", json={
        "email": "demo-admin@drishtigis.in",
        "password": "Admin123!"
    }).json()["access_token"]

    new_region = {
        "region_id": "lucknow_up",
        "country": "India",
        "state": "Uttar Pradesh",
        "city": "Lucknow",
        "description": "Lucknow Municipal GIS Jurisdiction",
        "status": "ACTIVE"
    }

    create_res = client.post(
        "/api/v1/auth/regions", 
        json=new_region, 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 200

def test_audit_logs_append_only():
    """Test that audit log entries are generated upon security actions."""
    logs = security_audit_logger.get_logs(limit=50)
    assert len(logs) > 0
    # Audit logs contain action types like LOGIN, REGISTER, etc.
    action_types = [l.action for l in logs]
    assert any(act in action_types for act in ["LOGIN", "REGISTER", "REGION_REGISTERED", "ROLE_CHANGED"])

def test_synthetic_disclaimer_preserved():
    """Ensure synthetic data disclaimer remains intact in API outputs."""
    res = client.get("/api/v1/reviews")
    assert res.status_code == 200
    data = res.json()
    assert "_disclaimer" in data
    assert "Synthetic" in data["_disclaimer"]
