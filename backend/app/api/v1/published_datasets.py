"""
DrishtiGIS — Published Dataset & Raster Tile Service API Router
================================================================
Exposes public/authenticated WebGIS endpoints for dataset discovery,
TileJSON metadata generation, dynamic XYZ tile streaming, and dataset details.

Endpoints:
- GET /api/v1/datasets/published -> List all published datasets
- GET /api/v1/datasets/{dataset_id} -> Get public dataset metadata
- GET /api/v1/datasets/{dataset_id}/tilejson.json -> TileJSON 3.0.0 metadata
- GET /api/v1/datasets/{dataset_id}/tiles/{z}/{x}/{y}.png -> XYZ raster tile streaming
"""

import os
import math
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query, Response, Path as FPath
from fastapi.responses import FileResponse

import rasterio
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import from_bounds
from PIL import Image

from backend.app.services.dataset_store import dataset_store, DatasetItem

router = APIRouter()

_REPO_ROOT = Path(__file__).resolve().parents[3]
TRANSPARENT_1X1_PNG = Buffer = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000200000500010d0a2db40000000049454e44ae426082"
)

def tile_xyz_to_wgs84_bounds(z: int, x: int, y: int) -> List[float]:
    """Calculate [min_lon, min_lat, max_lon, max_lat] in WGS84 for tile (z, x, y)."""
    if z < 0 or z > 30:
        raise ValueError("Invalid tile zoom level")
    n = 2.0 ** z
    if x < 0 or x >= n or y < 0 or y >= n:
        raise ValueError("Invalid tile coordinates for zoom level")

    min_lon = x / n * 360.0 - 180.0
    max_lon = (x + 1) / n * 360.0 - 180.0
    
    lat_rad_max = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
    max_lat = math.degrees(lat_rad_max)
    
    lat_rad_min = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 1) / n)))
    min_lat = math.degrees(lat_rad_min)
    
    return [round(min_lon, 6), round(min_lat, 6), round(max_lon, 6), round(max_lat, 6)]

def tile_xyz_to_epsg3857_bounds(z: int, x: int, y: int) -> List[float]:
    """Calculate exact [min_x, min_y, max_x, max_y] in Web Mercator (EPSG:3857) for tile (z, x, y)."""
    if z < 0 or z > 30:
        raise ValueError("Invalid tile zoom level")
    n = 2.0 ** z
    if x < 0 or x >= n or y < 0 or y >= n:
        raise ValueError("Invalid tile coordinates for zoom level")

    R = 20037508.342789244
    tile_size = 2.0 * R / n
    min_x = -R + x * tile_size
    max_x = -R + (x + 1) * tile_size
    max_y = R - y * tile_size
    min_y = R - (y + 1) * tile_size

    return [min_x, min_y, max_x, max_y]

def bounds_overlap(b1: List[float], b2: List[float]) -> bool:
    """Check if bounding box b1 overlaps b2 [min_lon, min_lat, max_lon, max_lat]."""
    if b1[2] < b2[0] or b1[0] > b2[2]:
        return False
    if b1[3] < b2[1] or b1[1] > b2[3]:
        return False
    return True

_TIFF_INDEX_CACHE: Dict[str, List[Any]] = {}

def get_indexed_tiffs(target_path: str, ds_bounds: List[float]) -> List[Any]:
    """
    Returns cached list of (filepath, wgs84_bounds, src_crs) for a directory or single GeoTIFF.
    Avoids opening hundreds of TIFF files sequentially on every single XYZ tile request.
    """
    if target_path in _TIFF_INDEX_CACHE:
        return _TIFF_INDEX_CACHE[target_path]

    import glob
    tiff_files = []
    if os.path.isdir(target_path):
        tiff_files = glob.glob(os.path.join(target_path, "*.tiff")) + glob.glob(os.path.join(target_path, "*.tif"))
    elif os.path.isfile(target_path):
        tiff_files = [target_path]

    indexed = []
    for tf in tiff_files:
        try:
            with rasterio.open(tf) as src:
                src_crs = src.crs or "EPSG:32643"
                if src.bounds:
                    try:
                        wgs_b = list(transform_bounds(src_crs, "EPSG:4326", src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top))
                    except Exception:
                        wgs_b = ds_bounds
                else:
                    wgs_b = ds_bounds
                indexed.append((tf, wgs_b, str(src_crs)))
        except Exception:
            continue

    _TIFF_INDEX_CACHE[target_path] = indexed
    return indexed

def generate_tile_png_from_dataset(ds: DatasetItem, z: int, x: int, y: int) -> bytes:
    """
    Renders an authoritative 256x256 WebMercator (EPSG:3857) RGBA tile image for a dataset
    using rasterio.warp.reproject. Supports single GeoTIFF files and directories of GeoTIFFs.
    """
    import numpy as np
    from rasterio.warp import reproject, Resampling, transform_bounds
    from rasterio.transform import from_bounds

    try:
        tile_3857_b = tile_xyz_to_epsg3857_bounds(z, x, y)
    except ValueError:
        return TRANSPARENT_1X1_PNG

    target_path = ds.file_path
    if not target_path or not os.path.exists(target_path):
        return TRANSPARENT_1X1_PNG

    ds_bounds = ds.bounds or [77.412951, 23.254292, 77.422689, 23.256671]
    indexed_tiffs = get_indexed_tiffs(target_path, ds_bounds)
    if not indexed_tiffs:
        return TRANSPARENT_1X1_PNG

    # Convert tile EPSG:3857 bounds to WGS84 for fast bounding box filtering
    try:
        t_wgs_b = transform_bounds("EPSG:3857", "EPSG:4326", *tile_3857_b)
    except Exception:
        t_wgs_b = ds_bounds

    # Quick check: if tile WGS84 bounds don't overlap dataset bounds, return transparent PNG
    if not bounds_overlap(t_wgs_b, ds_bounds):
        return TRANSPARENT_1X1_PNG

    # Filter to only the GeoTIFFs whose bounding box overlaps the tile
    overlapping_tiffs = [
        item for item in indexed_tiffs
        if bounds_overlap(t_wgs_b, item[1])
    ]
    if not overlapping_tiffs:
        return TRANSPARENT_1X1_PNG

    dst_transform = from_bounds(tile_3857_b[0], tile_3857_b[1], tile_3857_b[2], tile_3857_b[3], 256, 256)
    dst_data = np.zeros((4, 256, 256), dtype=np.uint8)
    rendered_any = False

    for tf, wgs_b, src_crs_str in overlapping_tiffs:
        try:
            with rasterio.open(tf) as src:
                src_crs = src.crs or src_crs_str

                count = min(src.count, 3)
                src_bands = list(range(1, count + 1))
                if count == 1:
                    src_bands = [1, 1, 1]

                # High-precision windowed read to sample native resolution
                try:
                    src_tile_b = transform_bounds("EPSG:3857", src_crs, *tile_3857_b)
                    win = from_bounds(src_tile_b[0], src_tile_b[1], src_tile_b[2], src_tile_b[3], src.transform)
                    win = win.round_offsets().round_shape()
                    c_off = max(0, int(win.col_off) - 2)
                    r_off = max(0, int(win.row_off) - 2)
                    w_len = min(src.width - c_off, int(win.width) + 4)
                    h_len = min(src.height - r_off, int(win.height) + 4)
                    
                    if w_len <= 0 or h_len <= 0:
                        continue
                        
                    win = rasterio.windows.Window(c_off, r_off, w_len, h_len)
                    raw_src = src.read(src_bands, window=win)
                    win_transform = rasterio.windows.transform(win, src.transform)
                except Exception:
                    raw_src = src.read(src_bands)
                    win_transform = src.transform

                temp_tile = np.zeros((3, 256, 256), dtype=np.uint8)

                reproject(
                    source=raw_src,
                    destination=temp_tile,
                    src_transform=win_transform,
                    src_crs=src_crs,
                    dst_transform=dst_transform,
                    dst_crs="EPSG:3857",
                    resampling=Resampling.cubic
                )

                mask = (temp_tile[0] > 0) | (temp_tile[1] > 0) | (temp_tile[2] > 0)
                if np.any(mask):
                    dst_mask = (dst_data[3] == 0) & mask
                    dst_data[:3] = np.where(dst_mask, temp_tile, dst_data[:3])
                    dst_data[3] = np.where(mask, 255, dst_data[3])
                    rendered_any = True

        except Exception:
            continue

    if not rendered_any:
        return TRANSPARENT_1X1_PNG

    img = Image.fromarray(dst_data.transpose(1, 2, 0), mode="RGBA")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# ── Public Endpoint: List Published Datasets for WebGIS ───────────────────────

@router.get("/published", summary="List All Published Datasets for WebGIS (Public)")
async def list_published_datasets():
    """
    Returns all published raster datasets ready to be rendered on the WebGIS map canvas.
    Filter strictly enforces format == 'uav_raster' and status == 'PUBLISHED' to prevent contamination.
    """
    all_datasets = dataset_store.list_datasets()
    published_items = [
        d for d in all_datasets
        if d.format == "uav_raster" and d.is_published and d.status == "PUBLISHED" and d.file_path and os.path.exists(d.file_path)
    ]
    
    result = []
    for d in published_items:
        tilejson_url = f"/api/v1/datasets/{d.dataset_id}/tilejson.json"
        tiles_url = f"/api/v1/datasets/{d.dataset_id}/tiles/{{z}}/{{x}}/{{y}}.png"
        
        result.append({
            "dataset_id": d.dataset_id,
            "name": d.name,
            "filename": d.filename,
            "format": d.format,
            "state": d.state,
            "city": d.city,
            "region_id": d.region_id,
            "crs": d.crs or "EPSG:4326 (WGS 84)",
            "bounds": d.bounds or [77.412951, 23.254292, 77.422689, 23.256671],
            "minzoom": 14,
            "maxzoom": 21,
            "tilejson_url": tilejson_url,
            "tiles_url": tiles_url,
            "uploaded_at": d.uploaded_at,
            "last_updated_at": d.last_updated_at,
            "is_published": True,
            "feature_count": d.feature_count or 0,
            "outputs": d.outputs or []
        })
        
    return {
        "total": len(result),
        "datasets": result
    }

# ── Public Endpoint: Get Dataset Details ──────────────────────────────────────

@router.get("/{dataset_id}", summary="Get Public Dataset Details")
async def get_public_dataset(dataset_id: str):
    ds = dataset_store.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset ID '{dataset_id}' not found.")
    
    data = ds.model_dump()
    data["tilejson_url"] = f"/api/v1/datasets/{dataset_id}/tilejson.json"
    data["tiles_url"] = f"/api/v1/datasets/{dataset_id}/tiles/{{z}}/{{x}}/{{y}}.png"
    return data

# ── Public Endpoint: TileJSON Metadata Specification ──────────────────────────

@router.get("/{dataset_id}/tilejson.json", summary="Get Dataset TileJSON Specification")
async def get_dataset_tilejson(dataset_id: str):
    """
    Returns standard TileJSON 3.0.0 metadata format for MapLibre GL raster source initialization.
    """
    ds = dataset_store.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset ID '{dataset_id}' not found.")
    if not ds.is_published and ds.status != "PUBLISHED":
        raise HTTPException(status_code=403, detail=f"Dataset '{dataset_id}' is not published for map display.")

    bounds = ds.bounds or [77.412951, 23.254292, 77.422689, 23.256671]
    center_lon = (bounds[0] + bounds[2]) / 2.0
    center_lat = (bounds[1] + bounds[3]) / 2.0

    return {
        "tilejson": "3.0.0",
        "name": ds.name,
        "description": f"DrishtiGIS Published Raster Dataset — {ds.name}",
        "version": "1.0.0",
        "attribution": "DrishtiGIS Geospatial Engine",
        "scheme": "xyz",
        "tiles": [
            f"/api/v1/datasets/{dataset_id}/tiles/{{z}}/{{x}}/{{y}}.png"
        ],
        "minzoom": 12,
        "maxzoom": 21,
        "bounds": bounds,
        "center": [round(center_lon, 6), round(center_lat, 6), 18],
        "tileSize": 256
    }

# ── Dynamic XYZ Raster Tile Endpoint ──────────────────────────────────────────

@router.get("/{dataset_id}/tiles/{z}/{x}/{y}.png", summary="Stream Dataset XYZ Raster Tile")
async def get_dataset_raster_tile(
    dataset_id: str,
    z: int = FPath(ge=0, le=30),
    x: int = FPath(ge=0),
    y: int = FPath(ge=0)
):
    """
    Streams single XYZ raster tile image (PNG) for published dataset.
    Reads tile from disk cache or generates PNG dynamically using windowed raster access.
    """
    ds = dataset_store.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset ID '{dataset_id}' not found.")
    if not ds.is_published and ds.status != "PUBLISHED":
        raise HTTPException(status_code=403, detail=f"Dataset '{dataset_id}' is not published for map display.")

    # 0. Validate XYZ coordinates
    try:
        tile_xyz_to_epsg3857_bounds(z, x, y)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))

    # 1. Check dataset cache tiles directory
    cache_dir = _REPO_ROOT / "data" / "uploads" / dataset_id / "cache_tiles" / str(z) / str(x)
    cache_file = cache_dir / f"{y}.png"
    if cache_file.exists():
        return FileResponse(str(cache_file), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})

    # 2. Generate tile PNG dynamically using EPSG:3857 reprojection
    png_bytes = generate_tile_png_from_dataset(ds, z, x, y)
    
    # 3. Save to tile cache if non-transparent
    if png_bytes != TRANSPARENT_1X1_PNG:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "wb") as f_out:
                f_out.write(png_bytes)
        except Exception:
            pass

    return Response(content=png_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

# ── Public Endpoint: Dataset Debug Footprints (GeoJSON) ───────────────────────

@router.get("/{dataset_id}/debug-footprints", summary="Get Dataset Raster Footprints GeoJSON")
async def get_dataset_debug_footprints(dataset_id: str):
    """
    Returns GeoJSON FeatureCollection containing precise polygon footprints for all source rasters.
    Used for visual verification of raster tile alignment and coverage bounds.
    """
    ds = dataset_store.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset ID '{dataset_id}' not found.")

    target_path = ds.file_path
    if not target_path or not os.path.exists(target_path):
        return {"type": "FeatureCollection", "features": []}

    tiff_files = []
    if os.path.isdir(target_path):
        tiff_files = glob.glob(os.path.join(target_path, "*.tiff")) + glob.glob(os.path.join(target_path, "*.tif"))
    elif os.path.isfile(target_path):
        tiff_files = [target_path]

    features = []
    for tf in tiff_files:
        fname = os.path.basename(tf)
        try:
            with rasterio.open(tf) as src:
                src_crs = src.crs or "EPSG:32643"
                wb = transform_bounds(src_crs, "EPSG:4326", src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
                poly_coords = [
                    [wb[0], wb[1]],
                    [wb[2], wb[1]],
                    [wb[2], wb[3]],
                    [wb[0], wb[3]],
                    [wb[0], wb[1]]
                ]
                features.append({
                    "type": "Feature",
                    "properties": {
                        "filename": fname,
                        "crs": str(src_crs),
                        "bounds": wb
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [poly_coords]
                    }
                })
        except Exception:
            continue

    return {
        "type": "FeatureCollection",
        "dataset_id": dataset_id,
        "total_rasters": len(features),
        "union_bounds": ds.bounds,
        "features": features
    }
