# DrishtiGIS — Phase 24 Security & Data Integrity Audit Report

> **Document ID:** `PHASE_24_SECURITY_DATA_INTEGRITY`  
> **Timestamp:** `2026-09-24T17:03:00+05:30`  
> **Status:** `AUDITED & SECURED`

---

## Executive Summary

Phase 24 introduces dynamic dataset discovery and tile serving while enforcing strict Role-Based Access Control (RBAC), tenant isolation, privacy controls, and data integrity checks across all raster endpoints.

---

## Security Audit & Access Control Policy

### 1. Published-Only Dataset Discovery
* **Endpoint:** `GET /api/v1/datasets/published`
* **Rule:** Exposes ONLY records where `is_published == True` or `status == "PUBLISHED"`.
* **Protection:** Draft, uploaded, validating, processing, failed, or cancelled datasets are strictly excluded from public discovery payload.

### 2. Unpublished Dataset Tile Rejection
* **Endpoint:** `GET /api/v1/datasets/{dataset_id}/tiles/{z}/{x}/{y}.png`
* **Rule:** If an unauthenticated or unauthorized user requests tiles for a dataset ID that is not published, the API immediately halts execution and returns `HTTP 403 Forbidden` (`detail: "Dataset '{id}' is not published for map display."`).

### 3. Path Traversal & File Injection Defense
* **Rule:** Dataset IDs are strictly validated to prevent directory traversal attacks (e.g. `../` or `..\\`).
* **Implementation:** `dataset_store.get_dataset(dataset_id)` retrieves target paths only from authoritative governance registry `data/governance/datasets.json`. Direct user-supplied file paths are NEVER accessed from HTTP parameters.

### 4. User Profile Privacy & Private HOME Protection
* Private HOME coordinates stored in `data/governance/user_homes.json` remain encrypted/isolated to the authenticated JWT subject (`sub`).
* Public tile endpoints and dataset discovery return zero personal user data or home locations.
