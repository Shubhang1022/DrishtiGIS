# PHASE 22: DATA INTEGRITY REPORT

## Overview
Data integrity controls ensure that raw uploaded geospatial files, metadata stores, output artifacts, and public WebGIS feeds remain uncorrupted, traceable, and compliant with privacy standards.

---

## Data Integrity Guarantees

### 1. Source Data Preservation
- Uploaded raw files are saved to `data/uploads/{dataset_id}/{filename}` and kept strictly read-only after ingestion.
- Output artifacts (tiled COGs, GeoJSON feeds, quality reports) are stored separately in `data/uploads/{dataset_id}/outputs/`.
- Reprojection or vectorization operations never overwrite or mutate original uploaded source files.

### 2. Monotonic Progress Tracking
- Processing stages update progress percentages strictly monotonically during execution attempt.
- Progress percentage resets to 15% only upon explicit administrative retry action.
- Status 100% completion is blocked until all pipeline stages and quality output verifications succeed.

### 3. Public WebGIS Endpoint Isolation
- Datasets in `REGISTERED`, `VALIDATING`, `PROCESSING`, `FAILED`, or `CANCELLED` states are completely excluded from public layer lists and WebGIS vector/raster endpoints.
- Datasets are served to public endpoints (`/api/v1/parcels`, `/api/v1/features`) ONLY after an authorized admin issues an explicit `publish` command on a `READY` or `QA_REQUIRED` dataset.

### 4. Synthetic Cadastral Data Integrity
- All synthetic parcel properties (`data/synthetic/bhopal-synthetic-properties.json`) retain explicit synthetic disclaimers.
- No synthetic property features interfere with or overwrite authentic user property markers or uploaded datasets.
