# DRISHTIGIS — REVIEW GEOMETRY IMMUTABILITY TEST REPORT
## Original AI Baseline Preservation vs Surveyor Modification Layer Separation

### Executive Summary
This report documents the verification of DrishtiGIS's human-in-the-loop geometry review engine (`/app/review`). A core design mandate of DrishtiGIS is that original AI-derived building geometries extracted by deep learning are strictly **immutable**. When a surveyor edits vector boundaries or attaches field verification evidence, the modification is stored in a separate review layer with a complete append-only audit trail.

---

### 1. Geometry Immutability & Audit Trail Test Matrix

| Test Step | Action Executed | Observed System Behavior | Immutability Status | Audit Log Event |
| :--- | :--- | :--- | :--- | :--- |
| **1. Original AI Geometry** | Extract AI building footprint `B-014` | Original coordinates stored in `bhopal-building-footprints.geojson` | **UNTOUCHED** | Initial AI feature registration logged. |
| **2. Surveyor Geometry Edit** | Submit modified vertex array via `/api/v1/reviews/B-014/edit` | Surveyor edit saved to `reviews.json` under `surveyor_geometry` | **IMMUTABLE** — Original AI footprint remains unchanged in base layer. | Event `GEOMETRY_EDITED` recorded with actor ID, timestamp, and before/after GeoJSON. |
| **3. Field Verification Attachment** | Submit GNSS RTK observation notes | Verification record appended to `verifications.json` | **IMMUTABLE** — Neither AI nor surveyor geometry overwritten. | Event `FIELD_VERIFICATION_ADDED` recorded. |
| **4. Reviewer Approval** | Approve review item via `/api/v1/reviews/B-014/status` | Status transitions from `SURVEYOR_EDITED` to `APPROVED` | **IMMUTABLE** — Both original AI geometry and surveyor edit preserved for historical audit. | Event `STATUS_CHANGED` recorded. |

---

### 2. Immutability Architecture Guarantees
- **Dual-Layer Representation**: The WebGIS map canvas renders the original AI footprint as a baseline layer and superimposes surveyor-edited polygons as a distinct review layer.
- **Append-Only Audit Log**: Security audit log entries cannot be modified or deleted via API endpoints; all status changes append a JSON record containing `timestamp`, `actor_id`, `role`, `previous_state`, and `new_state`.
