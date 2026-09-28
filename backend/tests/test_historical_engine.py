"""
DrishtiGIS — Phase 6 Historical & Multi-Epoch Test Suite
==========================================================
Tests for temporal dataset registration, building footprint spatial change
detection algorithms (IoU, centroid shift, area delta), parcel-level
aggregation, and API endpoints.

Uses deterministic TEST_FIXTURE geometries to verify software logic without
fabricating real historical land records.
"""

import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon, mapping

from backend.app.main import app
from backend.app.models.epoch import EpochMetadata, BuildingChangeItem, ParcelChangeSummary
from backend.app.gis.change_engine import (
    compute_iou,
    compute_polygon_area_m2,
    compute_centroid_distance_m,
    compare_building_epochs,
    summarize_parcel_changes
)

client = TestClient(app)

# ── Deterministic TEST_FIXTURE Geometries ─────────────────────────────────────

@pytest.fixture
def base_square_geojson():
    """Baseline test building square: (77.4150, 23.2560) to (77.4152, 23.2562)."""
    poly = Polygon([
        [77.4150, 23.2560],
        [77.4152, 23.2560],
        [77.4152, 23.2562],
        [77.4150, 23.2562],
        [77.4150, 23.2560]
    ])
    return {
        "type": "Feature",
        "properties": {
            "id": "FIXTURE-BLD-BASE-001",
            "primary_parcel_id": "DRS-BPL-00101",
            "confidence": 0.94
        },
        "geometry": mapping(poly)
    }

@pytest.fixture
def modified_square_geojson():
    """Slightly modified target building square (expanded east)."""
    poly = Polygon([
        [77.4150, 23.2560],
        [77.4153, 23.2560],
        [77.4153, 23.2562],
        [77.4150, 23.2562],
        [77.4150, 23.2560]
    ])
    return {
        "type": "Feature",
        "properties": {
            "id": "FIXTURE-BLD-TGT-001",
            "primary_parcel_id": "DRS-BPL-00101",
            "confidence": 0.95
        },
        "geometry": mapping(poly)
    }

@pytest.fixture
def added_square_geojson():
    """Newly added target building square elsewhere on parcel."""
    poly = Polygon([
        [77.4160, 23.2565],
        [77.4162, 23.2565],
        [77.4162, 23.2567],
        [77.4160, 23.2567],
        [77.4160, 23.2565]
    ])
    return {
        "type": "Feature",
        "properties": {
            "id": "FIXTURE-BLD-TGT-NEW",
            "primary_parcel_id": "DRS-BPL-00101",
            "confidence": 0.92
        },
        "geometry": mapping(poly)
    }


# ── Unit Tests: Geometry Metrics & IoU ───────────────────────────────────────

def test_compute_polygon_area_m2(base_square_geojson):
    from shapely.geometry import shape
    g = shape(base_square_geojson["geometry"])
    area = compute_polygon_area_m2(g)
    assert area > 0.0
    assert isinstance(area, float)

def test_compute_iou_identical(base_square_geojson):
    from shapely.geometry import shape
    g = shape(base_square_geojson["geometry"])
    iou = compute_iou(g, g)
    assert iou == 1.0

def test_compute_iou_partial_overlap(base_square_geojson, modified_square_geojson):
    from shapely.geometry import shape
    g1 = shape(base_square_geojson["geometry"])
    g2 = shape(modified_square_geojson["geometry"])
    iou = compute_iou(g1, g2)
    assert 0.5 < iou < 1.0


# ── Spatial Change Engine Tests ──────────────────────────────────────────────

def test_change_engine_unchanged(base_square_geojson):
    changes = compare_building_epochs([base_square_geojson], [base_square_geojson])
    assert len(changes) == 1
    assert changes[0].change_type == "UNCHANGED"
    assert changes[0].iou_score == 1.0
    assert changes[0].area_delta_m2 == 0.0

def test_change_engine_modified(base_square_geojson, modified_square_geojson):
    changes = compare_building_epochs([base_square_geojson], [modified_square_geojson])
    assert len(changes) == 1
    assert changes[0].change_type == "MODIFIED"
    assert changes[0].area_delta_m2 > 0.0

def test_change_engine_removed(base_square_geojson):
    changes = compare_building_epochs([base_square_geojson], [])
    assert len(changes) == 1
    assert changes[0].change_type == "REMOVED"
    assert changes[0].area_delta_m2 < 0.0

def test_change_engine_added(added_square_geojson):
    changes = compare_building_epochs([], [added_square_geojson])
    assert len(changes) == 1
    assert changes[0].change_type == "ADDED"
    assert changes[0].area_delta_m2 > 0.0

def test_parcel_change_summary(base_square_geojson, modified_square_geojson, added_square_geojson):
    summary = summarize_parcel_changes(
        parcel_id="DRS-BPL-00101",
        baseline_epoch_id="EPOCH-BPL-2024-01",
        target_epoch_id="EPOCH-BPL-2025-06",
        baseline_buildings=[base_square_geojson],
        target_buildings=[modified_square_geojson, added_square_geojson]
    )
    assert summary.parcel_id == "DRS-BPL-00101"
    assert summary.baseline_building_count == 1
    assert summary.target_building_count == 2
    assert summary.added_count == 1
    assert summary.modified_count == 1
    assert summary.removed_count == 0


# ── API Endpoint Integration Tests ──────────────────────────────────────────

def test_api_list_epochs():
    res = client.get("/api/v1/historical/epochs")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(e["epoch_id"] == "EPOCH-BPL-2024-01" for e in data)

def test_api_get_epoch_detail():
    res = client.get("/api/v1/historical/epochs/EPOCH-BPL-2024-01")
    assert res.status_code == 200
    data = res.json()
    assert data["epoch_id"] == "EPOCH-BPL-2024-01"
    assert data["is_baseline"] is True

def test_api_compare_epochs():
    res = client.get("/api/v1/historical/compare?parcel_id=DRS-BPL-00101")
    assert res.status_code == 200
    data = res.json()
    assert data["parcel_id"] == "DRS-BPL-00101"
    assert "changes" in data
    assert "total_area_change_m2" in data

def test_api_ingest_epoch():
    new_epoch = {
        "epoch_id": "EPOCH-LKO-2025-01",
        "dataset_id": "DATASET-LUCKNOW-UAV",
        "region_id": "REGION-LKO-01",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "crs": "EPSG:4326",
        "acquisition_datetime": "2025-01-10T09:00:00Z",
        "resolution_m": 0.05,
        "source_type": "UAV_ORTHOMOSAIC",
        "description": "Lucknow UAV temporal test dataset.",
        "building_count": 120,
        "is_baseline": False
    }
    res = client.post("/api/v1/historical/ingest", json=new_epoch)
    assert res.status_code == 201
    data = res.json()
    assert data["epoch_id"] == "EPOCH-LKO-2025-01"


# ── Non-Legal Disclaimer & Attribution Integrity Tests ───────────────────────

def test_disclaimer_on_change_item(base_square_geojson, modified_square_geojson):
    changes = compare_building_epochs([base_square_geojson], [modified_square_geojson])
    assert len(changes) > 0
    for chg in changes:
        assert "disclaimer" in chg.model_dump()
        assert "not an official cadastral change" in chg.disclaimer
