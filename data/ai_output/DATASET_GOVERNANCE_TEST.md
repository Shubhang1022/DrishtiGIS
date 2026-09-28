# DRISHTIGIS — DATASET GOVERNANCE & LIFECYCLE TEST REPORT
## Dataset Lifecycle State Machine, Governance Access Controls & Region Scoping

### Executive Summary
Testing was conducted against DrishtiGIS's dataset governance engine to verify lifecycle transitions (`REGISTERED` &rarr; `VALIDATING` &rarr; `PROCESSING` &rarr; `QA_REQUIRED` &rarr; `READY` &rarr; `PUBLISHED` &rarr; `ARCHIVED`), administrative permission checks, region scoping, and error recovery behavior.

---

### 1. Dataset Lifecycle State Transition Test Matrix

| Transition Step | Target State | Permitted Actor | Unpermitted Actor Attempt | State Validation Rule | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Upload & Ingest** | `REGISTERED` | `ADMIN` / `SURVEYOR` | `PUBLIC` &rarr; `HTTP 401/403` | Validates file format & GeoTIFF headers. | **PASS** |
| **2. Validation** | `VALIDATING` | System Pipeline | User direct force &rarr; `HTTP 400` | Checks spatial bounding box & CRS projection. | **PASS** |
| **3. AI Processing** | `PROCESSING` | System Pipeline | User direct force &rarr; `HTTP 400` | Executes U-Net segmentation & polygonization. | **PASS** |
| **4. Surveyor QA** | `QA_REQUIRED` | System Pipeline | `PUBLIC` &rarr; `HTTP 403` | Generates initial building-parcel spatial joins. | **PASS** |
| **5. Ready for Review** | `READY` | `SURVEYOR` | `PUBLIC` &rarr; `HTTP 403` | Requires all high-discrepancy items evaluated. | **PASS** |
| **6. Publish Dataset** | `PUBLISHED` | `REVIEWER` / `ADMIN` | `PUBLIC` / `SURVEYOR` &rarr; `HTTP 403` | Promotes dataset to public WebGIS visibility. | **PASS** |
| **7. Archive Dataset** | `ARCHIVED` | `ADMIN` | Non-Admin &rarr; `HTTP 403` | Deprecates dataset while preserving audit logs. | **PASS** |

---

### 2. Region Scoping & Governance Enforcement
- **Multi-Tenant Isolation**: Users assigned to region `bhopal_mp` cannot publish or modify datasets belonging to other regional jurisdictions (`delhi_ncr`, `lucknow_up`).
- **Failed Ingestion Recovery**: If a corrupt raster is uploaded during `VALIDATING`, the state transitions safely to `FAILED_VALIDATION` with a clear diagnostic message, preventing system lockup.
