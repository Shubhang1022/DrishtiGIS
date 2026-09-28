"""
DrishtiGIS — Phase 24.8 Raster Dataset Contamination Audit Automated Test Suite
=================================================================================
Verifies that:
1. Only valid 'uav_raster' datasets with status='PUBLISHED' and is_published=True are returned by /api/v1/datasets/published.
2. Legacy/test/archived datasets (such as DS-INGEST-20260922-05E9FA) are strictly excluded.
3. Non-uav_raster formats (geojson, vector, ai_footprints) are excluded from the raster published feed.
4. Dataset bounds for DS-BHOPAL-RASTER-001 match exact physical bounds [77.412951, 23.254292, 77.422689, 23.256671].
5. TileJSON specification returns exact bounds and single raster source schema.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.dataset_store import dataset_store

client = TestClient(app)

def test_01_published_datasets_endpoint_returns_only_single_uav_raster():
    """Verify /api/v1/datasets/published returns exactly 1 published UAV raster dataset."""
    response = client.get("/api/v1/datasets/published")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "datasets" in data
    assert "total" in data
    
    datasets = data["datasets"]
    assert len(datasets) == 1, f"Expected exactly 1 published raster dataset, found {len(datasets)}: {[d['dataset_id'] for d in datasets]}"
    
    active_ds = datasets[0]
    assert active_ds["dataset_id"] == "DS-BHOPAL-RASTER-001"
    assert active_ds["format"] == "uav_raster"
    assert active_ds["is_published"] is True

def test_02_archived_and_test_datasets_excluded():
    """Verify test dataset DS-INGEST-20260922-05E9FA and non-raster datasets are excluded from published list."""
    response = client.get("/api/v1/datasets/published")
    data = response.json()
    published_ids = [d["dataset_id"] for d in data["datasets"]]
    
    assert "DS-INGEST-20260922-05E9FA" not in published_ids, "Contaminating dataset DS-INGEST-20260922-05E9FA must NOT be published"
    assert "DS-BHOPAL-VECTOR-002" not in published_ids, "Vector dataset should not be in raster tile feed"
    assert "DS-BHOPAL-AI-003" not in published_ids, "AI footprints should not be in raster tile feed"

def test_03_authoritative_raster_bounds():
    """Verify DS-BHOPAL-RASTER-001 bounds match exact WGS84 physical coverage."""
    response = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001")
    assert response.status_code == 200
    
    ds = response.json()
    expected_bounds = [77.412951, 23.254292, 77.422689, 23.256671]
    assert ds["bounds"] == expected_bounds, f"Expected bounds {expected_bounds}, got {ds['bounds']}"

def test_04_tilejson_endpoint():
    """Verify TileJSON endpoint for active dataset returns correct specification."""
    response = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tilejson.json")
    assert response.status_code == 200
    
    tilejson = response.json()
    assert tilejson["tilejson"] == "3.0.0"
    assert tilejson["scheme"] == "xyz"
    assert tilejson["tileSize"] == 256
    assert tilejson["bounds"] == [77.412951, 23.254292, 77.422689, 23.256671]
    assert len(tilejson["tiles"]) == 1
    assert tilejson["tiles"][0] == "/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/{z}/{x}/{y}.png"

def test_05_unpublished_dataset_tilejson_forbidden():
    """Verify requesting TileJSON for an archived/unpublished dataset returns 403."""
    response = client.get("/api/v1/datasets/DS-INGEST-20260922-05E9FA/tilejson.json")
    assert response.status_code == 403, f"Expected 403 Forbidden for unpublished dataset, got {response.status_code}"

def test_06_unpublished_dataset_tiles_forbidden():
    """Verify requesting tiles for an archived/unpublished dataset returns 403."""
    response = client.get("/api/v1/datasets/DS-INGEST-20260922-05E9FA/tiles/16/46865/28415.png")
    assert response.status_code == 403, f"Expected 403 Forbidden for unpublished dataset tiles, got {response.status_code}"
