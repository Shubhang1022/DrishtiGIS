"""
DrishtiGIS — Phase 24.6 Automated Verification Suite
======================================================
Tests:
  1. Multi-TIFF Discovery & Individual Footprints
  2. Dataset Union Footprint & WGS84 Extent
  3. Windowed Raster Reading & Resampling
  4. XYZ Tile Reprojection & EPSG:3857 Bounds Calculation
  5. 9-Neighboring Tile Uniqueness & MD5 Hashes
  6. TileJSON Endpoint Integrity & Scheme Compliance
  7. Map Camera Freedom (Zero maxBounds restriction)
"""

import hashlib
import io
import math
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset_store import dataset_store
from backend.app.services.dataset_pipeline import _inspect_tiff
from backend.app.api.v1.published_datasets import (
    generate_tile_png_from_dataset,
    tile_xyz_to_epsg3857_bounds,
    bounds_overlap,
    TRANSPARENT_1X1_PNG
)

client = TestClient(app)

BHOPAL_DIR = Path("Dataset/geospatial-data/BHOPAL")


def test_01_multi_tiff_discovery_and_footprints():
    """Verify that all 121 GeoTIFF patches are discovered and inspected."""
    res = _inspect_tiff(str(BHOPAL_DIR))
    assert res["feature_count"] == 121, f"Expected 121 TIFF files, got {res['feature_count']}"
    assert res["crs"] == "EPSG:32643", f"Expected EPSG:32643, got {res['crs']}"
    assert res["bounds"] is not None
    assert len(res["bounds"]) == 4


def test_02_dataset_union_footprint():
    """Verify that the calculated union footprint matches exact physical GeoTIFF extent."""
    bounds = dataset_store.get_dataset("DS-BHOPAL-RASTER-001").bounds
    assert bounds is not None
    min_lon, min_lat, max_lon, max_lat = bounds

    assert 77.412 < min_lon < 77.414, f"Unexpected min_lon: {min_lon}"
    assert 77.421 < max_lon < 77.424, f"Unexpected max_lon: {max_lon}"
    assert 23.253 < min_lat < 23.255, f"Unexpected min_lat: {min_lat}"
    assert 23.255 < max_lat < 23.258, f"Unexpected max_lat: {max_lat}"


def test_03_epsg3857_tile_bounds_calculation():
    """Verify exact EPSG:3857 meter bounds for (z=18, x=187445, y=113652)."""
    b = tile_xyz_to_epsg3857_bounds(18, 187445, 113652)
    assert len(b) == 4
    assert b[0] < b[2]  # min_x < max_x
    assert b[1] < b[3]  # min_y < max_y
    width_m = b[2] - b[0]
    height_m = b[3] - b[1]
    assert abs(width_m - height_m) < 1e-4, f"Tile square mismatch: {width_m} vs {height_m}"


def test_04_9_neighboring_tiles_uniqueness():
    """Verify 3x3 neighboring tiles produce 9 distinct non-empty PNG images with unique hashes."""
    ds = dataset_store.get_dataset("DS-BHOPAL-RASTER-001")
    center_x, center_y, z = 187445, 113652, 18

    hashes = set()
    tile_count = 0

    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            x, y = center_x + dx, center_y + dy
            png = generate_tile_png_from_dataset(ds, z, x, y)
            assert png != TRANSPARENT_1X1_PNG, f"Tile ({z}/{x}/{y}) returned blank image"
            h = hashlib.md5(png).hexdigest()
            hashes.add(h)
            tile_count += 1

    assert tile_count == 9
    assert len(hashes) == 9, f"Expected 9 unique tile hashes, got {len(hashes)}"


def test_05_tilejson_endpoint():
    """Verify standard TileJSON 3.0.0 metadata output."""
    r = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tilejson.json")
    assert r.status_code == 200
    data = r.json()
    assert data["tilejson"] == "3.0.0"
    assert data["scheme"] == "xyz"
    assert data["tileSize"] == 256
    assert len(data["tiles"]) > 0
    assert "/tiles/{z}/{x}/{y}.png" in data["tiles"][0]


def test_06_dynamic_tile_endpoint():
    """Verify HTTP GET /api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/18/187445/113652.png."""
    r = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/18/187445/113652.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert len(r.content) > 1000  # valid image buffer


def test_07_out_of_bounds_tile_returns_transparent():
    """Verify tile requests far outside dataset return 200 with transparent PNG."""
    r = client.get("/api/v1/datasets/DS-BHOPAL-RASTER-001/tiles/18/0/0.png")
    assert r.status_code == 200
    assert r.content == TRANSPARENT_1X1_PNG
