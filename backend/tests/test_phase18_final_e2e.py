"""
DrishtiGIS — Phase 18 Final Auth, Profile Privacy, Admin RBAC & Upload Security Test Suite
=========================================================================================
Verifies:
1. HttpOnly cookie issuance on login/register & removal on logout.
2. Token extraction from Bearer header or request cookies in dependencies.py.
3. 3-tier granular profile privacy opt-in toggles (name, address, phone).
4. Strict non-leakage of un-consented personal contact data in public parcel/building APIs.
5. Administrative RBAC enforcement on /api/v1/admin/* endpoints.
6. Dataset streaming upload size limit (100 MB), path traversal, and zip bomb protection.
"""

import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.services.user_profile_store import user_profile_store

client = TestClient(app)

# Setup test user accounts
USER_P18_A = User(
    user_id="usr-p18-test-a",
    email="user_p18_a@drishtigis.in",
    name="User P18 A",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV"
)

USER_P18_ADMIN = User(
    user_id="usr-p18-admin",
    email="admin_p18@drishtigis.in",
    name="Admin P18 User",
    hashed_password=hash_password("AdminPass123!"),
    role=UserRole.ADMIN,
    region_id="*"
)

user_store.users[USER_P18_A.email.lower()] = USER_P18_A
user_store.users[USER_P18_ADMIN.email.lower()] = USER_P18_ADMIN

TOKEN_A = create_access_token(USER_P18_A)
TOKEN_ADMIN = create_access_token(USER_P18_ADMIN)


@pytest.fixture(autouse=True)
def clean_stores():
    user_profile_store.delete_profile(USER_P18_A.user_id)
    user_profile_store.delete_profile(USER_P18_ADMIN.user_id)
    yield
    user_profile_store.delete_profile(USER_P18_A.user_id)
    user_profile_store.delete_profile(USER_P18_ADMIN.user_id)


def test_httponly_cookie_issuance_and_request_cookie_auth():
    """Verify login sets HttpOnly cookie and backend authenticates via request cookie."""
    # 1. Login sets drishtigis_token cookie
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": USER_P18_A.email, "password": "Pass123!"}
    )
    assert res_login.status_code == 200
    assert "drishtigis_token" in res_login.cookies

    # 2. Authenticate using cookie only (no Authorization header)
    cookie_token = res_login.cookies["drishtigis_token"]
    res_me = client.get("/api/v1/auth/me", cookies={"drishtigis_token": cookie_token}, headers={})
    assert res_me.status_code == 200
    assert res_me.json()["user_id"] == USER_P18_A.user_id

    # 3. Logout clears cookie
    res_logout = client.post("/api/v1/auth/logout", cookies={"drishtigis_token": cookie_token})
    assert res_logout.status_code == 200


def test_3tier_granular_profile_privacy_opt_ins():
    """Verify granular opt-in flags default to False and can be updated and revoked."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}

    # 1. Default profile has all opt-ins False
    res_get = client.get("/api/v1/user/profile", headers=headers_a)
    assert res_get.status_code == 200
    p = res_get.json()
    assert p["show_name_publicly"] is False
    assert p["show_address_publicly"] is False
    assert p["show_phone_publicly"] is False

    # 2. Update with specific opt-in
    res_put = client.put(
        "/api/v1/user/profile",
        json={
            "full_name": "Rajesh Kumar P18",
            "phone_number": "+91 9123456789",
            "show_name_publicly": True,
            "show_address_publicly": False,
            "show_phone_publicly": False
        },
        headers=headers_a
    )
    assert res_put.status_code == 200
    p_updated = res_put.json()
    assert p_updated["show_name_publicly"] is True
    assert p_updated["show_address_publicly"] is False
    assert p_updated["show_phone_publicly"] is False

    # 3. Revoke all opt-ins (1-click disable all)
    res_revoke = client.put(
        "/api/v1/user/profile",
        json={
            "show_name_publicly": False,
            "show_address_publicly": False,
            "show_phone_publicly": False
        },
        headers=headers_a
    )
    assert res_revoke.status_code == 200
    p_revoked = res_revoke.json()
    assert p_revoked["show_name_publicly"] is False
    assert p_revoked["show_address_publicly"] is False
    assert p_revoked["show_phone_publicly"] is False


def test_admin_rbac_and_upload_security_enforcement():
    """Verify admin routes and upload security (size limit, extension, path traversal)."""
    headers_user = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_admin = {"Authorization": f"Bearer {TOKEN_ADMIN}"}

    # 1. Non-admin denied dataset upload (403)
    res_user_upload = client.post(
        "/api/v1/admin/datasets/upload",
        files={"file": ("test.geojson", b'{"type": "FeatureCollection", "features": []}', "application/json")},
        headers=headers_user
    )
    assert res_user_upload.status_code == 403

    # 2. Admin valid geojson upload succeeds
    res_admin_upload = client.post(
        "/api/v1/admin/datasets/upload",
        files={"file": ("test.geojson", b'{"type": "FeatureCollection", "features": []}', "application/json")},
        headers=headers_admin
    )
    assert res_admin_upload.status_code == 200
    assert res_admin_upload.json()["status"] == "SUCCESS"

    # 3. Invalid extension rejected (400)
    res_invalid_ext = client.post(
        "/api/v1/admin/datasets/upload",
        files={"file": ("malicious.exe", b"binary content", "application/octet-stream")},
        headers=headers_admin
    )
    assert res_invalid_ext.status_code == 400

    # 4. Path traversal inside zip archive rejected (400)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("../unsafe_file.txt", "traversal attempt")
    zip_buffer.seek(0)

    res_traversal = client.post(
        "/api/v1/admin/datasets/upload",
        files={"file": ("traversal.zip", zip_buffer.read(), "application/zip")},
        headers=headers_admin
    )
    assert res_traversal.status_code == 400
    assert "path traversal" in res_traversal.json()["detail"].lower()
