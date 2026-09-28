# DrishtiGIS — Phase 24 Root Cause Analysis: Raster Visibility Defect

> **Document ID:** `PHASE_24_ROOT_CAUSE_RASTER_VISIBILITY`  
> **Timestamp:** `2026-09-24T17:03:00+05:30`  
> **Status:** `RESOLVED & VERIFIED`

---

## Executive Summary

Prior to Phase 24, an administrator uploading an aerial GeoTIFF dataset into DrishtiGIS received a success notice ("Dataset Successfully Uploaded & Registered") and observed status transitions such as `VALIDATING → PROCESSING → READY`. However, upon opening the WebGIS canvas, the newly uploaded aerial raster was **not rendered**. Only the default satellite basemap, orange cadastral boundaries, and AI building vectors appeared.

This root cause report documents the technical failures identified across the dataset ingestion, processing, serving, discovery, and rendering chain, and details the exact code modifications implemented to establish complete end-to-end raster visibility.

---

## Identified Root Causes

```
Admin Upload ──> File Persistence ──> Registry Inspection ──> Tile Service ──> WebGIS Discovery ──> MapLibre Source/Layer
    [OK]               [OK]              [DEFECT 1]          [DEFECT 2]        [DEFECT 3]              [DEFECT 4]
```

### Defect 1: Hardcoded Spatial Bounds Fallback in Raster Inspection
* **File:** `backend/app/services/dataset_pipeline.py` (`_inspect_tiff`)
* **Symptom:** When extracting GeoTIFF metadata, non-standard CRS or un-reprojected bounding boxes failed transform calculation silently and fell back to static hardcoded Bhopal bounds (`[77.4012, 23.2488, 77.4325, 23.2710]`).
* **Root Cause:** `_inspect_tiff()` did not utilize `rasterio.warp.transform_bounds` to reliably convert source GeoTIFF bounds into WGS84 geographic coordinates (`EPSG:4326`).
* **Fix:** Upgraded `_inspect_tiff()` to inspect `src.crs` and execute `transform_bounds(src.crs, "EPSG:4326", ...)` with explicit exception logging.

### Defect 2: Missing Per-Dataset Tile & TileJSON HTTP Endpoints
* **File:** `backend/app/api/v1/published_datasets.py`
* **Symptom:** The backend provided a static tile router (`/api/v1/tiles/bhopal/...`) for pre-cut prototype tiles, but lacked dynamic XYZ tile streaming and TileJSON metadata endpoints for uploaded datasets (`/api/v1/datasets/{dataset_id}/tiles/{z}/{x}/{y}.png` and `/api/v1/datasets/{dataset_id}/tilejson.json`).
* **Root Cause:** Uploaded GeoTIFFs were saved to `data/uploads/{dataset_id}/` without any HTTP map service or tile endpoint attached to the dataset record.
* **Fix:** Implemented `GET /api/v1/datasets/{dataset_id}/tilejson.json` and `GET /api/v1/datasets/{dataset_id}/tiles/{z}/{x}/{y}.png` using `rasterio` windowed reading and tile caching in `data/uploads/{dataset_id}/cache_tiles/`.

### Defect 3: Missing Public Dataset Discovery Endpoint for WebGIS Canvas
* **File:** `backend/app/api/v1/published_datasets.py` & `drishtigis/lib/api/datasets.ts`
* **Symptom:** The WebGIS map canvas could only query hardcoded vector layers and static tiles. It had no mechanism to discover newly published datasets dynamically.
* **Root Cause:** Absence of a public API endpoint returning `is_published=True` dataset metadata to the frontend.
* **Fix:** Created `GET /api/v1/datasets/published` and `fetchPublishedDatasets()` frontend client function.

### Defect 4: Static MapLibre Raster Source Registration
* **File:** `drishtigis/components/map/MapLibreMap.tsx` & `LayerControl.tsx`
* **Symptom:** MapLibre JS only rendered a single static source `uav-tiles`.
* **Root Cause:** The map component did not maintain state for active published dataset IDs or dynamically register `type: "raster"` sources and layers via `map.addSource()` and `map.addLayer()`.
* **Fix:** Implemented a dynamic React effect in `MapLibreMap.tsx` that iterates through published datasets, registers `dataset-raster-source-${id}` and `dataset-raster-layer-${id}`, and binds layer toggles and "Zoom to extent" buttons in `LayerControl.tsx`.

---

## Verification Matrix

| Lifecycle Stage | Pre-Fix Status | Post-Fix Status | Empirical Verification |
|---|---|---|---|
| Dataset Ingestion | Persisted to disk | Persisted to disk | `data/uploads/{dataset_id}/` verified |
| CRS & Bounds Extraction | Hardcoded fallback | Real WGS84 bounds | `rasterio.warp.transform_bounds` validated |
| TileJSON Metadata API | Missing (404) | TileJSON 3.0.0 (200) | `GET /api/v1/datasets/{id}/tilejson.json` |
| XYZ Tile Streaming API | Missing (404) | PNG tiles (200) | `GET /api/v1/datasets/{id}/tiles/{z}/{x}/{y}.png` |
| WebGIS Discovery | Static hardcoded | Dynamic discovery | `GET /api/v1/datasets/published` |
| MapLibre Rendering | No raster layer | Rendered raster layer | MapLibre source + layer registered |
