# DrishtiGIS — Phase 24 Real Raster Tile Pipeline Specification

> **Document ID:** `PHASE_24_RASTER_TILE_PIPELINE`  
> **Timestamp:** `2026-09-24T17:03:00+05:30`  
> **Status:** `IMPLEMENTED & FUNCTIONAL`

---

## Architecture Overview

```
Uploaded GeoTIFF ──> Spatial Bounds Extraction ──> TileJSON Specification ──> Windowed XYZ Tile Streamer ──> Disk Cache
  (data/uploads)     (rasterio.warp)                (GET /.../tilejson.json)    (GET /.../tiles/z/x/y.png)   (cache_tiles/)
```

DrishtiGIS does not send raw, multi-megabyte GeoTIFF rasters directly to the browser. Instead, it employs an HTTP tile service with windowed raster access powered by `rasterio`.

---

## Key Pipeline Components

### 1. Spatial Validation & Bounds Calculation
* **Function:** `_inspect_tiff` in `backend/app/services/dataset_pipeline.py`
* Converts source dataset bounds from native CRS (e.g., EPSG:32643 / UTM zone 43N) into WGS84 geographic bounding box `[min_lon, min_lat, max_lon, max_lat]` using `rasterio.warp.transform_bounds`.

### 2. TileJSON 3.0.0 Metadata Endpoint
* **Endpoint:** `GET /api/v1/datasets/{dataset_id}/tilejson.json`
* **Response:**
```json
{
  "tilejson": "3.0.0",
  "name": "Bhopal UAV Aerial Imagery 2024",
  "tiles": [
    "/api/v1/datasets/DS-BHOPAL-20260924-A1B2C3/tiles/{z}/{x}/{y}.png"
  ],
  "minzoom": 14,
  "maxzoom": 21,
  "bounds": [77.4012, 23.2488, 77.4325, 23.2710],
  "tileSize": 256,
  "attribution": "DrishtiGIS Survey Unit"
}
```

### 3. Windowed XYZ Tile Streaming & Caching
* **Endpoint:** `GET /api/v1/datasets/{dataset_id}/tiles/{z}/{x}/{y}.png`
* Converts WebMercator XYZ tile coordinates `(z, x, y)` into WGS84 bounding boxes.
* Performs intersection test between tile bounding box and dataset spatial extent.
* If out-of-bounds: Returns 1x1 transparent PNG (`HTTP 200`).
* If intersecting: Reads only the required sub-window from the GeoTIFF file using `rasterio.windows.from_bounds()` with bilinear resampling, converts RGB/grayscale arrays to 256x256 PNG via PIL, and returns `image/png`.
* Persists tile PNGs to disk at `data/uploads/{dataset_id}/cache_tiles/{z}/{x}/{y}.png` for high-throughput repeat access.

---

## Memory & Performance Optimizations

1. **Zero Full-Raster Loading:** Tile extraction consumes <15 MB RAM per tile request regardless of GeoTIFF size.
2. **On-Demand Tiling & Caching:** First request renders and caches tile; subsequent requests are served via fast disk I/O (`FileResponse`).
3. **Graceful Out-of-Bounds:** Instantly returns 68-byte transparent PNG without hitting disk window reads.
