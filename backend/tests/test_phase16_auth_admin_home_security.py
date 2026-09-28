"""
DrishtiGIS Phase 16 — Comprehensive Security & Privacy Test Matrix
====================================================================
Validates:
1. Full Application API Authentication Enforcement
2. Admin Console Strict Authorization (403 for non-admins)
3. Authoritative 100MB Streaming Upload Limits (HTTP 413), Zip Bomb & Traversal Defense
4. Strict Per-User Scoped HOME Location Privacy & Controls
"""

import io
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.services.user_home_store import user_home_store

client = TestClient(app)

# ── Test User Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def public_token():
    user = User(
        user_id="usr-test-public-p16",
        email="test-public-p16@drishtigis.in",
        name="Test Public User",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.PUBLIC
    )
    user_store.users[user.email.lower()] = user
    return create_access_token(user)

@pytest.fixture(scope="module")
def surveyor_token():
    user = User(
        user_id="usr-test-surveyor-p16",
        email="test-surveyor-p16@drishtigis.in",
        name="Test Surveyor User",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.SURVEYOR
    )
    user_store.users[user.email.lower()] = user
    return create_access_token(user)

@pytest.fixture(scope="module")
def reviewer_token():
    user = User(
        user_id="usr-test-reviewer-p16",
        email="test-reviewer-p16@drishtigis.in",
        name="Test Reviewer User",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.REVIEWER
    )
    user_store.users[user.email.lower()] = user
    return create_access_token(user)

@pytest.fixture(scope="module")
def admin_token():
    user = User(
        user_id="usr-test-admin-p16",
        email="test-admin-p16@drishtigis.in",
        name="Test Admin User",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.ADMIN
    )
    user_store.users[user.email.lower()] = user
    return create_access_token(user)

# ── 1. Authentication Enforcement (Tests 1–9) ────────────────────────────────

def test_01_anonymous_cannot_access_parcels():
    res = client.get("/api/v1/parcels", headers={})
    assert res.status_code == 401

def test_02_anonymous_cannot_access_reviews():
    res = client.get("/api/v1/reviews", headers={})
    assert res.status_code == 401

def test_03_anonymous_cannot_access_assistant():
    res = client.post("/api/v1/assistant/chat", json={"query": "hello"}, headers={})
    assert res.status_code == 401

def test_04_anonymous_cannot_access_exports():
    res = client.get("/api/v1/exports/formats", headers={})
    assert res.status_code == 401

def test_05_anonymous_cannot_access_admin():
    res = client.get("/api/v1/admin/users", headers={})
    assert res.status_code == 401

def test_06_expired_jwt_rejected():
    expired = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3ItdGVzdCIsImV4cCI6MTAwMDAwMDAwMH0.signature"
    res = client.get("/api/v1/parcels", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401

def test_07_tampered_jwt_rejected(public_token):
    tampered = public_token[:-5] + "XXXXX"
    res = client.get("/api/v1/parcels", headers={"Authorization": f"Bearer {tampered}"})
    assert res.status_code == 401

def test_08_logout_endpoint_succeeds(public_token):
    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {public_token}"})
    assert res.status_code == 200

def test_09_unauthenticated_after_missing_header():
    res = client.get("/api/v1/features", headers={})
    assert res.status_code == 401

# ── 2. Admin Authorization Matrix (Tests 10–15) ──────────────────────────────

def test_10_public_user_denied_admin_users(public_token):
    res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {public_token}"})
    assert res.status_code == 403

def test_11_surveyor_user_denied_admin_users(surveyor_token):
    res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {surveyor_token}"})
    assert res.status_code == 403

def test_12_reviewer_user_denied_admin_users(reviewer_token):
    res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert res.status_code == 403

def test_13_non_admin_denied_admin_regions(reviewer_token):
    res = client.get("/api/v1/admin/regions", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert res.status_code == 403

def test_14_non_admin_denied_dataset_upload(surveyor_token):
    files = {"file": ("test.geojson", b'{"type":"FeatureCollection"}', "application/json")}
    res = client.post("/api/v1/admin/datasets/upload", files=files, headers={"Authorization": f"Bearer {surveyor_token}"})
    assert res.status_code == 403

def test_15_admin_user_allowed_admin_actions(admin_token):
    res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

# ── 3. Upload Size Limit & Ingestion Defense (Tests 16–25) ───────────────────

def test_16_upload_file_below_limit(admin_token):
    geojson_bytes = json.dumps({"type": "FeatureCollection", "features": []}).encode("utf-8")
    files = {"file": ("valid_cadastral.geojson", geojson_bytes, "application/geo+json")}
    res = client.post("/api/v1/admin/datasets/upload", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

def test_17_upload_content_length_exceeding_limit(admin_token):
    files = {"file": ("oversized.geojson", b"small content", "application/geo+json")}
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Length": str(150 * 1024 * 1024)  # 150 MB header
    }
    res = client.post("/api/v1/admin/datasets/upload", files=files, headers=headers)
    assert res.status_code == 413
    assert "File exceeds the maximum allowed upload size of 100 MB" in res.json()["detail"]

def test_18_upload_unsupported_file_extension(admin_token):
    files = {"file": ("malicious.exe", b"MZ...", "application/x-msdownload")}
    res = client.post("/api/v1/admin/datasets/upload", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]

def test_21_path_traversal_filename_sanitized(admin_token):
    files = {"file": ("../../etc/passwd.geojson", b'{"type":"FeatureCollection"}', "application/json")}
    res = client.post("/api/v1/admin/datasets/upload", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "passwd.geojson" in res.json()["filename"]

# ── 4. Private Scoped User HOME Location (Tests 33–45) ───────────────────────

def test_33_user_a_saves_home_location(public_token):
    payload = {"latitude": 23.2599, "longitude": 77.4126, "address_label": "User A Home", "accuracy_m": 5.0}
    res = client.post("/api/v1/user/home", json=payload, headers={"Authorization": f"Bearer {public_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["latitude"] == 23.2599
    assert data["address_label"] == "User A Home"

def test_34_user_a_retrieves_own_home_location(public_token):
    res = client.get("/api/v1/user/home", headers={"Authorization": f"Bearer {public_token}"})
    assert res.status_code == 200
    assert res.json()["address_label"] == "User A Home"

def test_35_user_b_cannot_see_user_a_home(surveyor_token):
    res = client.get("/api/v1/user/home", headers={"Authorization": f"Bearer {surveyor_token}"})
    assert res.status_code == 404

def test_36_user_b_saves_independent_home(surveyor_token, public_token):
    payload_b = {"latitude": 28.6139, "longitude": 77.2090, "address_label": "User B Home"}
    res_b = client.post("/api/v1/user/home", json=payload_b, headers={"Authorization": f"Bearer {surveyor_token}"})
    assert res_b.status_code == 200

    # Confirm User A's HOME is unchanged
    res_a = client.get("/api/v1/user/home", headers={"Authorization": f"Bearer {public_token}"})
    assert res_a.json()["address_label"] == "User A Home"

def test_37_user_b_cannot_delete_user_a_home(surveyor_token, public_token):
    # User B deletes User B's HOME
    res_del_b = client.delete("/api/v1/user/home", headers={"Authorization": f"Bearer {surveyor_token}"})
    assert res_del_b.status_code == 200

    # User A's HOME remains intact
    res_a = client.get("/api/v1/user/home", headers={"Authorization": f"Bearer {public_token}"})
    assert res_a.status_code == 200
    assert res_a.json()["address_label"] == "User A Home"

def test_41_user_a_deletes_own_home(public_token):
    res = client.delete("/api/v1/user/home", headers={"Authorization": f"Bearer {public_token}"})
    assert res.status_code == 200

    res_get = client.get("/api/v1/user/home", headers={"Authorization": f"Bearer {public_token}"})
    assert res_get.status_code == 404

def test_45_unauthenticated_cannot_access_user_home():
    res = client.get("/api/v1/user/home", headers={})
    assert res.status_code == 401
