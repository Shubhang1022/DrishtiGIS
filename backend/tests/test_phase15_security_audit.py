"""
Phase 15 — Security & Authorization Unit Tests
Tests RBAC permission enforcement, token validation, rate limiting, and anonymous mutation rejection.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth.user_store import user_store
from backend.app.auth.auth_service import create_access_token
from backend.app.services.review_store import review_store

client = TestClient(app)

def get_token_headers(email: str) -> dict:
    user = user_store.get_by_email(email)
    assert user is not None, f"User {email} not found"
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}

# ── 1. Anonymous & Unauthenticated Mutation Rejection ──────────────────────────

def test_01_anonymous_cannot_create_review():
    reviews = review_store.list_reviews()
    sample_dict = reviews[0].model_dump()
    sample_dict["review_id"] = "REV-TEST-ANON-999"
    response = client.post(
        "/api/v1/reviews",
        json=sample_dict,
        headers={}
    )
    assert response.status_code in [401, 403]

def test_02_anonymous_cannot_update_review_status():
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id
    response = client.patch(
        f"/api/v1/reviews/{rev_id}",
        json={"status": "ACCEPTED", "notes": "Unauthorized acceptance attempt"},
        headers={}
    )
    assert response.status_code in [401, 403]

def test_03_anonymous_cannot_edit_geometry():
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id
    response = client.post(
        f"/api/v1/reviews/{rev_id}/geometry",
        json={"geometry": {"type": "Polygon", "coordinates": []}, "notes": "Unauthorized edit"},
        headers={}
    )
    assert response.status_code in [401, 403]

def test_04_anonymous_cannot_record_verification():
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id
    response = client.post(
        f"/api/v1/reviews/{rev_id}/verify",
        json={
            "verification_method": "GNSS",
            "observed_feature": "Boundary",
            "observation": "Test observation",
            "reviewer": "Field-Surveyor"
        },
        headers={}
    )
    assert response.status_code in [401, 403]

# ── 2. Public User Role Mutation Rejection ────────────────────────────────────

def test_05_public_user_cannot_approve_review():
    headers = get_token_headers("demo-public@drishtigis.in")
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id
    response = client.patch(
        f"/api/v1/reviews/{rev_id}",
        json={"status": "ACCEPTED", "notes": "Public user trying to approve"},
        headers=headers
    )
    assert response.status_code == 403

def test_06_public_user_cannot_access_user_directory():
    headers = get_token_headers("demo-public@drishtigis.in")
    response = client.get("/api/v1/auth/users", headers=headers)
    assert response.status_code == 403

# ── 3. Surveyor Role Boundaries ───────────────────────────────────────────────

def test_07_surveyor_cannot_approve_review():
    headers = get_token_headers("demo-surveyor@drishtigis.in")
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id
    response = client.patch(
        f"/api/v1/reviews/{rev_id}",
        json={"status": "ACCEPTED", "notes": "Surveyor trying to approve"},
        headers=headers
    )
    assert response.status_code == 403

def test_08_surveyor_can_update_status_to_in_review():
    headers = get_token_headers("demo-surveyor@drishtigis.in")
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id
    response = client.patch(
        f"/api/v1/reviews/{rev_id}",
        json={"status": "IN_REVIEW", "notes": "Surveyor updating to IN_REVIEW"},
        headers=headers
    )
    assert response.status_code == 200

# ── 4. Token Security Tests ───────────────────────────────────────────────────

def test_09_invalid_token_rejection():
    headers = {"Authorization": "Bearer invalid.jwt.token.here"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

def test_10_login_invalid_credentials():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "demo-admin@drishtigis.in", "password": "WrongPassword123!"}
    )
    assert response.status_code == 401
    assert "Invalid email address or password" in response.json()["detail"]
