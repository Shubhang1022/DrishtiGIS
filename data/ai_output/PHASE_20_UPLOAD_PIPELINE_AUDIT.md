# DrishtiGIS — Phase 20 Dataset Upload Pipeline Audit Report

## 1. Upload Architecture Overview
The DrishtiGIS dataset upload pipeline processes geospatial raster orthomousaics, vector polygons, and archive bundles for administrative ingestion.

### Key Components:
- **UI File Input & Drag-and-Drop**: `drishtigis/app/admin/datasets/upload/page.tsx`
- **Frontend API Client**: `drishtigis/lib/api/datasets.ts` using `FormData` multipart requests
- **Backend Admin Ingestion Endpoint**: `POST /api/v1/admin/datasets/upload` in `backend/app/api/v1/admin.py`
- **Security & Authorization**: `require_admin` dependency restricting access to `ADMIN` role users

## 2. Upload Limit Alignment & Enforcement
- **Previous Inconsistency**: Frontend mock UI displayed "2.5 GB", while backend config specified `MAX_UPLOAD_SIZE_MB=100`.
- **Resolution**: Aligned frontend UI label to **100 MB (Configured limit)** (`MAX_UPLOAD_SIZE_MB=100`).
- **Client-Side Pre-Validation**: Checks `file.size > 100 * 1024 * 1024` before dispatching request, displaying a clear validation error.
- **Server-Side Content-Length Check**: Validates `Content-Length` header if provided against `100 * 1024 * 1024` bytes.
- **Streaming Byte Count Limit**: Reads binary stream in 64 KB chunks, tracking cumulative bytes read and truncating with HTTP 413 if total bytes exceed limit.
- **Cleanup On Failure**: Temporary upload directories (`tempfile.mkdtemp(prefix="drishti_upload_")`) are deleted in a `finally` block upon failure or abort.

## 3. Geospatial Format & Security Protections
- **Allowed Extensions**: `.tif`, `.tiff`, `.geojson`, `.gpkg`, `.zip`
- **ZIP Bomb Safeguards**: Enforces maximum 50 compressed files and 250 MB maximum uncompressed size threshold (`MAX_UNCOMPRESSED_ZIP_SIZE = 250 * 1024 * 1024`).
- **Path Traversal Security**: Rejects zip entries containing `..` or absolute path prefixes.
- **CRS & Geometry Inspection**: Validates GeoJSON and GeoTIFF files for valid bounds and coordinate reference systems.
- **Lifecycle Progression**: Registers valid datasets into state: `REGISTERED → VALIDATING → PROCESSING → READY`.

## 4. Test Verification Summary
- **Oversized Upload Test**: Attempting >100 MB file upload returns HTTP 413 `Payload Too Large`.
- **Invalid Format Test**: Attempting `.exe` or `.txt` upload returns HTTP 400 `Invalid file format`.
- **Non-Admin Test**: Unauthenticated or `PUBLIC`/`SURVEYOR` role accounts receive HTTP 403 `Forbidden`.
