"""
DrishtiGIS — Phase 8 Review & Ground-Truthing Workflow Tests
=============================================================
Tests for surveyor review queue, audit trail, geometry editing, topology validation,
spatial relationship recomputation, field verifications, GeoJSON export, and source classification.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.review import (
    ReviewItem,
    ReviewStatus,
    ReviewIssueType,
    ReviewSeverity,
    VerificationMethod,
    UserRole,
    ReviewSource,
)
from backend.app.services.review_store import review_store
from backend.app.gis.review_engine import validate_edited_geometry, recompute_parcel_building_relationships
from backend.app.auth.user_store import user_store
from backend.app.auth.auth_service import create_access_token

client = TestClient(app)

def get_surveyor_headers():
    surveyor_user = user_store.get_by_email("demo-surveyor@drishtigis.in")
    token = create_access_token(surveyor_user)
    return {"Authorization": f"Bearer {token}"}



def test_review_queue_retrieval():
    """Verify GET /api/v1/reviews returns seeded review items."""
    response = client.get("/api/v1/reviews")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] > 0
    assert data["_disclaimer"] is not None


def test_review_queue_filters():
    """Verify filters for status, issue_type, severity, and city."""
    # Filter by issue_type
    response = client.get("/api/v1/reviews?issue_type=BUILDING_CROSSES_PARCEL_BOUNDARY")
    assert response.status_code == 200
    data = response.json()
    assert all(item["issue_type"] == "BUILDING_CROSSES_PARCEL_BOUNDARY" for item in data["items"])

    # Filter by city
    response = client.get("/api/v1/reviews?city=Bhopal")
    assert response.status_code == 200
    data = response.json()
    assert all(item["city"] == "Bhopal" for item in data["items"])

    # Filter by non-existent city
    response = client.get("/api/v1/reviews?city=Lucknow")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_review_stats():
    """Verify GET /api/v1/reviews/stats."""
    response = client.get("/api/v1/reviews/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total_issues" in stats
    assert "open" in stats
    assert "field_verification_required" in stats


def test_get_review_detail():
    """Verify GET /api/v1/reviews/{review_id} with audit trail."""
    reviews = review_store.list_reviews()
    assert len(reviews) > 0
    sample_id = reviews[0].review_id

    response = client.get(f"/api/v1/reviews/{sample_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["item"]["review_id"] == sample_id
    assert "audit_trail" in data
    assert len(data["audit_trail"]) >= 1


def test_status_transition_and_audit_log():
    """Verify status update creates an audit trail entry without losing history."""
    reviews = review_store.list_reviews()
    sample = reviews[0]
    rev_id = sample.review_id

    # Update to IN_REVIEW
    response = client.patch(
        f"/api/v1/reviews/{rev_id}",
        json={"status": "IN_REVIEW", "reviewer": "Surveyor-01", "notes": "Inspecting discrepancy evidence."},
        headers=get_surveyor_headers()
    )
    assert response.status_code == 200
    assert response.json()["item"]["status"] == "IN_REVIEW"

    # Fetch audit trail
    response = client.get(f"/api/v1/reviews/{rev_id}/audit")
    assert response.status_code == 200
    audits = response.json()["audit_trail"]
    assert any(a["new_status"] == "IN_REVIEW" for a in audits)


def test_geometry_validation_valid():
    """Verify topology validation allows valid polygon."""
    valid_poly = {
        "type": "Polygon",
        "coordinates": [[
            [77.4000, 23.2500],
            [77.4010, 23.2500],
            [77.4010, 23.2510],
            [77.4000, 23.2510],
            [77.4000, 23.2500]
        ]]
    }
    is_valid, msg, meta = validate_edited_geometry(valid_poly)
    assert is_valid is True
    assert msg is None
    assert meta["area_m2"] > 0


def test_geometry_validation_invalid_self_intersecting():
    """Verify topology validation rejects self-intersecting polygon."""
    invalid_bow_tie = {
        "type": "Polygon",
        "coordinates": [[
            [77.4000, 23.2500],
            [77.4010, 23.2510],
            [77.4010, 23.2500],
            [77.4000, 23.2510],
            [77.4000, 23.2500]
        ]]
    }
    is_valid, msg, meta = validate_edited_geometry(invalid_bow_tie)
    assert is_valid is False
    assert "Geometry requires correction before approval" in msg


def test_geometry_edit_endpoint_rejection():
    """Verify POST /api/v1/reviews/{review_id}/geometry rejects invalid geometry."""
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id

    invalid_geom = {
        "type": "Polygon",
        "coordinates": [[
            [77.4000, 23.2500],
            [77.4010, 23.2510],
            [77.4010, 23.2500],
            [77.4000, 23.2510],
            [77.4000, 23.2500]
        ]]
    }

    response = client.post(
        f"/api/v1/reviews/{rev_id}/geometry",
        json={"geometry": invalid_geom, "reviewer": "Surveyor-01", "notes": "Attempting invalid edit."},
        headers=get_surveyor_headers()
    )
    assert response.status_code == 400
    assert "Geometry requires correction before approval" in response.json()["detail"]


def test_original_ai_geometry_immutability():
    """Verify original AI geometry remains intact after surveyor geometry edit."""
    reviews = review_store.list_reviews()
    sample = reviews[0]
    rev_id = sample.review_id

    valid_geom = {
        "type": "Polygon",
        "coordinates": [[
            [77.4000, 23.2500],
            [77.4020, 23.2500],
            [77.4020, 23.2520],
            [77.4000, 23.2520],
            [77.4000, 23.2500]
        ]]
    }

    response = client.post(
        f"/api/v1/reviews/{rev_id}/geometry",
        json={"geometry": valid_geom, "reviewer": "Surveyor-01", "notes": "Adjusted boundary."},
        headers=get_surveyor_headers()
    )
    assert response.status_code == 200
    item = response.json()["item"]

    # Source must be REVIEWED_AI_GEOMETRY
    assert item["source"] == "REVIEWED_AI_GEOMETRY"
    assert item["reviewed_geometry"] == valid_geom
    # Original geometry must be preserved
    assert item["original_geometry"] == sample.original_geometry


def test_parcel_building_relationship_recomputation():
    """Verify spatial relationships are recomputed upon parcel geometry edit."""
    parcel_poly = {
        "type": "Polygon",
        "coordinates": [[
            [77.4000, 23.2500],
            [77.4050, 23.2500],
            [77.4050, 23.2550],
            [77.4000, 23.2550],
            [77.4000, 23.2500]
        ]]
    }

    bldg1 = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [77.4010, 23.2510],
                [77.4020, 23.2510],
                [77.4020, 23.2520],
                [77.4010, 23.2520],
                [77.4010, 23.2510]
            ]]
        },
        "properties": {"id": "AI-BLD-TEST-1"}
    }

    results = recompute_parcel_building_relationships(parcel_poly, [bldg1], parcel_id="parcel-demo-001")
    assert results["building_count"] == 1
    assert results["buildings"][0]["properties"]["parcel_relationship"] == "FULLY_WITHIN"


def test_field_verification_workflow():
    """Verify field verification observation registration."""
    reviews = review_store.list_reviews()
    rev_id = reviews[0].review_id

    response = client.post(
        f"/api/v1/reviews/{rev_id}/verify",
        json={
            "verification_method": "GNSS",
            "observed_feature": "Observed boundary",
            "observation": "Observed boundary differs from preliminary AI-derived boundary.",
            "reviewer": "Field-Surveyor-02",
            "location": {"latitude": 23.2501, "longitude": 77.4002},
            "notes": "Verified using RTK GNSS receiver."
        },
        headers=get_surveyor_headers()
    )
    assert response.status_code == 201
    assert response.json()["status"] == "FIELD_VERIFICATION_REQUIRED"

    # Check updated review detail
    response = client.get(f"/api/v1/reviews/{rev_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["item"]["verification_method"] == "GNSS"
    assert len(data["field_verifications"]) >= 1


def test_geojson_export():
    """Verify reviewed GIS export as GeoJSON."""
    response = client.get("/api/v1/reviews/export?city=Bhopal")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "crs" in data
    assert data["_source"] == "REVIEWED_AI_GEOMETRY"
    assert "disclaimer" in data["features"][0]["properties"]
