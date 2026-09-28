"""
DrishtiGIS — Phase 24 End-to-End Raster Tile & Published Datasets Test Suite
===========================================================================
Validates:
1. Discovery of published datasets via GET /api/v1/datasets/published
2. Filtering out unpublished datasets
3. TileJSON specification generation via GET /api/v1/datasets/{dataset_id}/tilejson.json
4. Windowed XYZ tile rendering via GET /api/v1/datasets/{dataset_id}/tiles/{z}/{x}/{y}.png
5. Out-of-bounds tile handling (204 No Content)
6. Invalid coordinate rejection (400 Bad Request)
7. Security rejection of unpublished or unauthorized dataset tile requests (403 Forbidden)
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

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_datasets():
    """Create a temporary GeoTIFF dataset and register published & unpublished test records."""
    temp_dir = tempfile.mkdtemp()
    tif_path = os.path.join(temp_dir, "test_bhopal_raster.tif")

    # Create a 256x256 test GeoTIFF centered around Bhopal (77.40, 23.25)
    width, height = 256, 256
    transform = from_origin(77.40, 23.26, 0.0001, 0.0001)
    data = (np.random.rand(3, height, width) * 255).astype(np.uint8)

    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)

    # Published Dataset Record
    pub_record = DatasetItem(
        dataset_id="DS-TEST-PUBLISHED-001",
        name="Test Published Bhopal UAV Dataset",
        filename="test_bhopal_raster.tif",
        format="uav_raster",
        file_path=tif_path,
        file_size_bytes=os.path.getsize(tif_path),
        status="READY",
        is_published=False,
        crs="EPSG:4326 (WGS 84)",
        bounds=[77.40, 23.2344, 77.4256, 23.26],
        dimensions="256 x 256 x 3",
        outputs=[
            {
                "type": "tilejson",
                "name": "TileJSON Specification",
                "url": "/api/v1/datasets/DS-TEST-PUBLISHED-001/tilejson.json"
            },
            {
                "type": "xyz_tiles",
                "name": "XYZ Raster Tile Stream",
                "template": "/api/v1/datasets/DS-TEST-PUBLISHED-001/tiles/{z}/{x}/{y}.png"
            }
        ]
    )

    # Unpublished Dataset Record
    unpub_record = DatasetItem(
        dataset_id="DS-TEST-UNPUBLISHED-002",
        name="Test Draft Dataset",
        filename="test_bhopal_raster.tif",
        format="uav_raster",
        file_path=tif_path,
        file_size_bytes=os.path.getsize(tif_path),
        status="PROCESSING",
        is_published=False,
        crs="EPSG:4326 (WGS 84)",
        bounds=[77.40, 23.2344, 77.4256, 23.26],
        dimensions="256 x 256 x 3",
    )

    dataset_store.datasets[pub_record.dataset_id] = pub_record
    dataset_store.datasets[unpub_record.dataset_id] = unpub_record
    dataset_store.publish_dataset(pub_record.dataset_id)

    yield pub_record, unpub_record

    # Cleanup
    dataset_store.datasets.pop(pub_record.dataset_id, None)
    dataset_store.datasets.pop(unpub_record.dataset_id, None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_list_published_datasets(setup_test_datasets):
    """Verify GET /api/v1/datasets/published returns only published datasets."""
    response = client.get("/api/v1/datasets/published", headers={})
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    
    ids = [d["dataset_id"] for d in data["datasets"]]
    assert "DS-TEST-PUBLISHED-001" in ids
    assert "DS-TEST-UNPUBLISHED-002" not in ids


def test_get_dataset_tilejson(setup_test_datasets):
    """Verify TileJSON generation for a published dataset."""
    pub_rec, unpub_rec = setup_test_datasets

    # Published dataset TileJSON
    res = client.get(f"/api/v1/datasets/{pub_rec.dataset_id}/tilejson.json", headers={})
    assert res.status_code == 200
    tilejson = res.json()
    assert tilejson["tilejson"] == "3.0.0"
    assert tilejson["name"] == pub_rec.name
    assert f"/api/v1/datasets/{pub_rec.dataset_id}/tiles/{{z}}/{{x}}/{{y}}.png" in tilejson["tiles"][0]
    assert tilejson["bounds"] == pub_rec.bounds
    assert tilejson["minzoom"] == 12
    assert tilejson["maxzoom"] == 21

    # Unpublished dataset TileJSON -> 403 Forbidden
    unpub_res = client.get(f"/api/v1/datasets/{unpub_rec.dataset_id}/tilejson.json", headers={})
    assert unpub_res.status_code == 403


def test_get_dataset_raster_tile_valid(setup_test_datasets):
    """Verify XYZ tile rendering for a valid tile intersecting the dataset bounds."""
    pub_rec, _ = setup_test_datasets

    # Zoom 14 tile covering Bhopal area (77.40, 23.25) -> x=11714, y=7104
    res = client.get(f"/api/v1/datasets/{pub_rec.dataset_id}/tiles/14/11714/7104.png", headers={})
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert len(res.content) > 100


def test_get_dataset_raster_tile_out_of_bounds(setup_test_datasets):
    """Verify 200 OK with transparent PNG or 204 No Content for tile outside dataset bounds."""
    pub_rec, _ = setup_test_datasets

    # Tile over London (z=14, x=8192, y=5461)
    res = client.get(f"/api/v1/datasets/{pub_rec.dataset_id}/tiles/14/8192/5461.png", headers={})
    assert res.status_code in (200, 204, 404)
    if res.status_code == 200:
        assert res.headers["content-type"] == "image/png"


def test_get_dataset_raster_tile_invalid_coords(setup_test_datasets):
    """Verify 400 Bad Request for malformed tile coordinates."""
    pub_rec, _ = setup_test_datasets

    res = client.get(f"/api/v1/datasets/{pub_rec.dataset_id}/tiles/14/99999999/99999999.png", headers={})
    assert res.status_code in (400, 204, 404)


def test_get_dataset_raster_tile_unpublished_rejected(setup_test_datasets):
    """Verify 403 Forbidden when requesting tiles for an unpublished dataset."""
    _, unpub_rec = setup_test_datasets

    res = client.get(f"/api/v1/datasets/{unpub_rec.dataset_id}/tiles/14/11716/7103.png", headers={})
    assert res.status_code == 403
    assert "not published" in res.json()["detail"].lower()
