"""
DrishtiGIS — Phase 19 Integration Test Suite
================================================
Automated Pytest suite verifying HOME persistence, user property CRUD, draggable pin coordinates,
and strict multi-account privacy boundaries.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.user_store import user_store
from backend.app.services.user_home_store import user_home_store
from backend.app.services.user_property_store import user_property_store

client = TestClient(app)

@pytest.fixture
def user_a():
    u = User(
        user_id="usr_phase19_test_a",
        email="user_a@drishtigis.in",
        name="User Alpha",
        role=UserRole.SURVEYOR,
        hashed_password=hash_password("Pass123!"),
        is_active=True
    )
    user_store.users[u.user_id] = u
    user_store.users[u.email.lower()] = u
    return u

@pytest.fixture
def user_b():
    u = User(
        user_id="usr_phase19_test_b",
        email="user_b@drishtigis.in",
        name="User Beta",
        role=UserRole.PUBLIC,
        hashed_password=hash_password("Pass123!"),
        is_active=True
    )
    user_store.users[u.user_id] = u
    user_store.users[u.email.lower()] = u
    return u

@pytest.fixture
def token_a(user_a):
    return create_access_token(user_a)

@pytest.fixture
def token_b(user_b):
    return create_access_token(user_b)


def test_home_persistence_across_sessions_and_account_isolation(user_a, user_b, token_a, token_b):
    # 1. Clean previous state
    user_home_store.delete_home(user_a.user_id)
    user_home_store.delete_home(user_b.user_id)

    # 2. Account A saves HOME location
    res_save = client.post(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "latitude": 23.259933,
            "longitude": 77.412613,
            "address_label": "Alpha Residence",
            "accuracy_m": 8.5
        }
    )
    assert res_save.status_code == 200, res_save.text
    saved_home = res_save.json()
    assert saved_home["user_id"] == user_a.user_id
    assert saved_home["latitude"] == 23.259933
    assert saved_home["longitude"] == 77.412613
    assert saved_home["address_label"] == "Alpha Residence"

    # 3. Retrieve HOME for Account A (Session persistence check)
    res_get_a = client.get(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_get_a.status_code == 200
    assert res_get_a.json()["address_label"] == "Alpha Residence"

    # 4. Account Privacy Check: Account B attempts to read HOME
    res_get_b = client.get(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_get_b.status_code == 404, "Account B must NOT see Account A's HOME location"

    # 5. Account A updates HOME coordinates (Move HOME check)
    res_update = client.put(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "latitude": 23.261100,
            "longitude": 77.413200,
            "address_label": "Alpha Moved HOME",
            "accuracy_m": 2.1
        }
    )
    assert res_update.status_code == 200
    assert res_update.json()["latitude"] == 23.261100

    # 6. Delete HOME for Account A
    res_del = client.delete(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_del.status_code == 200

    # 7. Confirm deletion
    res_get_post_del = client.get(
        "/api/v1/user/home",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_get_post_del.status_code == 404


def test_user_properties_crud_and_privacy_isolation(user_a, user_b, token_a, token_b):
    # 1. Create property for Account A (Default: Private)
    res_create = client.post(
        "/api/v1/user/properties",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "Alpha Villa",
            "house_number": "H-102",
            "street_locality": "Arera Colony",
            "city": "Bhopal",
            "state": "Madhya Pradesh",
            "property_type": "house",
            "description": "Private residential property",
            "latitude": 23.250010,
            "longitude": 77.410020,
            "accuracy_m": 3.0,
            "is_user_adjusted": True,
            "is_public": False,
            "show_name_publicly": False,
            "show_address_publicly": False,
            "show_phone_publicly": False,
            "phone_number": "+91 99999 88888"
        }
    )
    assert res_create.status_code == 200, res_create.text
    prop_data = res_create.json()
    prop_id = prop_data["id"]
    assert prop_data["user_id"] == user_a.user_id
    assert prop_data["title"] == "Alpha Villa"

    # 2. Account A lists their properties
    res_list_a = client.get(
        "/api/v1/user/properties",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_list_a.status_code == 200
    props_a = res_list_a.json()
    assert any(p["id"] == prop_id for p in props_a)

    # 3. Account B lists their properties -> must NOT contain Account A's property
    res_list_b = client.get(
        "/api/v1/user/properties",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_list_b.status_code == 200
    props_b = res_list_b.json()
    assert not any(p["id"] == prop_id for p in props_b)

    # 4. Public endpoint while private -> must NOT return property
    res_pub_1 = client.get("/api/v1/user/properties/public")
    assert res_pub_1.status_code == 200
    pub_list_1 = res_pub_1.json()
    assert not any(p["id"] == prop_id for p in pub_list_1)

    # 5. Account A enables public sharing with name opt-in only
    res_upd = client.put(
        f"/api/v1/user/properties/{prop_id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "is_public": True,
            "show_name_publicly": True,
            "show_address_publicly": False,
            "show_phone_publicly": False
        }
    )
    assert res_upd.status_code == 200

    # 6. Public endpoint check -> property present, owner name visible, address and phone redacted
    res_pub_2 = client.get("/api/v1/user/properties/public")
    assert res_pub_2.status_code == 200
    pub_list_2 = res_pub_2.json()
    matched = [p for p in pub_list_2 if p["id"] == prop_id]
    assert len(matched) == 1
    pub_prop = matched[0]
    assert pub_prop["owner_name"] == user_a.name
    assert pub_prop["house_number"] is None, "Address must remain redacted when address opt-in is OFF"
    assert pub_prop["phone_number"] is None, "Phone number must remain redacted when phone opt-in is OFF"

    # 7. Delete property
    res_del_prop = client.delete(
        f"/api/v1/user/properties/{prop_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_del_prop.status_code == 200
