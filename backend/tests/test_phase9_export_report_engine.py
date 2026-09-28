"""
DrishtiGIS — Phase 9 GIS Export, Dynamic Reports & Evidence Packaging Tests
=============================================================================
Tests for unified GIS export engine (GeoJSON, GeoPackage, ZIP), report generator,
evidence packager, metadata preservation, CRS handling, and API endpoints.
"""

import json
import zipfile
import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.gis.export_engine import build_gis_export, validate_export
from backend.app.reports.report_engine import (
    generate_parcel_report,
    generate_surveyor_report,
    generate_area_report,
)
from backend.app.reports.evidence_packager import create_evidence_package

client = TestClient(app)


def test_export_formats_endpoint():
    """Verify GET /api/v1/exports/formats."""
    response = client.get("/api/v1/exports/formats")
    assert response.status_code == 200
    data = response.json()
    assert "supported_formats" in data
    assert "supported_layers" in data
    assert "supported_crss" in data
    format_ids = [f["id"] for f in data["supported_formats"]]
    assert "GeoJSON" in format_ids
    assert "GeoPackage" in format_ids
    assert "ZIP" in format_ids


def test_geojson_export_generation():
    """Verify GeoJSON multi-layer export generation."""
    file_bytes, filename, meta = build_gis_export(
        layers=["parcels", "buildings", "roads", "landuse"],
        output_format="GeoJSON",
        output_crs="EPSG:4326"
    )
    assert filename.endswith(".geojson")
    assert meta["feature_count"] > 0
    assert meta["layer_count"] == 4

    payload = json.loads(file_bytes.decode("utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert "metadata" in payload
    assert payload["metadata"]["export_id"] == meta["export_id"]

    # Verify source classifications and disclaimers preserved
    sources = set(f["properties"]["source"] for f in payload["features"] if "source" in f["properties"])
    assert "SYNTHETIC_DEMO" in sources
    assert "AI_DERIVED_UAVPAL" in sources
    assert "REFERENCE_GIS" in sources


def test_geopackage_export_generation():
    """Verify GeoPackage (.gpkg) export generation."""
    file_bytes, filename, meta = build_gis_export(
        layers=["parcels", "buildings"],
        output_format="GeoPackage"
    )
    assert filename.endswith(".gpkg")
    assert len(file_bytes) > 0


def test_zip_export_generation():
    """Verify ZIP multi-layer export archive generation."""
    file_bytes, filename, meta = build_gis_export(
        layers=["parcels", "buildings", "roads"],
        output_format="ZIP"
    )
    assert filename.endswith(".zip")
    zip_buffer = io.BytesIO(file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        names = zf.namelist()
        assert "metadata.json" in names
        assert "layers/parcels.geojson" in names
        assert "layers/buildings.geojson" in names
        assert "README.md" in names


def test_export_validation_pass():
    """Verify export validation passes valid GeoJSON payload."""
    valid_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [77.40, 23.25]},
                "properties": {"id": "1", "source": "AI_DERIVED_UAVPAL"}
            }
        ]
    }
    is_valid, errs = validate_export(valid_payload)
    assert is_valid is True
    assert len(errs) == 0


def test_export_validation_fail_empty_features():
    """Verify export validation rejects empty feature collection."""
    invalid_payload = {"type": "FeatureCollection", "features": []}
    is_valid, errs = validate_export(invalid_payload)
    assert is_valid is False
    assert any("empty" in e for e in errs)


def test_dynamic_parcel_report():
    """Verify dynamic parcel report generation."""
    report = generate_parcel_report("DRS-BPL-DEMO-001")
    assert report["report_type"] == "PARCEL_INTELLIGENCE_DOSSIER"
    assert report["parcel"]["parcel_id"] in ["DRS-BPL-DEMO-001", "parcel-demo-001"]
    assert report["parcel"]["source"] == "SYNTHETIC_DEMO"
    assert "Synthetic prototype data" in report["parcel"]["disclaimer"]
    assert report["ai_building_analysis"]["building_count"] >= 0


def test_dynamic_area_report():
    """Verify area report dynamically calculates statistics."""
    report = generate_area_report(city="Bhopal")
    assert report["report_type"] == "AREA_INTELLIGENCE_REPORT"
    assert report["location"]["city"] == "Bhopal"
    assert report["ai_building_extraction_metrics"]["total_buildings_detected"] == 834
    assert report["parcel_cadastral_metrics"]["total_demonstration_parcels"] == 35
    assert report["road_network_metrics"]["total_road_segments"] == 2933
    assert report["observed_landuse_metrics"]["total_polygons"] == 98


def test_evidence_package_generation():
    """Verify evidence package ZIP structure."""
    zip_bytes, filename = create_evidence_package(city="Bhopal")
    assert filename.endswith(".zip")
    zip_buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        names = zf.namelist()
        assert "metadata/dataset.json" in names
        assert "metadata/processing.json" in names
        assert "metadata/crs.json" in names
        assert "layers/parcels.geojson" in names
        assert "layers/buildings.geojson" in names
        assert "layers/roads.geojson" in names
        assert "layers/landuse.geojson" in names
        assert "reports/area_intelligence_report.json" in names
        assert "README.md" in names

        readme_text = zf.read("README.md").decode("utf-8")
        assert "Synthetic prototype data" in readme_text


def test_export_api_endpoint():
    """Verify POST /api/v1/exports."""
    response = client.post(
        "/api/v1/exports",
        json={
            "dataset_id": "DATASET-BHOPAL-UAV",
            "layers": ["parcels", "buildings"],
            "output_format": "GeoJSON",
            "output_crs": "EPSG:4326"
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "X-Export-ID" in response.headers


def test_reports_api_endpoints():
    """Verify POST /api/v1/reports/parcel/DRS-BPL-DEMO-001 and GET /api/v1/reports/region."""
    res1 = client.post("/api/v1/reports/parcel/DRS-BPL-DEMO-001")
    assert res1.status_code == 200
    assert res1.json()["parcel"]["parcel_id"] in ["DRS-BPL-DEMO-001", "parcel-demo-001"]

    res2 = client.get("/api/v1/reports/region?city=Bhopal")
    assert res2.status_code == 200
    assert res2.json()["location"]["city"] == "Bhopal"
