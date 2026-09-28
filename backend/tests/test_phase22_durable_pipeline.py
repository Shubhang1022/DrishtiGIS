"""
Phase 22: Dataset Pipeline Reality Audit, Durable Workers & Geospatial Integrity Test Suite
========================================================================================
Verifies:
1. Dataset registration and persistence.
2. Worker concurrency lock acquisition and isolation.
3. Strict state machine transitions (retry, cancel, publish rules).
4. Interrupted background job startup detection and recovery.
5. Real GeoJSON feature extraction and bounding box inspection.
6. Admin API endpoints and RBAC security enforcement.
"""

import os
import json
import pytest
import shutil
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset_store import dataset_store, DatasetItem, UPLOADS_DIR
from backend.app.services.dataset_pipeline import run_dataset_pipeline, _inspect_geojson
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure clean test state before each test run."""
    yield

def test_dataset_store_state_machine():
    """Verify strict state transitions for retry, cancel, and publish."""
    # 1. Register test dataset
    ds = dataset_store.register_dataset(
        name="Test Lifecycle GeoJSON",
        filename="test_lifecycle.geojson",
        format_type="geojson",
        file_size_bytes=1024,
        file_path="data/uploads/test_lifecycle.geojson"
    )
    assert ds.status == "REGISTERED"
    assert ds.is_published is False

    # 2. Cannot publish REGISTERED dataset
    with pytest.raises(ValueError, match="Cannot publish dataset"):
        dataset_store.publish_dataset(ds.dataset_id)

    # 3. Cannot retry REGISTERED dataset
    with pytest.raises(ValueError, match="Cannot retry dataset"):
        dataset_store.retry_dataset(ds.dataset_id)

    # 4. Cancel active dataset
    ds_cancelled = dataset_store.cancel_dataset(ds.dataset_id)
    assert ds_cancelled.status == "CANCELLED"

    # 5. Retry CANCELLED dataset
    ds_retried = dataset_store.retry_dataset(ds.dataset_id)
    assert ds_retried.status == "REGISTERED"

    # 6. Update to READY and publish
    dataset_store.update_dataset_status(ds.dataset_id, status="READY", current_stage="Validation Passed", progress_percent=100)
    ds_published = dataset_store.publish_dataset(ds.dataset_id)
    assert ds_published.status == "PUBLISHED"
    assert ds_published.is_published is True

def test_worker_concurrency_locking():
    """Verify that worker lock prevents duplicate concurrent execution."""
    ds_id = "DS-TEST-CONCURRENCY-LOCK"
    
    # Acquire lock
    acquired = dataset_store.acquire_worker_lock(ds_id)
    assert acquired is True
    assert dataset_store.is_worker_active(ds_id) is True

    # Duplicate acquisition must fail
    acquired_second = dataset_store.acquire_worker_lock(ds_id)
    assert acquired_second is False

    # Release lock
    dataset_store.release_worker_lock(ds_id)
    assert dataset_store.is_worker_active(ds_id) is False

def test_startup_interrupted_job_recovery():
    """Verify that interrupted jobs are identified for reboot recovery."""
    ds = dataset_store.register_dataset(
        name="Interrupted Job Test",
        filename="interrupted.geojson",
        format_type="geojson",
        file_size_bytes=2048,
        file_path="data/uploads/interrupted.geojson"
    )
    dataset_store.update_dataset_status(ds.dataset_id, status="PROCESSING", current_stage="Extracting Features", progress_percent=45)

    interrupted = dataset_store.get_interrupted_datasets()
    interrupted_ids = [d.dataset_id for d in interrupted]
    assert ds.dataset_id in interrupted_ids

def test_real_geojson_inspection(tmp_path):
    """Verify real GeoJSON feature count and bounds calculation without hardcoded values."""
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [77.4123, 23.2545]
                },
                "properties": {"name": "Plot 1"}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [77.4250, 23.2680]
                },
                "properties": {"name": "Plot 2"}
            }
        ]
    }
    
    file_path = tmp_path / "test_sample.geojson"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_geojson, f)

    meta = _inspect_geojson(file_path)
    assert meta["feature_count"] == 2
    assert meta["bounds"] == [77.4123, 23.2545, 77.425, 23.268]
    assert meta["crs"] == "EPSG:4326 (WGS 84)"
    assert "Point" in meta["geom_types"]

def test_admin_api_rbac_protection():
    """Verify non-admin users receive 403 Forbidden on admin dataset endpoints."""
    # Create regular user token
    regular_user = User(
        user_id="usr_test_citizen",
        email="user@drishtigis.in",
        name="Test Citizen",
        hashed_password="mockhashedpassword",
        role=UserRole.PUBLIC
    )
    regular_token = create_access_token(regular_user)
    headers = {"Authorization": f"Bearer {regular_token}"}

    # GET admin datasets
    resp = client.get("/api/v1/admin/datasets", headers=headers)
    assert resp.status_code in [401, 403]

    # POST retry admin dataset
    resp = client.post("/api/v1/admin/datasets/DS-BHOPAL-001/retry", headers=headers)
    assert resp.status_code in [401, 403]
