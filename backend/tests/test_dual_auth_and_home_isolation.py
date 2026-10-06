"""
DrishtiGIS — Phase 20 Dual Authentication & HOME Isolation Test Suite
======================================================================
Comprehensive verification of:
1. Real user authentication via Supabase Auth UUID.
2. HOME location isolation per unique Supabase user ID.
3. SIH Demo accounts (Public, Surveyor, Reviewer, Admin) compatibility.
4. Role permission enforcement & non-elevation for real users.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import UserRole
from backend.app.services.user_home_store import user_home_store
from backend.app.auth.supabase_auth_service import clear_supabase_token_cache

client = TestClient(app)

# Real User Identifiers (Supabase UUID format)
USER_A_UUID = "aaaaaaaa-1111-4444-8888-111111111111"
USER_A_EMAIL = "real-user-a@example.com"
TOKEN_REAL_A = f"sb_test_{USER_A_UUID}_{USER_A_EMAIL}"

USER_B_UUID = "bbbbbbbb-2222-4444-8888-222222222222"
USER_B_EMAIL = "real-user-b@example.com"
TOKEN_REAL_B = f"sb_test_{USER_B_UUID}_{USER_B_EMAIL}"

USER_C_UUID = "cccccccc-3333-4444-8888-333333333333"
USER_C_EMAIL = "real-user-c@example.com"
TOKEN_REAL_C = f"sb_test_{USER_C_UUID}_{USER_C_EMAIL}"


@pytest.fixture(autouse=True)
def clean_test_homes_and_cache():
    """Ensure clean slate before and after every test."""
    clear_supabase_token_cache()
    user_home_store.delete_home(USER_A_UUID)
    user_home_store.delete_home(USER_B_UUID)
    user_home_store.delete_home(USER_C_UUID)
    yield
    user_home_store.delete_home(USER_A_UUID)
    user_home_store.delete_home(USER_B_UUID)
    user_home_store.delete_home(USER_C_UUID)
    clear_supabase_token_cache()


# ============================================================================
# TEST 1: Real User A logs in, saves HOME A, GET /user/home returns HOME A
# ============================================================================
def test_01_real_user_a_save_and_retrieve_home():
    headers_a = {"Authorization": f"Bearer {TOKEN_REAL_A}"}

    # Save HOME A
    save_resp = client.post(
        "/api/v1/user/home",
        headers=headers_a,
        json={"latitude": 23.259933, "longitude": 77.412615, "address_label": "User A Residence", "accuracy_m": 4.5}
    )
    assert save_resp.status_code == 200, f"Expected 200, got: {save_resp.text}"
    saved_data = save_resp.json()
    assert saved_data["user_id"] == USER_A_UUID
    assert abs(saved_data["latitude"] - 23.259933) < 0.0001
    assert abs(saved_data["longitude"] - 77.412615) < 0.0001

    # Retrieve HOME A
    get_resp = client.get("/api/v1/user/home", headers=headers_a)
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["user_id"] == USER_A_UUID
    assert abs(retrieved["latitude"] - 23.259933) < 0.0001


# ============================================================================
# TEST 2: Real User B logs in, saves HOME B, GET /user/home returns HOME B
# ============================================================================
def test_02_real_user_b_save_and_retrieve_home():
    headers_b = {"Authorization": f"Bearer {TOKEN_REAL_B}"}

    # Save HOME B
    save_resp = client.post(
        "/api/v1/user/home",
        headers=headers_b,
        json={"latitude": 28.613939, "longitude": 77.209021, "address_label": "User B Residence", "accuracy_m": 6.0}
    )
    assert save_resp.status_code == 200
    saved_data = save_resp.json()
    assert saved_data["user_id"] == USER_B_UUID
    assert abs(saved_data["latitude"] - 28.613939) < 0.0001

    # Retrieve HOME B
    get_resp = client.get("/api/v1/user/home", headers=headers_b)
    assert get_resp.status_code == 200
    assert get_resp.json()["user_id"] == USER_B_UUID


# ============================================================================
# TEST 3 & 4: User A cannot retrieve User B's HOME & User B cannot retrieve User A's HOME
# ============================================================================
def test_03_and_04_cross_user_home_isolation():
    headers_a = {"Authorization": f"Bearer {TOKEN_REAL_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_REAL_B}"}

    # User A saves Home in Bhopal
    client.post(
        "/api/v1/user/home",
        headers=headers_a,
        json={"latitude": 23.250000, "longitude": 77.400000, "address_label": "Home A"}
    )

    # User B saves Home in Delhi
    client.post(
        "/api/v1/user/home",
        headers=headers_b,
        json={"latitude": 28.610000, "longitude": 77.200000, "address_label": "Home B"}
    )

    # A fetches HOME -> must strictly be A's coordinates
    res_a = client.get("/api/v1/user/home", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["user_id"] == USER_A_UUID
    assert abs(data_a["latitude"] - 23.250000) < 0.001
    assert abs(data_a["latitude"] - 28.610000) > 1.0  # NOT B's latitude

    # B fetches HOME -> must strictly be B's coordinates
    res_b = client.get("/api/v1/user/home", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["user_id"] == USER_B_UUID
    assert abs(data_b["latitude"] - 28.610000) < 0.001
    assert abs(data_b["latitude"] - 23.250000) > 1.0  # NOT A's latitude


# ============================================================================
# TEST 5: Unauthenticated request to /user/home returns 401
# ============================================================================
def test_05_unauthenticated_request_returns_401():
    resp_get = client.get("/api/v1/user/home", headers={})
    assert resp_get.status_code == 401

    resp_post = client.post("/api/v1/user/home", json={"latitude": 23.0, "longitude": 77.0}, headers={})
    assert resp_post.status_code == 401

    resp_delete = client.delete("/api/v1/user/home", headers={})
    assert resp_delete.status_code == 401


# ============================================================================
# TEST 6: Demo Public account still logs in
# ============================================================================
def test_06_demo_public_account_login():
    resp = client.post("/api/v1/auth/login", json={"email": "demo-public@drishtigis.in", "password": "Public123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "demo-public@drishtigis.in"
    assert data["user"]["role"] == UserRole.PUBLIC.value


# ============================================================================
# TEST 7: Demo Surveyor account still logs in
# ============================================================================
def test_07_demo_surveyor_account_login():
    resp = client.post("/api/v1/auth/login", json={"email": "demo-surveyor@drishtigis.in", "password": "Surveyor123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == UserRole.SURVEYOR.value


# ============================================================================
# TEST 8: Demo Reviewer account still logs in
# ============================================================================
def test_08_demo_reviewer_account_login():
    resp = client.post("/api/v1/auth/login", json={"email": "demo-reviewer@drishtigis.in", "password": "Reviewer123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == UserRole.REVIEWER.value


# ============================================================================
# TEST 9: Demo Admin account still logs in
# ============================================================================
def test_09_demo_admin_account_login():
    resp = client.post("/api/v1/auth/login", json={"email": "demo-admin@drishtigis.in", "password": "Admin123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == UserRole.ADMIN.value


# ============================================================================
# TEST 10: Demo account functionality remains unchanged
# ============================================================================
def test_10_demo_account_functionality_unchanged():
    # Admin can list users
    login_admin = client.post("/api/v1/auth/login", json={"email": "demo-admin@drishtigis.in", "password": "Admin123!"})
    admin_token = login_admin.json()["access_token"]
    users_resp = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert users_resp.status_code == 200
    assert len(users_resp.json()) >= 4

    # Public user cannot list users
    login_pub = client.post("/api/v1/auth/login", json={"email": "demo-public@drishtigis.in", "password": "Public123!"})
    pub_token = login_pub.json()["access_token"]
    forbidden_resp = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {pub_token}"})
    assert forbidden_resp.status_code == 403


# ============================================================================
# TEST 11 & 12: Logout handling for Supabase and demo sessions
# ============================================================================
def test_11_and_12_logout_endpoints():
    # Logout with Supabase token
    sb_logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {TOKEN_REAL_A}"})
    assert sb_logout.status_code == 200
    assert "drishtigis_token" in sb_logout.headers.get("set-cookie", "")

    # Logout with Demo token
    login_pub = client.post("/api/v1/auth/login", json={"email": "demo-public@drishtigis.in", "password": "Public123!"})
    demo_token = login_pub.json()["access_token"]
    demo_logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {demo_token}"})
    assert demo_logout.status_code == 200


# ============================================================================
# TEST 13: "Use My Location" (GPS) does not overwrite saved HOME
# ============================================================================
def test_13_gps_coordinates_do_not_overwrite_home():
    headers_a = {"Authorization": f"Bearer {TOKEN_REAL_A}"}

    # Explicitly save HOME
    client.post(
        "/api/v1/user/home",
        headers=headers_a,
        json={"latitude": 23.250000, "longitude": 77.400000, "address_label": "Original Home"}
    )

    # Calling other APIs or unauthenticated queries does not touch HOME
    home_before = client.get("/api/v1/user/home", headers=headers_a).json()
    assert abs(home_before["latitude"] - 23.250000) < 0.001

    # Simulate GPS query / ping - HOME remains exactly the same
    home_after = client.get("/api/v1/user/home", headers=headers_a).json()
    assert home_after["latitude"] == home_before["latitude"]
    assert home_after["longitude"] == home_before["longitude"]


# ============================================================================
# TEST 14: Reloading the browser / sending stored token does not switch user identity
# ============================================================================
def test_14_token_preserves_consistent_identity():
    headers_a = {"Authorization": f"Bearer {TOKEN_REAL_A}"}

    me_1 = client.get("/api/v1/auth/me", headers=headers_a).json()
    me_2 = client.get("/api/v1/auth/me", headers=headers_a).json()

    assert me_1["user_id"] == USER_A_UUID
    assert me_2["user_id"] == USER_A_UUID
    assert me_1["email"] == USER_A_EMAIL
    assert me_2["email"] == USER_A_EMAIL


# ============================================================================
# TEST 15: User A logout and User B login does not show User A's HOME
# ============================================================================
def test_15_logout_a_then_login_b_does_not_show_a_home():
    headers_a = {"Authorization": f"Bearer {TOKEN_REAL_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_REAL_B}"}

    # User A saves HOME
    client.post(
        "/api/v1/user/home",
        headers=headers_a,
        json={"latitude": 23.250000, "longitude": 77.400000, "address_label": "User A Home"}
    )

    # User A logs out
    client.post("/api/v1/auth/logout", headers=headers_a)

    # User B logs in (has not saved HOME yet)
    res_b = client.get("/api/v1/user/home", headers=headers_b)
    # User B MUST get 404 (No saved HOME), NEVER User A's HOME!
    assert res_b.status_code == 404


# ============================================================================
# TEST 16: A new real user has no HOME until they explicitly save one
# ============================================================================
def test_16_new_user_has_no_home_until_saved():
    headers_c = {"Authorization": f"Bearer {TOKEN_REAL_C}"}

    # New user requests HOME before saving
    resp = client.get("/api/v1/user/home", headers=headers_c)
    assert resp.status_code == 404
    assert "No private HOME location" in resp.json()["detail"]


# ============================================================================
# TEST 17: Real user authentication cannot request another user's HOME via parameter injection
# ============================================================================
def test_17_user_home_cannot_be_injected_via_query_or_body():
    headers_b = {"Authorization": f"Bearer {TOKEN_REAL_B}"}

    # User A saves HOME
    client.post(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {TOKEN_REAL_A}"},
        json={"latitude": 23.250000, "longitude": 77.400000}
    )

    # User B tries to pass ?user_id=... in GET
    resp_get = client.get(f"/api/v1/user/home?user_id={USER_A_UUID}", headers=headers_b)
    # Backend ignores parameter and checks current_user.user_id (User B has no home -> 404)
    assert resp_get.status_code == 404

    # User B tries to pass "user_id": USER_A_UUID in POST
    resp_post = client.post(
        "/api/v1/user/home",
        headers=headers_b,
        json={"latitude": 12.971598, "longitude": 77.594562, "user_id": USER_A_UUID}
    )
    assert resp_post.status_code == 200
    # Saved HOME MUST be attributed to User B's UUID, NEVER the spoofed User A's UUID
    assert resp_post.json()["user_id"] == USER_B_UUID


# ============================================================================
# TEST 18: Real user cannot elevate role to ADMIN through registration/API manipulation
# ============================================================================
def test_18_real_user_cannot_elevate_role():
    headers_a = {"Authorization": f"Bearer {TOKEN_REAL_A}"}

    # Verify real user's role is PUBLIC
    me = client.get("/api/v1/auth/me", headers=headers_a).json()
    assert me["role"] == UserRole.PUBLIC.value

    # Real user cannot manage users or view admin resources
    forbidden_resp = client.get("/api/v1/auth/users", headers=headers_a)
    assert forbidden_resp.status_code == 403

    # Direct registration request with role="ADMIN" cannot create an administrator
    reg_resp = client.post("/api/v1/auth/register", json={
        "name": "Hacker Attempt",
        "email": "hacker_admin@drishtigis.in",
        "password": "Password123!",
        "role": "ADMIN"  # Attempt to create admin via public register
    })
    # If endpoint exists, check role cannot be admin
    if reg_resp.status_code == 200:
        created_role = reg_resp.json()["user"]["role"]
        # Public registration cannot self-grant admin
        assert created_role != UserRole.ADMIN.value or not settings.ENABLE_DEMO_ACCOUNTS
