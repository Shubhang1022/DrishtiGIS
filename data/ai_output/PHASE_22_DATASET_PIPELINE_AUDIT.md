# PHASE 22: DATASET PIPELINE REALITY AUDIT REPORT

## Executive Summary
An independent audit of the DrishtiGIS dataset processing pipeline was conducted across backend services (`backend/app/services/dataset_pipeline.py`, `backend/app/services/dataset_store.py`) and administrative API controllers (`backend/app/api/v1/admin.py`).

Prior reports claimed asynchronous dataset ingestion with real-time stage transitions. The audit uncovered several key discrepancies:
- Worker tasks were previously unpersisted and managed via transient in-memory background tasks without startup recovery.
- Simulated static metadata (e.g. fixed EPSG:4326 strings and static feature counts) were used instead of real spatial header parsing.
- State machine rules were un-enforced on retry/publish endpoints, permitting premature publication of incomplete or validating datasets.

Phase 22 resolved these defects by establishing worker locking, startup recovery, real GeoJSON/TIFF inspection, and strict state transition guards.

---

## Detailed Audit Findings

| Finding ID | Component / File | Issue Description | Severity | Resolution Implemented |
|------------|------------------|-------------------|----------|------------------------|
| AUD-22-01 | `dataset_store.py` | Lack of worker lock led to potential duplicate workers processing the same dataset ID simultaneously. | HIGH | Added `acquire_worker_lock()` and `release_worker_lock()` in `DatasetStore`. |
| AUD-22-02 | `dataset_store.py` & `main.py` | Active background jobs in `REGISTERED` or `VALIDATING` state were abandoned upon server restart. | HIGH | Created `get_interrupted_datasets()` and an `@app.on_event("startup")` recovery handler to auto-resume jobs. |
| AUD-22-03 | `dataset_pipeline.py` | Geospatial metadata and feature counts were hardcoded or simulated via sleep intervals. | HIGH | Rebuilt `_inspect_geojson()` and `_inspect_tiff()` to inspect spatial bounds, geometry types, and feature counts dynamically. |
| AUD-22-04 | `admin.py` | Retry, cancel, and publish API endpoints did not check dataset state, allowing `PUBLISHED` on failed or non-`READY` items. | CRITICAL | Enforced strict `DatasetStore` state machine validation methods returning HTTP 400 on illegal transitions. |
| AUD-22-05 | `admin.py` & `upload/page.tsx` | UI advertised 100 MB upload limit while backend enforced streaming byte checks. | MEDIUM | Reconciled maximum upload size to authoritative 100 MB limit across backend headers and frontend UI. |
| AUD-22-06 | `dataset_pipeline.py` | Extracted ZIP archives lacked safety checks against Zip Slip path traversal. | CRITICAL | Added strict path sanitization checking for `..` and absolute file paths in `zipfile.ZipFile` extraction. |

---

## Direct Verification Checklist
1. **File Availability Post-HTTP**: Files stream directly to `data/uploads/{dataset_id}/{filename}` and persist across HTTP request completion.
2. **Background Task Execution**: `run_dataset_pipeline` executes asynchronous stages and updates JSON persistent state on disk (`data/datasets.json`).
3. **Reported Stages & Work**: Progress percentages monotonically increase from 15% through 100% tied directly to step completion.
4. **State Machine Integrity**: Attempting to publish an un-validated or validating dataset raises `ValueError` returning HTTP 400.
