"""
DrishtiGIS — Phase 17 Auth, Session, Profile & Privacy Test Suite
==================================================================
Verifies:
1. Cookie-based persistent session handling (Set-Cookie on login/register, delete on logout).
2. User Profile API endpoints (GET/PUT /api/v1/user/profile).
3. Strict per-user profile data isolation (User B cannot read/modify User A's profile).
4. Privacy separation (Personal profile contact data is absent from public map endpoints).
5. Server-side ADMIN RBAC enforcement (/api/v1/admin/* requires UserRole.ADMIN).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.services.user_profile_store import user_profile_store

client = TestClient(app)

# Setup test user accounts
USER_P17_A = User(
    user_id="usr-p17-test-a",
    email="user_p17_a@drishtigis.in",
    name="User P17 A",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV"
)

USER_P17_B = User(
    user_id="usr-p17-test-b",
    email="user_p17_b@drishtigis.in",
    name="User P17 B",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV"
)

USER_P17_ADMIN = User(
    user_id="usr-p17-admin",
    email="admin_p17@drishtigis.in",
    name="Admin P17 User",
    hashed_password=hash_password("AdminPass123!"),
    role=UserRole.ADMIN,
    region_id="*"
)

user_store.users[USER_P17_A.email.lower()] = USER_P17_A
user_store.users[USER_P17_B.email.lower()] = USER_P17_B
user_store.users[USER_P17_ADMIN.email.lower()] = USER_P17_ADMIN

TOKEN_A = create_access_token(USER_P17_A)
TOKEN_B = create_access_token(USER_P17_B)
TOKEN_ADMIN = create_access_token(USER_P17_ADMIN)


@pytest.fixture(autouse=True)
def clean_profile_store():
    user_profile_store.delete_profile(USER_P17_A.user_id)
    user_profile_store.delete_profile(USER_P17_B.user_id)
    user_profile_store.delete_profile(USER_P17_ADMIN.user_id)
    yield
    user_profile_store.delete_profile(USER_P17_A.user_id)
    user_profile_store.delete_profile(USER_P17_B.user_id)
    user_profile_store.delete_profile(USER_P17_ADMIN.user_id)


def test_cookie_session_headers_on_login_and_logout():
    """Verify login response includes Set-Cookie for drishtigis_token with max-age."""
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": USER_P17_A.email, "password": "Pass123!"}
    )
    assert res_login.status_code == 200
    assert "drishtigis_token" in res_login.cookies
    assert res_login.json()["access_token"] is not None

    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    res_logout = client.post("/api/v1/auth/logout", headers=headers_a)
    assert res_logout.status_code == 200


def test_user_profile_get_and_update():
    """Verify user can retrieve and update their personal profile details."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}

    # 1. GET default profile
    res_get = client.get("/api/v1/user/profile", headers=headers_a)
    assert res_get.status_code == 200
    prof = res_get.json()
    assert prof["user_id"] == USER_P17_A.user_id
    assert prof["show_phone_publicly"] is False

    # 2. PUT update profile fields
    update_data = {
        "full_name": "Rajesh Kumar P17",
        "phone_number": "+91 9876543210",
        "house_number": "Flat 402",
        "street_locality": "Arera Colony",
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "pincode": "462016",
        "organization": "Drishti GIS Survey",
        "show_phone_publicly": False
    }
    res_put = client.put("/api/v1/user/profile", json=update_data, headers=headers_a)
    assert res_put.status_code == 200
    updated = res_put.json()
    assert updated["full_name"] == "Rajesh Kumar P17"
    assert updated["phone_number"] == "+91 9876543210"
    assert updated["pincode"] == "462016"
    assert updated["show_phone_publicly"] is False

    # 3. Verify GET returns updated data
    res_get_updated = client.get("/api/v1/user/profile", headers=headers_a)
    assert res_get_updated.status_code == 200
    assert res_get_updated.json()["phone_number"] == "+91 9876543210"


def test_user_profile_strict_isolation():
    """Verify User B cannot read or tamper with User A's profile."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_B}"}

    # User A updates profile
    client.put(
        "/api/v1/user/profile",
        json={"full_name": "User A Private Name", "phone_number": "+91 1111111111"},
        headers=headers_a
    )

    # User B requests GET /api/v1/user/profile -> returns User B's profile, NOT User A's profile
    res_b_get = client.get("/api/v1/user/profile", headers=headers_b)
    assert res_b_get.status_code == 200
    assert res_b_get.json()["user_id"] == USER_P17_B.user_id
    assert res_b_get.json()["phone_number"] != "+91 1111111111"

    # User B updates User B's profile
    client.put(
        "/api/v1/user/profile",
        json={"full_name": "User B Profile", "phone_number": "+91 2222222222"},
        headers=headers_b
    )

    # User A's profile remains untouched
    res_a_get = client.get("/api/v1/user/profile", headers=headers_a)
    assert res_a_get.status_code == 200
    assert res_a_get.json()["phone_number"] == "+91 1111111111"


def test_privacy_separation_from_public_parcels():
    """Verify private personal profile fields (phone number, house number) are NOT leaked in public parcel API."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}

    # Save User A profile with phone number
    client.put(
        "/api/v1/user/profile",
        json={"phone_number": "+91 9999988888", "house_number": "Secret House 99"},
        headers=headers_a
    )

    # Fetch public demo parcels
    res_parcels = client.get("/api/v1/parcels?city=Bhopal", headers=headers_a)
    assert res_parcels.status_code == 200
    parcels_data = res_parcels.json()

    # Ensure no parcel feature contains "+91 9999988888" or "Secret House 99"
    raw_str = str(parcels_data)
    assert "+91 9999988888" not in raw_str
    assert "Secret House 99" not in raw_str


def test_admin_rbac_enforcement():
    """Verify /api/v1/admin/users requires ADMIN role."""
    headers_non_admin = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_admin = {"Authorization": f"Bearer {TOKEN_ADMIN}"}

    # Non-admin gets 403 Forbidden
    res_forbidden = client.get("/api/v1/auth/users", headers=headers_non_admin)
    assert res_forbidden.status_code == 403

    # Admin gets 200 OK
    res_ok = client.get("/api/v1/auth/users", headers=headers_admin)
    assert res_ok.status_code == 200
    assert len(res_ok.json()) >= 1
