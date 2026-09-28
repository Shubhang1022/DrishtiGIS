# PHASE 22: DURABLE WORKER & JOB RECOVERY REPORT

## Overview
DrishtiGIS operates on a zero-cost local deployment model without external Redis or Celery dependencies. In Phase 22, worker durability, idempotency, and background job recovery were implemented directly within `backend/app/services/dataset_store.py` and `backend/app/main.py`.

---

## Technical Architecture

### 1. Job State Persistence
Dataset state and job metadata are atomically saved to `data/datasets.json` after every state change via an in-memory thread lock (`threading.RLock`).
Fields persisted include:
- `dataset_id`, `job_id`, `status` (`REGISTERED`, `VALIDATING`, `PROCESSING`, `QA_REQUIRED`, `READY`, `PUBLISHED`, `FAILED`, `CANCELLED`)
- `current_stage`, `progress_percent`, `completed_steps`, `pending_steps`, `failed_steps`
- `crs`, `bounds`, `dimensions`, `feature_count`, `outputs`
- Timestamps (`uploaded_at`, `processing_started_at`, `completed_at`, `last_updated_at`)

### 2. Startup Job Recovery
When the FastAPI backend boots up or restarts:
1. `@app.on_event("startup")` invokes `dataset_store.get_interrupted_datasets()`.
2. Any dataset remaining in `REGISTERED`, `VALIDATING`, or `PROCESSING` state whose worker lock is not active is identified.
3. The server automatically re-enqueues `asyncio.create_task(run_dataset_pipeline(dataset_id))`.

### 3. Duplicate Worker Lock Prevention
To prevent multiple async workers from processing the same dataset simultaneously:
- `acquire_worker_lock(dataset_id)` checks `_active_workers` set under lock.
- If already active, the worker aborts execution safely without modifying dataset state.
- `release_worker_lock(dataset_id)` releases the lock upon completion or error handling in `try...finally`.

### 4. Idempotent Retry & Cancellation
- `retry_dataset(dataset_id)` resets state to `REGISTERED`, clears failure steps, and re-queues processing.
- `cancel_dataset(dataset_id)` moves status to `CANCELLED` and sets completed timestamp.
