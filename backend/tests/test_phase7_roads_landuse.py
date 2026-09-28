"""
DrishtiGIS — Phase 7 Urban Feature Extraction Test Suite
==========================================================
Tests for road features, metric centerline length/width estimation,
access corridor spatial analysis, land-use classification, non-legal disclaimers,
and API endpoints.

Uses deterministic TEST_FIXTURE geometries to verify software logic without
fabricating real-world land records or AI training labels.
"""

import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon, LineString, mapping

from backend.app.main import app
from backend.app.models.road import RoadFeature, AccessCorridorSummary
from backend.app.models.landuse import LandUseFeature, ParcelLandUseSummary
from backend.app.gis.road_engine import (
    compute_line_length_m,
    compute_parcel_road_distance_m,
    process_road_features,
    analyze_parcel_access
)
from backend.app.gis.landuse_engine import (
    compute_polygon_area_m2,
    process_landuse_features,
    analyze_parcel_landuse
)

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_road_geojson():
    """Sample road GeoJSON feature."""
    line = LineString([[77.4150, 23.2560], [77.4150, 23.2570]])
    return {
        "type": "Feature",
        "properties": {
            "osm_id": "ROAD-FIXTURE-001",
            "highway": "residential",
            "name": "Gandhi Marg",
            "surface": "paved"
        },
        "geometry": mapping(line)
    }

@pytest.fixture
def sample_parcel_geojson():
    """Sample parcel polygon GeoJSON feature."""
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
            "property_id": "DRS-BPL-00101",
            "plot_number": "101"
        },
        "geometry": mapping(poly)
    }

@pytest.fixture
def sample_landuse_geojson():
    """Sample land-use polygon GeoJSON feature."""
    poly = Polygon([
        [77.4140, 23.2550],
        [77.4160, 23.2550],
        [77.4160, 23.2570],
        [77.4140, 23.2570],
        [77.4140, 23.2550]
    ])
    return {
        "type": "Feature",
        "properties": {
            "osm_id": "LU-FIXTURE-001",
            "landuse": "residential"
        },
        "geometry": mapping(poly)
    }


# ── Road Engine & Access Corridor Unit Tests ──────────────────────────────────

def test_road_length_m(sample_road_geojson):
    from shapely.geometry import shape
    geom = shape(sample_road_geojson["geometry"])
    length = compute_line_length_m(geom)
    assert length > 0.0
    assert isinstance(length, float)

def test_process_road_features(sample_road_geojson):
    roads = process_road_features([sample_road_geojson])
    assert len(roads) == 1
    r = roads[0]
    assert r.road_id == "ROAD-FIXTURE-001"
    assert r.road_class == "LOCAL"
    assert r.source_type == "REFERENCE_GIS"
    assert r.estimated_width_m == 5.5
    assert r.length_m > 0.0

def test_analyze_parcel_access_direct(sample_parcel_geojson, sample_road_geojson):
    roads = process_road_features([sample_road_geojson])
    summary = analyze_parcel_access(
        parcel_id="DRS-BPL-00101",
        parcel_geojson_geom=sample_parcel_geojson["geometry"],
        road_features=roads
    )
    assert summary.parcel_id == "DRS-BPL-00101"
    assert summary.access_status == "ACCESS_DETECTED"
    assert summary.has_direct_access is True
    assert summary.nearest_road_id == "ROAD-FIXTURE-001"
    assert summary.distance_to_road_m <= 2.0


# ── Land-Use Processing Unit Tests ───────────────────────────────────────────

def test_landuse_area_m2(sample_landuse_geojson):
    from shapely.geometry import shape
    geom = shape(sample_landuse_geojson["geometry"])
    area = compute_polygon_area_m2(geom)
    assert area > 0.0

def test_process_landuse_features(sample_landuse_geojson):
    landuses = process_landuse_features([sample_landuse_geojson])
    assert len(landuses) == 1
    lu = landuses[0]
    assert lu.landuse_id == "LU-FIXTURE-001"
    assert lu.classification == "RESIDENTIAL"
    assert lu.source_type == "REFERENCE_GIS"

def test_analyze_parcel_landuse(sample_parcel_geojson, sample_landuse_geojson):
    landuses = process_landuse_features([sample_landuse_geojson])
    summary = analyze_parcel_landuse(
        parcel_id="DRS-BPL-00101",
        parcel_geojson_geom=sample_parcel_geojson["geometry"],
        landuse_features=landuses
    )
    assert summary.parcel_id == "DRS-BPL-00101"
    assert summary.observed_land_use_pattern == "RESIDENTIAL"
    assert summary.source_type == "REFERENCE_GIS"


# ── API Endpoint Integration Tests ──────────────────────────────────────────

def test_api_list_roads():
    res = client.get("/api/v1/roads")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_api_get_road_detail():
    res = client.get("/api/v1/roads")
    road_id = res.json()[0]["road_id"]
    detail_res = client.get(f"/api/v1/roads/{road_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["road_id"] == road_id

def test_api_parcel_access_analysis():
    res = client.get("/api/v1/roads/access/DRS-BPL-00101")
    assert res.status_code == 200
    data = res.json()
    assert data["parcel_id"] == "DRS-BPL-00101"
    assert "access_status" in data
    assert "distance_to_road_m" in data

def test_api_list_landuse():
    res = client.get("/api/v1/landuse")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_api_get_landuse_detail():
    res = client.get("/api/v1/landuse")
    lu_id = res.json()[0]["landuse_id"]
    detail_res = client.get(f"/api/v1/landuse/{lu_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["landuse_id"] == lu_id

def test_api_parcel_landuse_analysis():
    res = client.get("/api/v1/landuse/parcel/DRS-BPL-00101")
    assert res.status_code == 200
    data = res.json()
    assert data["parcel_id"] == "DRS-BPL-00101"
    assert "observed_land_use_pattern" in data


# ── Non-Legal Disclaimer & Attribution Integrity Tests ───────────────────────

def test_road_non_legal_disclaimer(sample_parcel_geojson, sample_road_geojson):
    roads = process_road_features([sample_road_geojson])
    summary = analyze_parcel_access("DRS-BPL-00101", sample_parcel_geojson["geometry"], roads)
    assert "disclaimer" in summary.model_dump()
    assert "does not constitute official legal access rights" in summary.disclaimer

def test_landuse_non_legal_disclaimer(sample_parcel_geojson, sample_landuse_geojson):
    landuses = process_landuse_features([sample_landuse_geojson])
    summary = analyze_parcel_landuse("DRS-BPL-00101", sample_parcel_geojson["geometry"], landuses)
    assert "disclaimer" in summary.model_dump()
    assert "does not constitute legal zoning" in summary.disclaimer
