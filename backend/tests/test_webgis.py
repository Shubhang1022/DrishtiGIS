"""
DrishtiGIS — Core India WebGIS Integration Tests
==================================================
Spec: core-india-webgis v0.1, Task A.8

Tests every new endpoint introduced in this spec:
  - Raster tile API
  - OSM layer API
  - Coverage availability API
  - Location search API
  - Parcel API (extended behavior)
  - AI feature API (source classification)
  - Data integrity (no raw dataset exposure)
  - Path traversal protection

Run from backend/ directory:
    python -m pytest tests/test_webgis.py -v
"""

import json
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# Ensure the backend package is importable when pytest runs from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=True)

# ── Known-good tile coordinates (verified in Phase 2) ─────────────────────
GOOD_Z, GOOD_X, GOOD_Y = 18, 187445, 113652


# =============================================================================
# Raster Tile Endpoint Tests
# =============================================================================

class TestTileEndpoint:
    def test_valid_tile_returns_200(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/{GOOD_X}/{GOOD_Y}.png")
        assert r.status_code == 200

    def test_valid_tile_content_type_is_png(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/{GOOD_X}/{GOOD_Y}.png")
        assert r.status_code == 200
        assert "image/png" in r.headers["content-type"]

    def test_valid_tile_body_is_non_empty(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/{GOOD_X}/{GOOD_Y}.png")
        assert r.status_code == 200
        assert len(r.content) > 500

    def test_valid_tile_has_cache_header(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/{GOOD_X}/{GOOD_Y}.png")
        assert r.status_code == 200
        cc = r.headers.get("cache-control", "")
        assert "public" in cc
        assert "max-age" in cc

    def test_zoom_below_range_returns_404(self):
        r = client.get(f"/api/v1/tiles/bhopal/17/{GOOD_X}/{GOOD_Y}.png")
        assert r.status_code == 404

    def test_zoom_above_range_returns_404(self):
        r = client.get(f"/api/v1/tiles/bhopal/22/{GOOD_X}/{GOOD_Y}.png")
        assert r.status_code == 404

    def test_nonexistent_tile_coords_returns_404(self):
        r = client.get("/api/v1/tiles/bhopal/18/0/0.png")
        assert r.status_code == 404

    def test_non_integer_z_returns_422(self):
        r = client.get("/api/v1/tiles/bhopal/abc/0/0.png")
        assert r.status_code == 422

    def test_non_integer_x_returns_422(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/abc/0.png")
        assert r.status_code == 422

    def test_non_integer_y_returns_422(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/{GOOD_X}/abc.png")
        assert r.status_code == 422

    def test_negative_x_returns_422(self):
        r = client.get(f"/api/v1/tiles/bhopal/{GOOD_Z}/-1/{GOOD_Y}.png")
        assert r.status_code == 422

    def test_path_traversal_attempt_rejected(self):
        # Path-like strings cannot be integers — FastAPI rejects at 422
        r = client.get("/api/v1/tiles/bhopal/18/../../../etc/passwd.png")
        assert r.status_code in (404, 422)

    def test_zoom_19_tile_exists(self):
        """Zoom 19: x=374891, y=227304 (computed from Bhopal center)"""
        r = client.get("/api/v1/tiles/bhopal/19/374891/227304.png")
        assert r.status_code == 200

    def test_zoom_20_tile_exists(self):
        """Zoom 20: x=749783, y=454608"""
        r = client.get("/api/v1/tiles/bhopal/20/749783/454608.png")
        assert r.status_code == 200


# =============================================================================
# OSM Layer Endpoint Tests
# =============================================================================

class TestOsmLayers:
    @pytest.mark.parametrize("layer", ["buildings", "roads", "waterways", "landuse"])
    def test_all_layers_return_200(self, layer: str):
        r = client.get(f"/api/v1/osm/bhopal/{layer}")
        assert r.status_code == 200, f"Layer {layer} returned {r.status_code}"

    @pytest.mark.parametrize("layer", ["buildings", "roads", "waterways", "landuse"])
    def test_all_layers_return_valid_geojson(self, layer: str):
        r = client.get(f"/api/v1/osm/bhopal/{layer}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) > 0

    @pytest.mark.parametrize("layer", ["buildings", "roads", "waterways", "landuse"])
    def test_all_layers_source_is_osm(self, layer: str):
        r = client.get(f"/api/v1/osm/bhopal/{layer}")
        data = r.json()
        # _source is embedded in the GeoJSON file from Phase 3 extraction
        assert data.get("_source") == "OSM_OPENSTREETMAP" or \
               data.get("metadata", {}).get("_source") == "OSM_OPENSTREETMAP"

    @pytest.mark.parametrize("layer", ["buildings", "roads", "waterways", "landuse"])
    def test_all_layers_have_attribution_header(self, layer: str):
        r = client.get(f"/api/v1/osm/bhopal/{layer}")
        attribution = r.headers.get("x-osm-attribution", "")
        assert "OpenStreetMap" in attribution
        assert "ODbL" in attribution
    @pytest.mark.parametrize("layer", ["buildings", "roads", "waterways", "landuse"])
    def test_all_layers_have_data_source_header(self, layer: str):
        r = client.get(f"/api/v1/osm/bhopal/{layer}")
        assert r.headers.get("x-data-source") == "OSM_OPENSTREETMAP"

    def test_unknown_layer_returns_404(self):
        r = client.get("/api/v1/osm/bhopal/schools")
        assert r.status_code == 404

    def test_internal_bbox_nodes_not_exposed(self):
        r = client.get("/api/v1/osm/bhopal/_bbox_nodes")
        assert r.status_code == 404

    def test_extraction_report_not_exposed(self):
        r = client.get("/api/v1/osm/bhopal/extraction_report")
        assert r.status_code == 404

    def test_roads_feature_count(self):
        r = client.get("/api/v1/osm/bhopal/roads")
        data = r.json()
        assert len(data["features"]) == 2933

    def test_waterways_feature_count(self):
        r = client.get("/api/v1/osm/bhopal/waterways")
        data = r.json()
        assert len(data["features"]) == 31

    def test_landuse_feature_count(self):
        r = client.get("/api/v1/osm/bhopal/landuse")
        data = r.json()
        assert len(data["features"]) == 98

    def test_osm_features_have_osm_id(self):
        r = client.get("/api/v1/osm/bhopal/roads")
        data = r.json()
        sample = data["features"][:5]
        for feat in sample:
            assert "osm_id" in feat["properties"]
            assert isinstance(feat["properties"]["osm_id"], int)
            assert feat["properties"]["osm_id"] > 0

    def test_osm_features_not_fabricated(self):
        """All OSM IDs must be positive integers — no fabricated data."""
        r = client.get("/api/v1/osm/bhopal/roads")
        data = r.json()
        for feat in data["features"][:20]:
            osm_id = feat["properties"].get("osm_id", -1)
            assert isinstance(osm_id, int) and osm_id > 0, \
                f"Fabricated or invalid osm_id: {osm_id}"

    def test_osm_source_distinct_from_ai(self):
        osm_r = client.get("/api/v1/osm/bhopal/buildings")
        ai_r  = client.get("/api/v1/features")
        # OSM source must be different from AI source
        osm_src = osm_r.json().get("_source") or osm_r.json().get("metadata", {}).get("_source")
        ai_src  = ai_r.json().get("_source")
        assert osm_src == "OSM_OPENSTREETMAP"
        assert ai_src == "AI_DERIVED_DEMO"
        assert osm_src != ai_src


# =============================================================================
# Coverage / Location Search Tests
# =============================================================================

class TestCoverageEndpoint:
    def test_bhopal_coverage_returns_200(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert r.status_code == 200

    def test_bhopal_imagery_available(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert r.json()["imagery_available"] is True

    def test_bhopal_parcel_available(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert r.json()["parcel_data_available"] is True

    def test_bhopal_ai_available(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert r.json()["ai_analysis_available"] is True

    def test_bhopal_historical_not_available(self):
        """historical_data_available must be False — no second epoch exists."""
        r = client.get("/api/v1/coverage/bhopal")
        assert r.json()["historical_data_available"] is False

    def test_bhopal_source_is_prototype(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert r.json()["coverage_source"] == "prototype"

    def test_bhopal_disclaimer_present(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert r.json()["disclaimer"] is not None
        assert len(r.json()["disclaimer"]) > 10

    def test_bhopal_has_datasets(self):
        r = client.get("/api/v1/coverage/bhopal")
        assert "datasets" in r.json()
        assert len(r.json()["datasets"]) >= 1

    def test_lucknow_imagery_false(self):
        r = client.get("/api/v1/coverage/lucknow")
        assert r.status_code == 200
        assert r.json()["imagery_available"] is False

    def test_lucknow_parcel_false(self):
        r = client.get("/api/v1/coverage/lucknow")
        assert r.json()["parcel_data_available"] is False

    def test_lucknow_ai_false(self):
        r = client.get("/api/v1/coverage/lucknow")
        assert r.json()["ai_analysis_available"] is False

    def test_lucknow_coverage_none(self):
        r = client.get("/api/v1/coverage/lucknow")
        assert r.json()["coverage_source"] == "none"

    def test_lucknow_no_disclaimer(self):
        r = client.get("/api/v1/coverage/lucknow")
        assert r.json()["disclaimer"] is None

    def test_delhi_slug_works(self):
        r = client.get("/api/v1/coverage/delhi")
        assert r.status_code == 200
        assert r.json()["imagery_available"] is False

    def test_hyphenated_slug(self):
        """new-delhi slug must be normalised to 'New Delhi'"""
        r = client.get("/api/v1/coverage/new-delhi")
        assert r.status_code == 200
        assert r.json()["coverage_source"] == "none"

    def test_unknown_city_coverage_graceful(self):
        r = client.get("/api/v1/coverage/nonexistentcity123")
        assert r.status_code == 200
        assert r.json()["imagery_available"] is False


class TestLocationSearch:
    def test_bhopal_search_returns_results(self):
        r = client.get("/api/v1/locations/search?q=Bhopal")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_bhopal_search_result_has_coverage(self):
        r = client.get("/api/v1/locations/search?q=Bhopal")
        bhopal = next(x for x in r.json()["results"] if x["name"] == "Bhopal")
        assert bhopal["coverage"]["imagery_available"] is True
        assert bhopal["coverage"]["parcel_data_available"] is True

    def test_lucknow_search_no_intelligence(self):
        r = client.get("/api/v1/locations/search?q=Lucknow")
        data = r.json()
        assert data["total"] >= 1
        lucknow = next(x for x in data["results"] if x["name"] == "Lucknow")
        assert lucknow["coverage"]["parcel_data_available"] is False
        assert lucknow["coverage"]["imagery_available"] is False

    def test_delhi_search(self):
        r = client.get("/api/v1/locations/search?q=Delhi")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_nonexistent_city_empty(self):
        r = client.get("/api/v1/locations/search?q=xyz_nonexistent_city_123")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_search_result_has_center(self):
        r = client.get("/api/v1/locations/search?q=Mumbai")
        result = r.json()["results"][0]
        assert "center" in result
        assert "lat" in result["center"]
        assert "lon" in result["center"]

    def test_search_result_has_zoom(self):
        r = client.get("/api/v1/locations/search?q=Bhopal")
        result = r.json()["results"][0]
        assert "zoom_level" in result
        assert isinstance(result["zoom_level"], int)

    def test_state_search_works(self):
        """Searching by state name should return cities in that state"""
        r = client.get("/api/v1/locations/search?q=Maharashtra")
        data = r.json()
        assert data["total"] >= 1
        # At least one result should be from Maharashtra
        assert any(x["state"] == "Maharashtra" for x in data["results"])

    def test_search_caps_at_ten(self):
        """Results must not exceed 10"""
        r = client.get("/api/v1/locations/search?q=a")  # many matches
        assert len(r.json()["results"]) <= 10


# =============================================================================
# Parcel API Extended Behavior
# =============================================================================

class TestParcelExtended:
    def test_bhopal_returns_3_parcels(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        assert len(data["features"]) == 3

    def test_bhopal_parcel_source_classification(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert r.json()["_source"] == "DEMO_DATA_PROTOTYPE_ONLY"

    def test_bhopal_demo_placeholder_header(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert r.headers.get("x-data-status") == "demo-placeholder"

    def test_lucknow_returns_zero_with_coverage_note(self):
        r = client.get("/api/v1/parcels?city=Lucknow")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert len(data["features"]) == 0
        assert "_coverage_note" in data
        assert "Lucknow" in data["_coverage_note"]

    def test_delhi_coverage_note(self):
        r = client.get("/api/v1/parcels?city=Delhi")
        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert "_coverage_note" in r.json()

    def test_parcel_detail_drs_bpl_00101(self):
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        assert r.status_code == 200
        data = r.json()
        assert data["parcel"]["properties"]["property_id"] == "DRS-BPL-00101"
        assert data["parcel"]["properties"]["city"] == "Bhopal"
        assert data["property"] is not None
        assert "_source" in data

    def test_parcel_detail_has_ai_features(self):
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        data = r.json()
        assert "ai_features" in data
        assert len(data["ai_features"]) >= 1

    def test_parcel_detail_has_discrepancies(self):
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        data = r.json()
        assert "discrepancies" in data
        assert len(data["discrepancies"]) >= 1

    def test_discrepancy_legal_status_null(self):
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        for disc in r.json()["discrepancies"]:
            assert disc["legal_status"] is None

    def test_discrepancy_no_forbidden_language(self):
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        for disc in r.json()["discrepancies"]:
            text = (disc.get("description", "") + disc.get("ui_label", "")).lower()
            for forbidden in ["illegal", "fraud", "encroachment", "violation", "unauthorized"]:
                assert forbidden not in text, f"Forbidden word '{forbidden}' found in discrepancy"

    def test_unknown_parcel_returns_404(self):
        r = client.get("/api/v1/parcels/NONEXISTENT-00000")
        assert r.status_code == 404

    def test_parcel_not_labeled_as_official(self):
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        assert r.json()["_source"] == "DEMO_DATA_PROTOTYPE_ONLY"
        assert r.json()["_source"] != "OFFICIAL_REFERENCE"


# =============================================================================
# AI Feature Source Classification
# =============================================================================

class TestAIFeatureSourceClassification:
    def test_ai_features_source_is_ai_derived_demo(self):
        r = client.get("/api/v1/features")
        assert r.status_code == 200
        assert r.json()["_source"] == "AI_DERIVED_DEMO"

    def test_ai_source_distinct_from_osm(self):
        ai_r  = client.get("/api/v1/features")
        osm_r = client.get("/api/v1/osm/bhopal/buildings")
        assert ai_r.json()["_source"] != osm_r.json().get("_source") and \
               ai_r.json()["_source"] != osm_r.json().get("metadata", {}).get("_source")

    def test_ai_source_not_official_reference(self):
        r = client.get("/api/v1/features")
        assert r.json()["_source"] != "OFFICIAL_REFERENCE"

    def test_ai_features_have_confidence(self):
        r = client.get("/api/v1/features")
        for feat in r.json()["features"]:
            conf = feat["properties"].get("confidence")
            assert conf is not None
            assert 0.0 <= conf <= 1.0

    def test_ai_feature_filter_by_parcel(self):
        r = client.get("/api/v1/features?parcel_id=parcel-bpl-001")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["features"][0]["properties"]["associated_parcel_id"] == "parcel-bpl-001"


# =============================================================================
# Raw Dataset Protection
# =============================================================================

class TestRawDataProtection:
    def test_dataset_dir_not_reachable_via_tiles(self):
        """Tiles endpoint must not serve Dataset/ files"""
        # Non-integer z means the int validator rejects it first
        r = client.get("/api/v1/tiles/bhopal/18/../../../Dataset/Drone-Images/BHOPAL/00_00.tiff")
        assert r.status_code in (404, 422)

    def test_india_pbf_not_served(self):
        """The 1.7GB India PBF must never be served"""
        r = client.get("/api/v1/osm/bhopal/india-260905")
        assert r.status_code == 404

    def test_cog_not_served_via_osm(self):
        r = client.get("/api/v1/osm/bhopal/bhopal_cog")
        assert r.status_code == 404

    def test_raw_tiff_not_in_osm_allowlist(self):
        r = client.get("/api/v1/osm/bhopal/00_00")
        assert r.status_code == 404

    def test_env_file_not_accessible(self):
        """Environment files must not be reachable"""
        r = client.get("/api/v1/osm/bhopal/.env")
        assert r.status_code == 404

    def test_osm_bbox_cache_not_served(self):
        r = client.get("/api/v1/osm/bhopal/_bbox_nodes")
        assert r.status_code == 404
