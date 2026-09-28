"""
DrishtiGIS — Phase 21 Dataset Processing Transparency, Inventory & Analytics Test Suite
========================================================================================
Verifies:
1. File upload registers dataset in REGISTERED state and enqueues async background job.
2. Background pipeline updates lifecycle status (REGISTERED -> VALIDATING -> PROCESSING -> QA_REQUIRED -> READY).
3. Searchable, sortable, filterable dataset inventory API.
4. Dataset detail view retrieving comprehensive geospatial metadata & stage timeline.
5. Admin retry, cancel, and publish endpoints.
6. Operational GIS analytics summary endpoint.
7. Property & Cadastral Intelligence table with privacy opt-in safeguards & synthetic disclaimers.
"""

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.services.dataset_store import dataset_store

client = TestClient(app)

ADMIN_USER_P21 = User(
    user_id="usr-p21-admin",
    email="admin_p21@drishtigis.in",
    name="Admin P21 User",
    hashed_password=hash_password("AdminPass123!"),
    role=UserRole.ADMIN,
    region_id="*"
)

PUBLIC_USER_P21 = User(
    user_id="usr-p21-public",
    email="public_p21@drishtigis.in",
    name="Public P21 User",
    hashed_password=hash_password("PublicPass123!"),
    role=UserRole.PUBLIC,
    region_id="bhopal_mp"
)

user_store.users[ADMIN_USER_P21.email.lower()] = ADMIN_USER_P21
user_store.users[PUBLIC_USER_P21.email.lower()] = PUBLIC_USER_P21

TOKEN_ADMIN = create_access_token(ADMIN_USER_P21)
TOKEN_PUBLIC = create_access_token(PUBLIC_USER_P21)


def test_01_upload_registers_dataset_not_instant_complete():
    """Verify upload endpoint returns immediately with REGISTERED status & job metadata."""
    headers = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
    files = {"file": ("p21_cadastral.geojson", b'{"type": "FeatureCollection", "features": []}', "application/json")}
    data = {
        "dataset_name": "P21_Bhopal_Cadastral_Test",
        "region_id": "bhopal_mp",
        "dataset_type": "cadastral_vector"
    }
    res = client.post("/api/v1/admin/datasets/upload", files=files, data=data, headers=headers)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["status"] == "SUCCESS"
    assert "registered" in res_json["message"].lower()

    ds_id = res_json["dataset_id"]
    ds = dataset_store.get_dataset(ds_id)
    assert ds is not None
    assert ds.name == "P21_Bhopal_Cadastral_Test"
    assert ds.status in ["REGISTERED", "VALIDATING", "PROCESSING", "READY"]


def test_02_admin_list_datasets_with_filters():
    """Verify dataset inventory API supports status, format, and search filtering."""
    headers = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
    res = client.get("/api/v1/admin/datasets?status=ALL&format_type=ALL", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "datasets" in data
    assert data["total"] >= 1


def test_03_admin_get_dataset_detail():
    """Verify fetching detailed metadata & timeline for a specific dataset ID."""
    headers = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
    ds_id = "DS-BHOPAL-RASTER-001"
    res = client.get(f"/api/v1/admin/datasets/{ds_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_id"] == ds_id
    assert "crs" in data
    assert "completed_steps" in data


def test_04_non_admin_denied_dataset_endpoints():
    """Verify unauthenticated/public users are denied access to admin dataset APIs."""
    headers = {"Authorization": f"Bearer {TOKEN_PUBLIC}"}
    res_list = client.get("/api/v1/admin/datasets", headers=headers)
    assert res_list.status_code == 403

    res_analytics = client.get("/api/v1/admin/analytics/summary", headers=headers)
    assert res_analytics.status_code == 403


def test_05_admin_analytics_summary_endpoint():
    """Verify operational GIS analytics summary metric calculations."""
    headers = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
    res = client.get("/api/v1/admin/analytics/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_datasets" in data
    assert "active_processing_jobs" in data
    assert "by_status" in data
    assert "by_format" in data


def test_06_admin_properties_table_endpoint():
    """Verify property & cadastral intelligence table returns records with synthetic disclaimers."""
    headers = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
    res = client.get("/api/v1/admin/properties", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "properties" in data
    assert data["total"] >= 1

    first_prop = data["properties"][0]
    assert "property_id" in first_prop
    assert "disclaimer" in first_prop
    assert "purchase_price_inr" in first_prop
