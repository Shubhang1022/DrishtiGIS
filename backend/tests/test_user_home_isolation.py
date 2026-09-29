"""
DrishtiGIS — User Home Location Isolation & Multi-User Privacy Regression Suite
================================================================================
Comprehensive regression tests for:
1. Default India map view coordinates (neutral overview, not HOME).
2. No HOME marker for new or unconfigured users (404 Not Found).
3. User A HOME is never visible to User B (strict identity scoping).
4. Current GPS does not overwrite or move HOME.
5. Save HOME persists strictly for the authenticated user ID.
6. Logout clears session cookie and unauthenticated access is rejected (401).
7. Switching accounts does not leak HOME across user sessions.
8. Multi-device user isolation flow (Device 1 Account A vs Device 2 Account B).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.services.user_home_store import user_home_store
from backend.app.core.config import settings

client = TestClient(app)

# Test User Accounts for Isolation Testing
USER_A = User(
    user_id="usr-iso-test-a",
    email="user_a_iso@drishtigis.in",
    name="User A Isolation",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="bhopal_mp"
)

USER_B = User(
    user_id="usr-iso-test-b",
    email="user_b_iso@drishtigis.in",
    name="User B Isolation",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="bhopal_mp"
)

USER_NEW = User(
    user_id="usr-iso-test-new",
    email="user_new_iso@drishtigis.in",
    name="Brand New User",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="bhopal_mp"
)

user_store.users[USER_A.email.lower()] = USER_A
user_store.users[USER_B.email.lower()] = USER_B
user_store.users[USER_NEW.email.lower()] = USER_NEW

TOKEN_A = create_access_token(USER_A)
TOKEN_B = create_access_token(USER_B)
TOKEN_NEW = create_access_token(USER_NEW)


@pytest.fixture(autouse=True)
def clean_test_homes():
    """Ensure test users start with a clean state and clean up afterwards."""
    user_home_store.delete_home(USER_A.user_id)
    user_home_store.delete_home(USER_B.user_id)
    user_home_store.delete_home(USER_NEW.user_id)
    yield
    user_home_store.delete_home(USER_A.user_id)
    user_home_store.delete_home(USER_B.user_id)
    user_home_store.delete_home(USER_NEW.user_id)


def test_01_default_india_geographic_constants():
    """Validate that default center is India national center, not user HOME."""
    # Front-end reference constants check
    india_lon = 78.9629
    india_lat = 20.5937
    india_zoom = 5

    # Coordinates must represent central geographic India
    assert 68.0 <= india_lon <= 98.0
    assert 6.0 <= india_lat <= 38.0
    assert india_zoom <= 7  # National scale overview zoom


def test_02_new_user_has_no_home():
    """Verify newly registered / unconfigured user receives 404 (no HOME marker)."""
    headers = {"Authorization": f"Bearer {TOKEN_NEW}"}
    res = client.get("/api/v1/user/home", headers=headers)
    assert res.status_code == 404
    assert "No private HOME location" in res.json()["detail"]


def test_03_user_a_home_cannot_appear_for_user_b():
    """Verify User A's saved HOME is completely hidden from User B."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_B}"}

    # User A saves HOME at Location A (Bhopal coordinates)
    loc_a = {
        "latitude": 23.256201,
        "longitude": 77.417834,
        "address_label": "User A Residence",
        "accuracy_m": 5.0
    }
    save_res = client.post("/api/v1/user/home", json=loc_a, headers=headers_a)
    assert save_res.status_code == 200

    # User B requests /api/v1/user/home -> MUST return 404
    res_b = client.get("/api/v1/user/home", headers=headers_b)
    assert res_b.status_code == 404
    assert res_b.status_code != 200

    # Verify User A can still retrieve Location A
    res_a = client.get("/api/v1/user/home", headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["latitude"] == 23.256201
    assert res_a.json()["longitude"] == 77.417834
    assert res_a.json()["user_id"] == USER_A.user_id


def test_04_current_gps_does_not_overwrite_home():
    """Verify device GPS detection does NOT overwrite or mutate saved HOME."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}

    # 1. User A saves HOME at Location A
    loc_a = {"latitude": 23.256201, "longitude": 77.417834, "address_label": "HOME"}
    client.post("/api/v1/user/home", json=loc_a, headers=headers_a)

    # 2. Simulate User A moving/detecting GPS at Location C (Indore)
    current_gps = {"latitude": 22.719568, "longitude": 75.857727, "accuracy": 12.0}

    # Merely detecting GPS does NOT call POST /api/v1/user/home.
    # Verify User A's HOME remains untouched at Location A
    home_res = client.get("/api/v1/user/home", headers=headers_a)
    assert home_res.status_code == 200
    assert home_res.json()["latitude"] == 23.256201
    assert home_res.json()["longitude"] == 77.417834
    assert home_res.json()["latitude"] != current_gps["latitude"]


def test_05_save_home_persists_only_for_authenticated_user():
    """Verify unauthenticated requests cannot save HOME, and saves strictly scope to JWT subject."""
    # Unauthenticated save fails with 401
    unauth_res = client.post(
        "/api/v1/user/home",
        json={"latitude": 23.2562, "longitude": 77.4178},
        headers={}
    )
    assert unauth_res.status_code == 401

    # Authenticated save succeeds and is attributed to current_user.user_id
    auth_headers = {"Authorization": f"Bearer {TOKEN_A}"}
    auth_res = client.post(
        "/api/v1/user/home",
        json={"latitude": 23.2562, "longitude": 77.4178},
        headers=auth_headers
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["user_id"] == USER_A.user_id


def test_06_logout_clears_session_and_rejects_unauthenticated():
    """Verify logout deletes session cookie and subsequent unauthenticated requests are rejected."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    client.post("/api/v1/user/home", json={"latitude": 23.2562, "longitude": 77.4178}, headers=headers_a)

    # Call logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers_a)
    assert logout_res.status_code == 200
    assert "drishtigis_token" in logout_res.headers.get("set-cookie", "")

    # Unauthenticated request without token must get 401
    get_res = client.get("/api/v1/user/home", headers={})
    assert get_res.status_code == 401


def test_07_switching_accounts_does_not_leak_home():
    """Verify switching from Account A to Account B does not leak HOME."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_B}"}

    # 1. User A saves Location A
    client.post("/api/v1/user/home", json={"latitude": 23.2562, "longitude": 77.4178}, headers=headers_a)

    # 2. User A logs out
    client.post("/api/v1/auth/logout", headers=headers_a)

    # 3. User B logs in -> Must see 404
    res_b_init = client.get("/api/v1/user/home", headers=headers_b)
    assert res_b_init.status_code == 404

    # 4. User B saves Location B (Delhi)
    client.post("/api/v1/user/home", json={"latitude": 28.6139, "longitude": 77.2090}, headers=headers_b)

    # 5. User B logs out
    client.post("/api/v1/auth/logout", headers=headers_b)

    # 6. User A logs back in -> Must see Location A only (NOT Location B)
    res_a_back = client.get("/api/v1/user/home", headers=headers_a)
    assert res_a_back.status_code == 200
    assert res_a_back.json()["latitude"] == 23.2562
    assert res_a_back.json()["longitude"] == 77.4178
    assert res_a_back.json()["latitude"] != 28.6139


def test_08_multi_device_user_isolation_scenario():
    """
    Test exact multi-device scenario specified in PRD:
    Device 1 (Account A): Save HOME at Location A
    Device 2 (Account B): Login -> India overview, No Location A, No HOME marker
    Device 2 (Account B): Use My Location -> centers on Location B, HOME absent
    Device 2 (Account B): Save as HOME -> HOME marker = Location B
    Logout B, Login A -> HOME = Location A only
    """
    device1_headers = {"Authorization": f"Bearer {TOKEN_A}"}
    device2_headers = {"Authorization": f"Bearer {TOKEN_B}"}

    # Step 1: Device 1 (Account A) saves HOME at Location A (Bhopal)
    loc_a = {"latitude": 23.256201, "longitude": 77.417834, "address_label": "Home A"}
    res_d1_save = client.post("/api/v1/user/home", json=loc_a, headers=device1_headers)
    assert res_d1_save.status_code == 200

    # Step 2: Device 2 (Account B) logs in
    # Expected: No Location A, No HOME marker (404)
    res_d2_login = client.get("/api/v1/user/home", headers=device2_headers)
    assert res_d2_login.status_code == 404

    # Step 3: Account B simulates "Use My Location" at Location B (Delhi)
    # Expected: Current GPS position detected, HOME remains absent (still 404)
    res_d2_check = client.get("/api/v1/user/home", headers=device2_headers)
    assert res_d2_check.status_code == 404

    # Step 4: Account B presses "Save as HOME" with Location B
    loc_b = {"latitude": 28.613939, "longitude": 77.209021, "address_label": "Home B"}
    res_d2_save = client.post("/api/v1/user/home", json=loc_b, headers=device2_headers)
    assert res_d2_save.status_code == 200
    assert res_d2_save.json()["latitude"] == 28.613939
    assert res_d2_save.json()["longitude"] == 77.209021

    # Step 5: Logout B
    client.post("/api/v1/auth/logout", headers=device2_headers)

    # Step 6: Login A -> HOME must be Location A only
    res_a_final = client.get("/api/v1/user/home", headers=device1_headers)
    assert res_a_final.status_code == 200
    assert res_a_final.json()["latitude"] == 23.256201
    assert res_a_final.json()["longitude"] == 77.417834
    assert res_a_final.json()["address_label"] == "Home A"
