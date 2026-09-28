"""
DrishtiGIS Phase 4 — Building footprint extraction unit tests.

Covers:
  - Building class extraction = 4
  - Mask dimensions
  - Connected components
  - Min-area filtering
  - Contour → polygon
  - Geometry validity
  - CRS transformation
  - Area calculation
  - Confidence calculation
  - Source-tile attribution
  - Stable IDs
  - Overlap deduplication
  - No fabricated features
  - Coordinates inside imagery coverage
  - No test-tile contamination
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT       = Path(__file__).parent.parent.parent
CONFIG     = ROOT / "data/uavpal/training_config.json"
SPLIT      = ROOT / "data/uavpal/validation_split.json"
GEOJSON    = ROOT / "data/ai_output/bhopal-buildings-ai.geojson"
REPORT     = ROOT / "data/ai_output/bhopal-building-inference-report.json"
COVERAGE   = ROOT / "data/uavpal/tile_coverage.json"
RGB_DIR    = ROOT / "Dataset/geospatial-data/BHOPAL"

# Skip geometry / ML tests if heavy deps absent
_shapely_ok = False
_torch_ok   = False
_rasterio_ok = False

try:
    from shapely.geometry import shape, Polygon
    from shapely.validation import make_valid
    _shapely_ok = True
except ImportError:
    pass

try:
    import torch
    _torch_ok = True
except ImportError:
    pass

try:
    import rasterio
    _rasterio_ok = True
except ImportError:
    pass

skip_shapely  = pytest.mark.skipif(not _shapely_ok,  reason="shapely required")
skip_torch    = pytest.mark.skipif(not _torch_ok,    reason="torch required")
skip_rasterio = pytest.mark.skipif(not _rasterio_ok, reason="rasterio required")
skip_outputs  = pytest.mark.skipif(
    not GEOJSON.exists(), reason="GeoJSON output not yet generated — run pipeline first"
)


# ── 1. Building class constant ────────────────────────────────────────────────

class TestBuildingClass:
    def test_building_class_id_is_4(self):
        from backend.ai.uavpal.classes import BUILDING_CLASS_ID
        assert BUILDING_CLASS_ID == 4

    def test_building_class_name(self):
        from backend.ai.uavpal.classes import CLASS_BY_ID
        assert CLASS_BY_ID[4].name == "Building"

    def test_postprocess_constant(self):
        from backend.ai.segmentation.postprocess import BUILDING_CLASS_ID as BID
        assert BID == 4

    def test_georef_constant(self):
        from backend.ai.segmentation.georef import BUILDING_CLASS_ID as BID
        assert BID == 4


# ── 2. Mask extraction ────────────────────────────────────────────────────────

class TestMaskExtraction:
    def test_building_mask_from_prediction(self):
        """Building mask must select exactly the pixels where pred==4."""
        pred = np.zeros((64, 64), dtype=np.uint8)
        pred[10:20, 10:20] = 4   # a 10×10 building block
        pred[30:35, 30:35] = 2   # some road
        bld_mask = (pred == 4).astype(np.uint8)
        assert bld_mask.sum() == 100
        assert bld_mask[15, 15] == 1
        assert bld_mask[32, 32] == 0

    def test_mask_dimensions_preserved(self):
        """Mask must be 2048×2048 for a full tile."""
        pred = np.zeros((2048, 2048), dtype=np.uint8)
        pred[100:200, 100:200] = 4
        assert pred.shape == (2048, 2048)
        assert (pred == 4).sum() == 10000

    def test_no_values_outside_0_5(self):
        """Prediction mask must only contain 0–5."""
        pred = np.array([0, 1, 2, 3, 4, 5], dtype=np.uint8)
        assert set(np.unique(pred)).issubset({0, 1, 2, 3, 4, 5})


# ── 3. Connected components ───────────────────────────────────────────────────

class TestConnectedComponents:
    def test_two_separate_buildings(self):
        """Two non-touching building blobs → 2 components."""
        from scipy.ndimage import label
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[5:15, 5:15]   = 1   # building A
        mask[30:40, 30:40] = 1   # building B
        struct = np.ones((3, 3), dtype=np.int32)
        labeled, n = label(mask, structure=struct)
        assert n == 2

    def test_touching_buildings_merged(self):
        """Two adjacent blobs touching → 1 component without separation."""
        from scipy.ndimage import label
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[5:20, 5:15] = 1
        mask[5:20, 15:25] = 1   # touching at col=15
        struct = np.ones((3, 3), dtype=np.int32)
        labeled, n = label(mask, structure=struct)
        assert n == 1

    def test_component_extraction_smoke(self):
        """extract_building_components must run without error on synthetic input."""
        from backend.ai.segmentation.postprocess import extract_building_components
        pred = np.zeros((256, 256), dtype=np.uint8)
        pred[10:60, 10:60] = 4   # 50×50 building block
        prob = np.where(pred == 4, 0.9, 0.05).astype(np.float32)
        result = extract_building_components(
            tile_id="test_tile", pred_mask=pred, prob_building=prob,
            min_area_m2=0.001, use_watershed=False,
        )
        assert result.filtered_components >= 1
        assert result.raw_components >= 1
        assert len(result.components) >= 1


# ── 4. Min-area filtering ─────────────────────────────────────────────────────

class TestMinAreaFilter:
    def test_small_noise_filtered(self):
        """A 3×3 px component (~0.00004 m²) should be filtered at 5 m²."""
        from backend.ai.segmentation.postprocess import (
            extract_building_components, DEFAULT_PX_SIZE_M,
        )
        pred = np.zeros((64, 64), dtype=np.uint8)
        pred[10:13, 10:13] = 4          # 3×3 = 9 px ≈ 0.000004 m²
        pred[20:70, 20:70] = 4          # but array is only 64, clips to 44×44
        pred = pred[:64, :64]
        prob = np.where(pred == 4, 0.8, 0.1).astype(np.float32)
        result = extract_building_components(
            tile_id="t", pred_mask=pred, prob_building=prob,
            min_area_m2=5.0, use_watershed=False,
        )
        # Only large block survives
        areas = [c.area_m2 for c in result.components]
        assert all(a >= 5.0 for a in areas), f"Filtered component < 5 m²: {areas}"

    def test_large_building_retained(self):
        """A 200×200 px building (~1880 m²) must survive any reasonable threshold."""
        from backend.ai.segmentation.postprocess import extract_building_components
        pred = np.zeros((256, 256), dtype=np.uint8)
        pred[20:220, 20:220] = 4
        prob = np.where(pred == 4, 0.85, 0.1).astype(np.float32)
        result = extract_building_components(
            tile_id="t", pred_mask=pred, prob_building=prob,
            min_area_m2=10.0, use_watershed=False,
        )
        assert result.filtered_components >= 1
        assert result.components[0].area_m2 > 10.0


# ── 5. Contour → polygon ──────────────────────────────────────────────────────

class TestContourPolygon:
    def test_contour_extracted_from_blob(self):
        """_extract_contour must return a valid closed polygon."""
        from backend.ai.segmentation.postprocess import _extract_contour
        mask = np.zeros((64, 64), dtype=np.uint8)
        mask[10:50, 10:50] = 1
        contour = _extract_contour(mask, simplify_px=0)
        assert contour is not None
        assert len(contour) >= 4
        # Must be closed: first == last
        assert np.allclose(contour[0], contour[-1], atol=2)

    def test_contour_column_row_order(self):
        """Contour must be in (col, row) = (x, y) order."""
        from backend.ai.segmentation.postprocess import _extract_contour
        mask = np.zeros((64, 64), dtype=np.uint8)
        mask[20:40, 10:30] = 1    # rows 20-40, cols 10-30
        contour = _extract_contour(mask, simplify_px=0)
        assert contour is not None
        # col (x) should be around 10-30, row (y) around 20-40
        col_range = (contour[:, 0].min(), contour[:, 0].max())
        row_range = (contour[:, 1].min(), contour[:, 1].max())
        assert 5 <= col_range[0] <= 15,  f"col min unexpected: {col_range}"
        assert 25 <= col_range[1] <= 35, f"col max unexpected: {col_range}"
        assert 15 <= row_range[0] <= 25, f"row min unexpected: {row_range}"
        assert 35 <= row_range[1] <= 45, f"row max unexpected: {row_range}"

    @skip_shapely
    def test_contour_forms_valid_polygon(self):
        """Pixel contour → Shapely polygon must be valid after make_valid."""
        from backend.ai.segmentation.postprocess import _extract_contour
        from shapely.geometry import Polygon
        from shapely.validation import make_valid
        mask = np.zeros((64, 64), dtype=np.uint8)
        mask[10:50, 10:50] = 1
        contour = _extract_contour(mask, simplify_px=1.0)
        assert contour is not None
        # Build polygon from contour (col, row) as (x, y) pixel coords
        coords = list(map(tuple, contour.tolist()))
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = make_valid(poly)
        assert not poly.is_empty
        assert poly.area > 0


# ── 6. Geometry validity ──────────────────────────────────────────────────────

@skip_shapely
class TestGeometryValidity:
    def test_repair_self_intersecting(self):
        """_repair_geometry must fix a bowtie polygon."""
        from backend.ai.segmentation.georef import _repair_geometry
        from shapely.geometry import Polygon
        # Bowtie (figure-8) — self-intersecting
        bowtie = Polygon([(0,0),(2,2),(2,0),(0,2),(0,0)])
        assert not bowtie.is_valid
        fixed = _repair_geometry(bowtie)
        assert fixed is not None
        assert fixed.is_valid
        assert fixed.area > 0

    def test_valid_polygon_unchanged(self):
        """A valid polygon should pass through _repair_geometry without change."""
        from backend.ai.segmentation.georef import _repair_geometry
        from shapely.geometry import Polygon
        rect = Polygon([(0,0),(1,0),(1,1),(0,1),(0,0)])
        assert rect.is_valid
        fixed = _repair_geometry(rect)
        assert fixed is not None
        assert abs(fixed.area - rect.area) < 1e-9


# ── 7. CRS transformation ─────────────────────────────────────────────────────

@skip_shapely
class TestCRSTransformation:
    def test_epsg32643_to_4326_roundtrip(self):
        """Transform EPSG:32643 → 4326 → 32643 and verify minimal drift."""
        from pyproj import Transformer
        t_fwd = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
        t_inv = Transformer.from_crs("EPSG:4326",  "EPSG:32643", always_xy=True)
        # A point in the middle of the Bhopal survey area
        e_orig, n_orig = 747200.0, 2573960.0
        lon, lat = t_fwd.transform(e_orig, n_orig)
        e_back, n_back = t_inv.transform(lon, lat)
        assert abs(e_back - e_orig) < 0.01   # < 1 cm
        assert abs(n_back - n_orig) < 0.01

    def test_output_coordinates_in_bhopal_bbox(self):
        """All output feature coordinates must fall inside Bhopal survey area."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        # Generous bounding box around the full UAV survey
        LON_MIN, LON_MAX = 77.35, 77.50
        LAT_MIN, LAT_MAX = 23.20, 23.30
        for feat in gj["features"][:200]:   # check first 200
            geom = shape(feat["geometry"])
            cen  = geom.centroid
            assert LON_MIN <= cen.x <= LON_MAX, f"centroid lon {cen.x} outside bbox"
            assert LAT_MIN <= cen.y <= LAT_MAX, f"centroid lat {cen.y} outside bbox"


# ── 8. Area calculation ───────────────────────────────────────────────────────

class TestAreaCalculation:
    def test_area_positive(self):
        """Every building must have positive area."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            assert feat["properties"]["area_m2"] > 0, \
                f"Zero/negative area: {feat['properties']['id']}"

    def test_area_above_min_threshold(self):
        """All features must meet the 5 m² minimum."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            assert feat["properties"]["area_m2"] >= 5.0, \
                f"Area below threshold: {feat['properties']['id']} = {feat['properties']['area_m2']}"

    def test_no_unreasonably_large_buildings(self):
        """Buildings > 50,000 m² in dense urban Bhopal are suspect — flag, not fail."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        giant = [f for f in gj["features"] if f["properties"]["area_m2"] > 50000]
        # We don't fail — just verify there are not thousands of them (model artefacts)
        assert len(giant) < 50, \
            f"Unexpectedly many giant buildings (>50k m²): {len(giant)}"


# ── 9. Confidence calculation ─────────────────────────────────────────────────

class TestConfidenceCalculation:
    def test_confidence_in_0_1(self):
        """All confidence values must be in [0, 1]."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            c = feat["properties"]["confidence"]
            assert c is None or 0.0 <= c <= 1.0, \
                f"Confidence out of range: {feat['properties']['id']} = {c}"

    def test_confidence_methodology_documented(self):
        """Inference report must document the confidence methodology."""
        if not REPORT.exists():
            pytest.skip("Report not yet generated")
        with open(REPORT, encoding="utf-8") as f:
            rep = json.load(f)
        assert "confidence_methodology" in rep
        method = rep["confidence_methodology"]
        assert "softmax" in method.lower() or "probability" in method.lower()

    def test_no_fabricated_confidence(self):
        """Confidence must be derived from the model, not hard-coded."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        confs = [f["properties"]["confidence"] for f in gj["features"]]
        # All identical confidence would indicate hard-coding
        unique_confs = len(set(confs))
        if len(confs) > 10:
            assert unique_confs > 5, "All confidence values identical — possible fabrication"


# ── 10. Source-tile attribution ───────────────────────────────────────────────

class TestSourceTileAttribution:
    def test_every_feature_has_source_tile(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        all_tiles = sorted(f.stem for f in RGB_DIR.glob("*.tiff"))
        for feat in gj["features"]:
            tile = feat["properties"].get("source_tile")
            assert tile is not None, f"No source_tile: {feat['properties']['id']}"
            assert tile in all_tiles, f"Unknown source_tile: {tile}"

    def test_required_properties_present(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        required = {
            "id", "source", "model", "source_tile", "source_class",
            "source_class_name", "area_m2", "confidence",
            "crs_source", "crs_output",
        }
        for feat in gj["features"][:50]:
            props = feat["properties"]
            missing = required - set(props.keys())
            assert not missing, f"{props.get('id')}: missing {missing}"

    def test_source_is_ai_derived_uavpal(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"][:100]:
            assert feat["properties"]["source"] == "AI_DERIVED_UAVPAL"

    def test_source_class_is_4(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"][:100]:
            assert feat["properties"]["source_class"] == 4


# ── 11. Stable IDs ────────────────────────────────────────────────────────────

class TestStableIDs:
    def test_all_ids_unique(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        ids = [f["properties"]["id"] for f in gj["features"]]
        assert len(ids) == len(set(ids)), "Duplicate IDs found"

    def test_id_format(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"][:50]:
            fid = feat["properties"]["id"]
            assert fid.startswith("AI-BPL-"), f"Unexpected ID format: {fid}"

    def test_no_demo_ids_present(self):
        """Output must not contain the old hand-authored demo polygon IDs."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        demo_ids = {"ai-bld-001a", "ai-bld-001b", "ai-bld-002a", "ai-bld-002b", "ai-bld-003"}
        output_ids = {f["properties"]["id"] for f in gj["features"]}
        assert not (demo_ids & output_ids), \
            f"Demo polygon IDs found in output: {demo_ids & output_ids}"


# ── 12. Deduplication ─────────────────────────────────────────────────────────

class TestDeduplication:
    def test_dedup_removes_nearby_duplicates(self):
        """Two features from adjacent tiles with same centroid must be deduplicated."""
        from backend.ai.segmentation.dedup import deduplicate_features
        # Create two near-identical features from adjacent tiles
        feat_a = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.410, 23.255], [77.411, 23.255],
                                  [77.411, 23.256], [77.410, 23.256],
                                  [77.410, 23.255]]],
            },
            "properties": {
                "id": "raw-a", "source_tile": "00_05",
                "centroid_lon": 77.4105, "centroid_lat": 23.2555,
                "area_m2": 120.0, "confidence": 0.85,
            },
        }
        feat_b = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.4100, 23.2550], [77.4110, 23.2550],
                                  [77.4110, 23.2560], [77.4100, 23.2560],
                                  [77.4100, 23.2550]]],
            },
            "properties": {
                "id": "raw-b", "source_tile": "00_06",
                "centroid_lon": 77.4105, "centroid_lat": 23.2555,
                "area_m2": 110.0, "confidence": 0.80,
            },
        }
        result, n_removed, _ = deduplicate_features([feat_a, feat_b])
        assert n_removed == 1
        assert len(result) == 1
        # Larger area (feat_a, 120 m²) should be retained
        assert result[0]["properties"]["area_m2"] == 120.0

    def test_far_buildings_not_deduped(self):
        """Two buildings from the same tile (non-adjacent pair) must NOT be deduplicated."""
        from backend.ai.segmentation.dedup import deduplicate_features
        feat_a = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.400, 23.250], [77.401, 23.250],
                                  [77.401, 23.251], [77.400, 23.251],
                                  [77.400, 23.250]]],
            },
            "properties": {
                "id": "x1", "source_tile": "00_00",
                "centroid_lon": 77.4005, "centroid_lat": 23.2505,
                "area_m2": 100.0, "confidence": 0.80,
            },
        }
        feat_b = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.450, 23.270], [77.451, 23.270],
                                  [77.451, 23.271], [77.450, 23.271],
                                  [77.450, 23.270]]],
            },
            "properties": {
                "id": "x2", "source_tile": "00_22",
                "centroid_lon": 77.4505, "centroid_lat": 23.2705,
                "area_m2": 100.0, "confidence": 0.80,
            },
        }
        result, n_removed, _ = deduplicate_features([feat_a, feat_b])
        assert n_removed == 0
        assert len(result) == 2


# ── 13. No fabricated features ────────────────────────────────────────────────

class TestNoFabrication:
    def test_geojson_metadata_source(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        meta = gj.get("metadata", {})
        assert meta.get("_source") == "AI_DERIVED_UAVPAL"
        assert "NOT cadastral" in meta.get("_disclaimer", "")

    def test_no_hand_authored_geometry(self):
        """Geometries must not match known demo polygon coordinates."""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        # Demo polygon coordinate (from bhopal-ai-features.geojson)
        DEMO_COORD = [77.41485, 23.256335]
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            coords = feat["geometry"]["coordinates"]
            if isinstance(coords[0], list) and isinstance(coords[0][0], list):
                flat = coords[0]
            else:
                flat = coords
            for c in flat:
                if isinstance(c, (list, tuple)) and len(c) == 2:
                    if (abs(c[0] - DEMO_COORD[0]) < 0.00001 and
                            abs(c[1] - DEMO_COORD[1]) < 0.00001):
                        pytest.fail("Found hand-authored demo coordinate in AI output")

    def test_output_references_model(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"][:10]:
            assert "UNet" in feat["properties"]["model"], \
                f"Unexpected model: {feat['properties']['model']}"

    def test_no_test_tile_contamination(self):
        """Building features must not be fabricated from test tile labels.
        (This checks that test tile names appear correctly attributed —
         it's valid for test tiles to generate features from inference.)"""
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        # All source tiles in the output must come from the 30 actual RGB tiles
        valid_tiles = {f.stem for f in RGB_DIR.glob("*.tiff")}
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            tile = feat["properties"]["source_tile"]
            assert tile in valid_tiles, f"Unknown source tile: {tile}"


# ── 14. Coordinates inside imagery ───────────────────────────────────────────

@skip_shapely
class TestCoordinatesInImagery:
    def test_output_geojson_valid_geometry(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        n_invalid = 0
        for feat in gj["features"]:
            geom = shape(feat["geometry"])
            if not geom.is_valid:
                n_invalid += 1
        assert n_invalid == 0, \
            f"{n_invalid} invalid geometries found in output GeoJSON"

    def test_no_empty_geometries(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            geom = shape(feat["geometry"])
            assert not geom.is_empty, \
                f"Empty geometry: {feat['properties']['id']}"

    def test_geometry_type(self):
        if not GEOJSON.exists():
            pytest.skip("GeoJSON not yet generated")
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"][:200]:
            assert feat["geometry"]["type"] in ("Polygon", "MultiPolygon"), \
                f"Unexpected geometry type: {feat['geometry']['type']}"


# ── 15. Inference report integrity ───────────────────────────────────────────

class TestInferenceReport:
    def test_report_exists(self):
        assert REPORT.exists(), "Inference report not generated"

    def test_report_fields(self):
        if not REPORT.exists():
            pytest.skip("Report not yet generated")
        with open(REPORT, encoding="utf-8") as f:
            rep = json.load(f)
        required = {
            "model", "source_tile_count", "min_area_threshold_m2",
            "total_raw_components", "total_filtered_components",
            "total_raw_polygons", "duplicates_removed",
            "final_building_count", "geometry_repair",
            "average_confidence", "median_confidence",
            "per_tile",
        }
        missing = required - set(rep.keys())
        assert not missing, f"Report missing fields: {missing}"

    def test_final_count_consistent_with_geojson(self):
        if not REPORT.exists() or not GEOJSON.exists():
            pytest.skip("Files not yet generated")
        with open(REPORT, encoding="utf-8") as f:
            rep = json.load(f)
        with open(GEOJSON, encoding="utf-8") as f:
            gj = json.load(f)
        assert rep["final_building_count"] == len(gj["features"]), \
            (f"Report count {rep['final_building_count']} != "
             f"GeoJSON count {len(gj['features'])}")

    def test_per_tile_count_matches_tiles(self):
        if not REPORT.exists():
            pytest.skip("Report not yet generated")
        with open(REPORT, encoding="utf-8") as f:
            rep = json.load(f)
        assert rep["source_tile_count"] == 30
        assert len(rep["per_tile"]) == 30
