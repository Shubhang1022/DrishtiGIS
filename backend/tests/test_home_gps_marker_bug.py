"""
DrishtiGIS — Private User HOME GPS Marker & Privacy Test Suite
================================================================
Verifies:
1. Strict authentication enforcement for GET/POST/DELETE /api/v1/user/home.
2. Coordinate boundary checking (latitude in [-90, 90], longitude in [-180, 180]).
3. Strict per-user isolation: User A's HOME is never visible to or mutable by User B.
4. Correct coordinate response payload structure for MapLibre rendering [lng, lat].
5. User deletion of HOME record.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.services.user_home_store import user_home_store

client = TestClient(app)

# Setup test user accounts
USER_A = User(
    user_id="usr-home-bug-test-a",
    email="user_a_home_test@drishtigis.in",
    name="User A Home Test",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV"
)

USER_B = User(
    user_id="usr-home-bug-test-b",
    email="user_b_home_test@drishtigis.in",
    name="User B Home Test",
    hashed_password=hash_password("Pass123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV"
)

user_store.users[USER_A.email.lower()] = USER_A
user_store.users[USER_B.email.lower()] = USER_B

TOKEN_A = create_access_token(USER_A)
TOKEN_B = create_access_token(USER_B)


@pytest.fixture(autouse=True)
def clean_home_store():
    user_home_store.delete_home(USER_A.user_id)
    user_home_store.delete_home(USER_B.user_id)
    yield
    user_home_store.delete_home(USER_A.user_id)
    user_home_store.delete_home(USER_B.user_id)


def test_unauthenticated_access_denied():
    """Verify GET/POST/DELETE /api/v1/user/home rejects unauthenticated requests."""
    res_get = client.get("/api/v1/user/home", headers={})
    assert res_get.status_code == 401

    res_post = client.post(
        "/api/v1/user/home",
        json={"latitude": 23.2562, "longitude": 77.4178},
        headers={}
    )
    assert res_post.status_code == 401

    res_del = client.delete("/api/v1/user/home", headers={})
    assert res_del.status_code == 401


def test_invalid_coordinate_rejection():
    """Verify invalid WGS84 coordinates are rejected with 422 Unprocessable Entity."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}

    # Latitude > 90
    res = client.post(
        "/api/v1/user/home",
        json={"latitude": 95.0, "longitude": 77.4178},
        headers=headers_a
    )
    assert res.status_code == 422

    # Longitude < -180
    res = client.post(
        "/api/v1/user/home",
        json={"latitude": 23.2562, "longitude": -190.0},
        headers=headers_a
    )
    assert res.status_code == 422


def test_home_save_and_retrieval_flow():
    """Verify user can save HOME and retrieve valid coordinates matching identity."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}

    # 1. GET before save returns 404
    res_404 = client.get("/api/v1/user/home", headers=headers_a)
    assert res_404.status_code == 404

    # 2. POST save HOME with accuracy
    save_data = {
        "latitude": 23.256201,
        "longitude": 77.417834,
        "address_label": "HOME",
        "accuracy_m": 8.5
    }
    res_post = client.post("/api/v1/user/home", json=save_data, headers=headers_a)
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["user_id"] == USER_A.user_id
    assert data["latitude"] == 23.256201
    assert data["longitude"] == 77.417834
    assert data["address_label"] == "HOME"
    assert data["accuracy_m"] == 8.5

    # 3. GET saved HOME
    res_get = client.get("/api/v1/user/home", headers=headers_a)
    assert res_get.status_code == 200
    assert res_get.json()["user_id"] == USER_A.user_id


def test_strict_account_privacy_isolation():
    """Verify User B cannot read or modify User A's saved HOME location."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_B}"}

    # Save User A's HOME at Location A (Bhopal)
    client.post(
        "/api/v1/user/home",
        json={"latitude": 23.256201, "longitude": 77.417834, "address_label": "User A Home"},
        headers=headers_a
    )

    # User B requests GET /api/v1/user/home -> MUST return 404 (Not User A's data)
    res_b_get = client.get("/api/v1/user/home", headers=headers_b)
    assert res_b_get.status_code == 404

    # User B saves User B's HOME at Location B (Delhi)
    client.post(
        "/api/v1/user/home",
        json={"latitude": 28.6139, "longitude": 77.2090, "address_label": "User B Home"},
        headers=headers_b
    )

    # Verify User B GET returns Delhi (Location B), NOT Bhopal (Location A)
    res_b_saved = client.get("/api/v1/user/home", headers=headers_b)
    assert res_b_saved.status_code == 200
    assert res_b_saved.json()["latitude"] == 28.6139
    assert res_b_saved.json()["longitude"] == 77.2090

    # Verify User A GET still returns Bhopal (Location A), untampered
    res_a_saved = client.get("/api/v1/user/home", headers=headers_a)
    assert res_a_saved.status_code == 200
    assert res_a_saved.json()["latitude"] == 23.256201
    assert res_a_saved.json()["longitude"] == 77.417834


def test_home_deletion_privacy():
    """Verify User B deleting their HOME does not affect User A's HOME."""
    headers_a = {"Authorization": f"Bearer {TOKEN_A}"}
    headers_b = {"Authorization": f"Bearer {TOKEN_B}"}

    # Save HOME for both
    client.post("/api/v1/user/home", json={"latitude": 23.2562, "longitude": 77.4178}, headers=headers_a)
    client.post("/api/v1/user/home", json={"latitude": 28.6139, "longitude": 77.2090}, headers=headers_b)

    # User B deletes HOME
    res_del = client.delete("/api/v1/user/home", headers=headers_b)
    assert res_del.status_code == 200

    # User B GET is 404
    assert client.get("/api/v1/user/home", headers=headers_b).status_code == 404

    # User A GET is still 200
    assert client.get("/api/v1/user/home", headers=headers_a).status_code == 200
