"""
DrishtiGIS — Property Ownership, Residents & Property Value Details Security & Data Integrity Tests
========================================================================================================
Validates 20 test points for ownership, resident count logic, currency formatting, vacant plot safeguards,
Pydantic schema validation, and data integrity.
"""

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from backend.app.schemas.parcel import PropertySchema, PropertyType
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store

client = TestClient(app)

@pytest.fixture(scope="module")
def auth_headers():
    user = User(
        user_id="usr-prop-test-user",
        email="prop-test@drishtigis.in",
        name="Property Test User",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.SURVEYOR
    )
    user_store.users[user.email.lower()] = user
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


# ── 1. House Displays Owner & Previous Owner ──────────────────────────────────
def test_01_house_displays_owner_and_previous_owner(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert prop["current_owner_name"] == "Rajesh Kumar"
    assert prop["previous_owner_name"] is not None


# ── 2. House Displays Resident Count ──────────────────────────────────────────
def test_02_house_displays_resident_count(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert prop["property_type"] == "HOUSE"
    assert isinstance(prop["resident_count"], int)
    assert prop["resident_count"] >= 0


# ── 3. Building Displays Resident Count ────────────────────────────────────────
def test_03_building_displays_resident_count(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-002", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert prop["property_type"] == "BUILDING"
    assert isinstance(prop["resident_count"], int)
    assert prop["resident_count"] >= 0


# ── 4. Vacant Plot Hides Resident Count ────────────────────────────────────────
def test_04_vacant_plot_hides_resident_count(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-004", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert prop["property_type"] == "VACANT_PLOT"
    assert prop["resident_count"] is None


# ── 5. Vacant Plot Still Displays Owner & Previous Owner ──────────────────────
def test_05_vacant_plot_displays_owner_and_previous_owner(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-004", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert prop["current_owner_name"] is not None
    assert prop["previous_owner_name"] is not None


# ── 6. Purchase Price Numerical Backend Value ──────────────────────────────────
def test_06_purchase_price_numeric_format(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert isinstance(prop["purchase_price_inr"], (int, float))
    assert prop["purchase_price_inr"] > 0


# ── 7. Estimated Selling Price Shows Current Year ─────────────────────────────
def test_07_estimated_selling_price_current_year(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    prop = data["property"]
    assert isinstance(prop["estimated_selling_price_inr"], (int, float))
    assert prop["valuation_year"] == datetime.now().year


# ── 8. Missing Values Return None/Not Available in Response ────────────────────
def test_08_missing_values_handled_gracefully(auth_headers):
    # Test property schema with missing fields
    p = PropertySchema(current_owner_name=None, previous_owner_name=None)
    assert p.current_owner_name is None
    assert p.previous_owner_name is None


# ── 9. Null Resident Count Does Not Default to Zero ────────────────────────────
def test_09_null_resident_count_is_none():
    p = PropertySchema(property_type=PropertyType.VACANT_PLOT, resident_count=None)
    assert p.resident_count is None
    assert p.resident_count != 0


# ── 10. Synthetic Values Retain Demo Disclaimers ──────────────────────────────
def test_10_synthetic_disclaimer_preserved(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "Synthetic prototype data" in data["_disclaimer"]


# ── 11. No Synthetic Data Marked Official ──────────────────────────────────────
def test_11_no_synthetic_data_marked_official(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["_source"] != "OFFICIAL_REFERENCE"
    assert data["property"]["record_status"] == "SYNTHETIC_DEMO"


# ── 12. PUBLIC Users Cannot Modify Property Records ────────────────────────────
def test_12_public_users_cannot_modify_property_records(auth_headers):
    # Verify no unauthenticated or public POST/PUT endpoints exist for property mutation
    res = client.post("/api/v1/parcels", json={"property_id": "DRS-TEST"}, headers={})
    assert res.status_code in (401, 403, 405)


# ── 13. Invalid Negative Prices Rejected ───────────────────────────────────────
def test_13_invalid_negative_price_rejected():
    with pytest.raises(ValidationError):
        PropertySchema(purchase_price_inr=-500.0)


# ── 14. Invalid Resident Counts Rejected ───────────────────────────────────────
def test_14_invalid_resident_count_rejected():
    with pytest.raises(ValidationError):
        PropertySchema(resident_count=-2)


# ── 15. Unknown Property Types Rejected ────────────────────────────────────────
def test_15_unknown_property_type_rejected():
    with pytest.raises(ValidationError):
        PropertySchema(property_type="INVALID_TYPE")


# ── 16. Existing AI Building Analysis Unchanged ────────────────────────────────
def test_16_ai_building_analysis_intact(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "ai_analysis" in data
    assert data["ai_analysis"]["ai_available"] is True


# ── 17. Existing Review and Discrepancy Panels Unchanged ──────────────────────
def test_17_discrepancies_intact(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "discrepancies" in data


# ── 18. Existing Property IDs & Geometry Unchanged ─────────────────────────────
def test_18_property_ids_and_geometry_intact(auth_headers):
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["parcel"]["properties"]["property_id"] == "DRS-BPL-DEMO-001"
    assert data["parcel"]["geometry"]["type"] == "Polygon"


# ── 19. Existing Authentication Continues to Work ──────────────────────────────
def test_19_auth_enforcement_works():
    res = client.get("/api/v1/parcels/DRS-BPL-DEMO-001", headers={})
    assert res.status_code == 401


# ── 20. Existing HOME Location Privacy Unaaffected ─────────────────────────────
def test_20_home_location_privacy_unaffected(auth_headers):
    res = client.get("/api/v1/user/home", headers=auth_headers)
    assert res.status_code in (200, 404)
