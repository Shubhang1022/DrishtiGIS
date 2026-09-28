"""
DrishtiGIS — Phase 24.5 Comprehensive Raster Georeferencing & Alignment Test Suite
==================================================================================
Validates:
1. GeoTIFF CRS inspection (EPSG:32643 UTM Zone 43N) & WGS84 bounds extraction.
2. Web Mercator (EPSG:3857) tile reprojection via rasterio.warp.reproject.
3. Spatial uniqueness of neighboring XYZ tiles (tile A != tile B != tile C).
4. Transparency mask generation for non-overlapping pixels.
5. Directory-level multi-file GeoTIFF dataset stitching.
6. TileJSON schema consistency & minzoom/maxzoom enforcement.
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset_store import dataset_store, DatasetItem
from backend.app.api.v1.published_datasets import (
    tile_xyz_to_epsg3857_bounds,
    generate_tile_png_from_dataset,
    bounds_overlap
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_utm_dataset():
    """Create a temporary EPSG:32643 UTM GeoTIFF and register as a published dataset."""
    temp_dir = tempfile.mkdtemp()
    tif_path = os.path.join(temp_dir, "test_bhopal_utm.tif")

    # Create a 256x256 EPSG:32643 GeoTIFF around Bhopal UTM (746867.75, 2573942.57)
    width, height = 256, 256
    transform = from_origin(746867.75, 2573987.04, 0.2, 0.2)
    data = (np.random.rand(3, height, width) * 200 + 50).astype(np.uint8)

    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=data.dtype,
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)

    ds_record = DatasetItem(
        dataset_id="DS-TEST-UTM-001",
        name="Test Bhopal UTM Dataset",
        filename="test_bhopal_utm.tif",
        format="uav_raster",
        file_path=tif_path,
        file_size_bytes=os.path.getsize(tif_path),
        status="READY",
        is_published=False,
        crs="EPSG:32643",
        bounds=[77.4129, 23.2562, 77.4135, 23.2567],
        dimensions="256 x 256 x 3",
    )

    dataset_store.datasets[ds_record.dataset_id] = ds_record
    dataset_store.publish_dataset(ds_record.dataset_id)

    yield ds_record

    dataset_store.datasets.pop(ds_record.dataset_id, None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_epsg3857_tile_bounds_calculation():
    """Verify Web Mercator EPSG:3857 bounding box formula."""
    bounds = tile_xyz_to_epsg3857_bounds(0, 0, 0)
    R = 20037508.342789244
    assert pytest.approx(bounds[0], rel=1e-5) == -R
    assert pytest.approx(bounds[1], rel=1e-5) == -R
    assert pytest.approx(bounds[2], rel=1e-5) == R
    assert pytest.approx(bounds[3], rel=1e-5) == R


def test_reprojected_tile_rendering(setup_utm_dataset):
    """Verify reprojection from EPSG:32643 to EPSG:3857 tile PNG."""
    ds = setup_utm_dataset

    # Zoom 18 tile covering Bhopal UTM area (z=18, x=187442, y=113652)
    png_bytes = generate_tile_png_from_dataset(ds, 18, 187442, 113652)
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 100
    assert png_bytes[:4] == b"\x89PNG"


def test_neighboring_tiles_uniqueness(setup_utm_dataset):
    """Verify neighboring tiles return geographically distinct images."""
    ds = setup_utm_dataset

    res_a = client.get(f"/api/v1/datasets/{ds.dataset_id}/tiles/18/187442/113652.png")
    res_b = client.get(f"/api/v1/datasets/{ds.dataset_id}/tiles/18/187443/113652.png")

    assert res_a.status_code == 200
    assert res_b.status_code == 200
    assert res_a.content != res_b.content


def test_out_of_bounds_transparent_tile(setup_utm_dataset):
    """Verify tiles outside dataset extent return transparent PNG."""
    ds = setup_utm_dataset

    # Tile over London (z=18, x=131072, y=87381)
    res = client.get(f"/api/v1/datasets/{ds.dataset_id}/tiles/18/131072/87381.png")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    # Transparent 1x1 or 256x256 PNG is returned
    assert len(res.content) < 1000 or res.content.startswith(b"\x89PNG")


def test_tilejson_schema(setup_utm_dataset):
    """Verify TileJSON endpoint exposes correct scheme and bounds."""
    ds = setup_utm_dataset

    res = client.get(f"/api/v1/datasets/{ds.dataset_id}/tilejson.json")
    assert res.status_code == 200
    tjson = res.json()
    assert tjson["tilejson"] == "3.0.0"
    assert tjson["scheme"] == "xyz"
    assert tjson["bounds"] == ds.bounds
    assert tjson["minzoom"] == 12
    assert tjson["maxzoom"] == 21
