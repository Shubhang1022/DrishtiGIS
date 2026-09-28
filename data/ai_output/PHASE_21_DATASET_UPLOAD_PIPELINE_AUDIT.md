# DrishtiGIS — Phase 21 Dataset Upload Pipeline Audit Report

## 1. Executive Summary & Root Cause Audit
Prior to Phase 21, aerial image uploads from the Admin Panel completed in ~1 second and displayed "Dataset Successfully Uploaded & Registered" followed by `VALIDATING → PROCESSING`.

### Discovered Root Cause:
1. **Request Lifecycle Disconnect**: The upload endpoint received binary chunks into a temporary folder, logged a security event, and immediately returned HTTP 200 `SUCCESS`.
2. **File Deletion**: In a `finally` block, `shutil.rmtree(temp_dir)` deleted the uploaded file without persisting it to a permanent dataset directory or triggering background processing.
3. **Missing State Persistence**: No job execution record was written to disk or database. The UI reported progress without backend tracking.

## 2. Repaired Background Job Architecture
Phase 21 introduces an asynchronous background pipeline worker (`backend/app/services/dataset_pipeline.py`) integrated with the thread-safe `DatasetStore` (`backend/app/services/dataset_store.py`).

### Workflow Sequence:
1. **Upload & Receipt**: `POST /api/v1/admin/datasets/upload` receives streamed chunks (up to 100 MB max) and saves the file to `data/uploads/{dataset_id}/{filename}`.
2. **Job Registration**: Registers `DatasetItem` in `REGISTERED` state (`progress_percent: 15`).
3. **Immediate HTTP 200/202 Response**: Returns dataset and job metadata with message: `"Upload successful — dataset registered. Processing has been queued in background."`.
4. **Asynchronous Background Worker**: `asyncio.create_task(run_dataset_pipeline(dataset_id))` handles processing across 4 lifecycle stages:
   - `REGISTERED → VALIDATING` (35% - 45%): Checks ZIP archive integrity, path traversal safety, CRS headers, spatial bounds.
   - `VALIDATING → PROCESSING` (65% - 80%): Performs COG pyramid tiling & vector feature indexing.
   - `PROCESSING → QA_REQUIRED` (90%): Runs automated quality checks.
   - `QA_REQUIRED → READY` (100%): Marks dataset ready for admin publication to public WebGIS endpoints.
