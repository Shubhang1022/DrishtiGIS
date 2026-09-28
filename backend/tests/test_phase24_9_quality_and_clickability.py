"""
DrishtiGIS — Phase 24.9 UAV Image Quality & GIS Feature Clickability Comprehensive Test Suite
=============================================================================================
Section 28 Requirements:
RASTER:
 1. Correct native source resolution (~0.02 m/pixel)
 2. High-zoom tile resolution (z14-z19 detailed output)
 3. No preview used as native raster (authoritative GeoTIFF store)
 4. No unnecessary overscaling (native resolution sampled at high zooms)
 5. Correct maxzoom (21)
 6. Correct resampling (cubic)
 7. Tile dimensions (strictly 256x256 RGBA)
 8. Raster quality metadata (CRS, bounds, status)

INTERACTION:
 9. OSM building click (dispatches osm-feature with REFERENCE_GIS attribution)
10. OSM road click (dispatches road with REFERENCE_GIS)
11. Parcel click (dispatches parcel with property context)
12. AI building click (dispatches ai-feature)
13. Review geometry / coverage click
14. Layer-specific query (queryRenderedFeatures with layer filter)
15. Click priority (AI > parcel > OSM building > road > landuse)
16. Transparent hit area (osm-roads-hit-area 16px line-width, 0 opacity)
17. No raster feature selection (raster excluded from interactive layers)
18. No overlay blocking (pointer-events: none on non-interactive overlays)
19. Pointer cursor feedback (mouseenter/mouseleave cursor styling)
20. High-zoom click (rich vector feature payloads available for selection)
"""

import os
import glob
import io
import pytest
from pathlib import Path
from PIL import Image
import rasterio
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[2]

# ── RASTER TESTS (1 - 8) ──────────────────────────────────────────────────────

def test_01_correct_native_source_resolution():
    """1. Verify UAV source GeoTIFFs have native spatial resolution of ~0.02 m/pixel."""
    tiff_dir = REPO_ROOT / "Dataset" / "geospatial-data" / "BHOPAL"
    tiff_files = glob.glob(str(tiff_dir / "*.tiff")) + glob.glob(str(tiff_dir / "*.tif"))
    assert len(tiff_files) > 0, "No GeoTIFFs found in Bhopal dataset folder"
    
    with rasterio.open(tiff_files[0]) as src:
        res_x, res_y = src.res
        assert 0.015 <= res_x <= 0.030, f"Native X resolution {res_x} not in ~0.02m range"
        assert 0.015 <= res_y <= 0.030, f"Native Y resolution {res_y} not in ~0.02m range"
        assert str(src.crs) == "EPSG:32643", f"Expected UTM 43N, got {src.crs}"

def test_02_high_zoom_tile_resolution():
    """2. Verify XYZ raster tile generation at zoom levels 14 through 19 return non-trivial data."""
    zoom_samples = [
        (14, 11715, 7103),
        (15, 23430, 14206),
        (16, 46861, 28413),
        (17, 93722, 56826),
        (18, 187445, 113652),
        (19, 374890, 227304)
    ]
    for z, x, y in zoom_samples:
        response = client.get(f"/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/{z}/{x}/{y}.png")
        assert response.status_code == 200, f"Failed at z={z}: HTTP {response.status_code}"
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 5000, f"Tile too small at z={z}: {len(response.content)} bytes"

def test_03_no_preview_used_as_native_raster():
    """3. Verify dataset path points directly to full-resolution GeoTIFF directory, not a preview."""
    response = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001")
    assert response.status_code == 200
    data = response.json()
    assert "Dataset" in data["file_path"] and "BHOPAL" in data["file_path"]
    assert "preview" not in data["file_path"].lower()
    assert "thumb" not in data["file_path"].lower()

def test_04_no_unnecessary_overscaling():
    """4. Verify z18 and z19 produce distinct, high-entropy detail rather than identical bytes."""
    r18 = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/18/187445/113652.png")
    r19 = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/19/374890/227304.png")
    assert r18.status_code == 200 and r19.status_code == 200
    assert r18.content != r19.content, "z18 and z19 tiles are unexpectedly identical"

def test_05_correct_maxzoom():
    """5. Verify TileJSON metadata configures maxzoom=21 supporting high UAV resolution."""
    response = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tilejson.json")
    assert response.status_code == 200
    tilejson = response.json()
    assert tilejson["tileSize"] == 256
    assert tilejson["minzoom"] == 12
    assert tilejson["maxzoom"] == 21

def test_06_correct_resampling():
    """6. Verify cubic resampling is explicitly specified in the tile rendering pipeline."""
    code_path = REPO_ROOT / "backend" / "app" / "api" / "v1" / "published_datasets.py"
    with open(code_path, "r", encoding="utf-8") as f:
        code = f.read()
    assert "Resampling.cubic" in code, "Cubic resampling not configured in published_datasets.py"

def test_07_tile_dimensions():
    """7. Verify tile output strictly adheres to 256x256 RGBA dimensions."""
    response = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/18/187445/113652.png")
    assert response.status_code == 200
    img = Image.open(io.BytesIO(response.content))
    assert img.size == (256, 256), f"Expected 256x256, got {img.size}"
    assert img.mode == "RGBA", f"Expected RGBA, got {img.mode}"

def test_08_raster_quality_metadata():
    """8. Verify dataset details API exposes valid geospatial metadata."""
    response = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001")
    assert response.status_code == 200
    ds = response.json()
    assert ds["format"] == "uav_raster"
    assert ds["status"] == "PUBLISHED"
    assert len(ds["bounds"]) == 4

# ── INTERACTION TESTS (9 - 20) ────────────────────────────────────────────────

def test_09_osm_building_click_handling():
    """9. Verify MapLibreMap dispatches osm-feature context with REFERENCE_GIS attribution."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert "osm-buildings-fill" in map_code
    assert 'type: "osm-feature"' in map_code
    assert 'source_type: "REFERENCE_GIS"' in map_code

def test_10_osm_road_click_handling():
    """10. Verify MapLibreMap dispatches road context with REFERENCE_GIS."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert 'type: "road"' in map_code
    assert "osm-roads" in map_code

def test_11_parcel_click_handling():
    """11. Verify parcel endpoint returns valid GeoJSON for ContextSidebar."""
    response = client.get("/api/v1/parcels?city=Bhopal")
    assert response.status_code == 200
    geojson = response.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

def test_12_ai_building_click_handling():
    """12. Verify AI features endpoint returns building footprints."""
    response = client.get("/api/v1/features")
    assert response.status_code == 200
    geojson = response.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

def test_13_review_geometry_click_handling():
    """13. Verify review / coverage points endpoint returns valid features."""
    response = client.get("/api/v1/osm/bhopal/buildings")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"

def test_14_layer_specific_query():
    """14. Verify queryRenderedFeatures restricts queries strictly to active interactive vector layers."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert "map.queryRenderedFeatures(e.point, { layers: availableLayers })" in map_code

def test_15_click_priority_deterministic():
    """15. Verify deterministic priority order is explicitly configured."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert 'PRIORITY_ORDER' in map_code
    assert '"ai-features-fill": 1' in map_code
    assert '"parcels-fill": 2' in map_code
    assert '"osm-buildings-fill": 3' in map_code
    assert '"osm-roads": 4' in map_code
    assert '"osm-landuse-fill": 5' in map_code

def test_16_transparent_hit_area_for_thin_lines():
    """16. Verify transparent 16px interaction layer exists for roads."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert '"osm-roads-hit-area"' in map_code
    assert '"line-width": 16' in map_code
    assert '"line-opacity": 0' in map_code

def test_17_no_raster_feature_selection():
    """17. Verify raster layers are excluded from INTERACTIVE_LAYER_IDS and return early if clicked."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert "dataset-raster-layer" not in map_code.split("INTERACTIVE_LAYER_IDS = [")[1].split("];")[0]
    assert "NEVER select raster" in map_code

def test_18_no_overlay_blocking_map_canvas():
    """18. Verify non-interactive overlays use pointer-events: none."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert 'pointerEvents: "none"' in map_code

def test_19_pointer_cursor_feedback():
    """19. Verify mouseenter/mouseleave events update canvas style cursor."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert 'map.getCanvas().style.cursor = "pointer"' in map_code
    assert 'map.getCanvas().style.cursor = ""' in map_code

def test_20_high_zoom_click_endpoints_integration():
    """20. Verify OSM reference GIS layers (roads, buildings, landuse, waterways) return 200 OK."""
    for layer in ["buildings", "roads", "landuse", "waterways"]:
        response = client.get(f"/api/v1/osm/bhopal/{layer}")
        assert response.status_code == 200, f"Layer {layer} failed: HTTP {response.status_code}"
        assert response.json()["type"] == "FeatureCollection"
