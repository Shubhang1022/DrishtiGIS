# PHASE 8 REPORT — SURVEYOR REVIEW, GROUND-TRUTHING & CADASTRAL GEOMETRY EDITING

**Project**: DrishtiGIS — AI-Based Urban Parcel Mapping & Cadastral Feature Intelligence  
**Problem Statement**: SIH26012 — AI-Based Automated Urban Parcel Mapping and Cadastral Feature Extraction System using Drone Imagery  
**Phase**: Phase 8 — Surveyor Review, Ground-Truthing & Cadastral Geometry Editing Workflow  
**Timestamp**: 2026-09-16  

---

## 1. Executive Summary & Principles

Phase 8 introduces a **Surveyor Review & Field Verification Workflow** into DrishtiGIS. The core architecture follows the strict principle:

> **AI proposes. GIS analyzes. Surveyor verifies. System records.**

The platform does **NOT** attempt to replace official human land surveyors or make automated legal property/ownership decisions. Instead, it provides a structured geospatial environment for inspecting preliminary AI/GIS outputs, reviewing geometric discrepancies, validating cadastral topology, executing controlled geometry edits, recording ground-truthing field observations, maintaining an immutable audit trail, and exporting GIS-ready cadastral features.

---

## 2. Review Architecture & Data Flow

```
   Map / Review Queue (/app/review)
                 │
                 ▼
          ContextSidebar
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
  AI Evidence          GIS Evidence
(UAVPal ResNet18)     (OSM / Synthetic)
      │                     │
      └──────────┬──────────┘
                 ▼
       Geometry Editing Engine
                 │
                 ▼
    Topology & Geometry Validation (Shapely)
    (Rejects self-intersections / zero-area)
                 │
                 ▼
   Spatial Relationship Recomputation
   (FULLY_WITHIN, CROSSES_BOUNDARY, overlap ratio)
                 │
                 ▼
   Ground-Truthing / Field Verification
   (GNSS, On-Site, CORS, Neutral Observations)
                 │
                 ▼
        Immutable Audit Log
                 │
                 ▼
     Reviewed GIS Export (GeoJSON)
```

---

## 3. Data Model Specifications

### Review Item Entity (`ReviewItem`)
- `review_id`: Unique identifier (e.g. `REV-DISC-55-00000`).
- `entity_type`: `PARCEL` | `AI_BUILDING` | `DISCREPANCY` | `ACCESS_CORRIDOR` | `LAND_USE`.
- `entity_id`: Related parcel or building ID.
- `parcel_id`: Foreign key reference to parcel record.
- `region_id`: Pan-India region code (e.g. `REGION-BPL-01`).
- `dataset_id`: Onboarded dataset ID (e.g. `DATASET-BHOPAL-UAV`).
- `epoch_id`: Capture epoch identifier (e.g. `EPOCH-BPL-2024-01`).
- `country`: `India`.
- `state`: `Madhya Pradesh`.
- `city`: `Bhopal`.
- `issue_type`: `BUILDING_CROSSES_PARCEL_BOUNDARY` | `MULTIPLE_BUILDINGS_IN_PARCEL` | `NO_PARCEL_MATCH` | `ACCESS_REVIEW_REQUIRED` | `NO_DETECTED_ACCESS_CORRIDOR` | `LAND_USE_REVIEW` | `HISTORICAL_CHANGE_REVIEW` | `INVALID_OR_INCONSISTENT_GEOMETRY` | `OTHER_REVIEW`.
- `source`: `AI_DERIVED_UAVPAL` | `REFERENCE_GIS` | `SYNTHETIC_DEMO` | `REVIEWED_AI_GEOMETRY` | `FIELD_VERIFIED`.
- `severity`: `HIGH` | `MEDIUM` | `LOW` | `INFO`.
- `status`: `OPEN` | `IN_REVIEW` | `FIELD_VERIFICATION_REQUIRED` | `ACCEPTED` | `REJECTED` | `RESOLVED`.
- `reviewer_notes`: Technical findings recorded by reviewer.
- `original_geometry`: Original geometry preserved untouched.
- `reviewed_geometry`: Adjusted geometry created by reviewer edit.
- `geometry_changed`: Boolean flag indicating if geometry was adjusted.
- `verification_method`: `ON_SITE` | `GNSS` | `CORS` | `SURVEY_RECORD` | `FIELD_PHOTO` | `AUTHORITY_RECORD` | `OTHER`.
- `verification_timestamp`: ISO timestamp of field verification.

### Audit Trail Log (`ReviewAuditTrail`)
- `audit_id`: Unique log identifier.
- `review_id`: Associated review item.
- `action`: `STATUS_CHANGE` | `GEOMETRY_EDITED` | `NOTE_ADDED` | `FIELD_VERIFICATION_RECORDED`.
- `previous_status` -> `new_status`.
- `reviewer`: Identifier of acting reviewer.
- `timestamp`: Immutable execution timestamp.

---

## 4. Geometry Editing & Immutability Guarantees

### Immutability of Source AI Data
- The 834 original AI building footprints (`AI_DERIVED_UAVPAL`) and 30 UAV GeoTIFF tiles remain strictly **immutable**.
- Edits made by a surveyor create a separate reviewed geometry record assigned source classification **`REVIEWED_AI_GEOMETRY`**.
- WebGIS UI provides a side-by-side toggle: **"Show Original AI"** vs **"Show Reviewed Geometry"**.

### Permissions & Layer Control
- **PARCEL**: Editable in review mode (for prototype demo parcels).
- **AI BUILDING**: Editable as a `REVIEWED_AI_GEOMETRY` layer.
- **REFERENCE OSM**: Read-Only.
- **OFFICIAL REFERENCE**: Read-Only.
- **SYNTHETIC DEMO**: Editable for prototype demonstration; retains mandatory disclaimer.

---

## 5. Topology Validation & Spatial Recomputation

### Topology Validation Rules
Before saving any geometry edit, `backend/app/gis/review_engine.py` executes Shapely validation:
1. Valid GeoJSON Polygon/MultiPolygon format.
2. Valid coordinate ring structure (>= 4 coordinates per ring, closed ring).
3. Non-empty geometry.
4. No self-intersections (`geom.is_valid`).
5. Non-zero metric area (> 0.001 m²).
If validation fails, the system rejects the edit with message:  
> **"Geometry requires correction before approval."**

### Automatic Relationship Recomputation
When parcel boundary geometry is edited, the GIS engine automatically recomputes:
- Spatial relationships: `FULLY_WITHIN`, `CROSSES_BOUNDARY`, `NO_PARCEL_MATCH`.
- Overlap ratios (`intersection_area / building_area`).
- Building counts and total parcel building area.
- Derived discrepancy list.

---

## 6. Ground-Truthing & Field Verification Workflow

A reviewer or field team member can record ground-truthing observations without fabricating data:
- **Methods Supported**: `ON_SITE`, `GNSS` (RTK receiver), `CORS`, `SURVEY_RECORD`, `FIELD_PHOTO`, `AUTHORITY_RECORD`.
- **Neutral Field Language**:
  - *"Observed boundary differs from preliminary AI-derived boundary."*
  - *"Building footprint aligns with physical ground structures observed via GNSS."*
- Strictly avoids legal terms (`illegal`, `encroachment`, `unauthorized`).

---

## 7. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/reviews` | List review items with filters (`status`, `issue_type`, `severity`, `city`, `dataset_id`) |
| `GET` | `/api/v1/reviews/stats` | Workflow statistics summary |
| `GET` | `/api/v1/reviews/export` | Export reviewed GIS geometry as GeoJSON |
| `GET` | `/api/v1/reviews/{review_id}` | Get review item details, audit trail, and verifications |
| `POST` | `/api/v1/reviews` | Create review item |
| `PATCH` | `/api/v1/reviews/{review_id}` | Update review status and record audit log |
| `POST` | `/api/v1/reviews/{review_id}/geometry` | Submit edited geometry, validate topology & recompute relationships |
| `POST` | `/api/v1/reviews/{review_id}/verify` | Record field verification observation |
| `GET` | `/api/v1/reviews/{review_id}/audit` | Get complete immutable audit log |
| `GET` | `/api/v1/parcels/{parcel_id}/review-history` | Get review history for a parcel |

---

## 8. WebGIS Integration

- **Review Queue Page (`/app/review`)**: Dedicated queue view featuring metric summary cards, multi-column filters (Status, Issue Type, Severity, City), search box, review item table, and GeoJSON export.
- **Map Review Mode (`ContextSidebar.tsx` & `ReviewModePanel.tsx`)**: Directly integrated into the right contextual sidebar. Reviewers can click any parcel or discrepancy on the map, click **"Review Issue"**, toggle original vs reviewed geometry, submit edits, record GNSS field observations, and view the audit trail.

---

## 9. Verification & Data Integrity Results

### Automated Backend Tests
- **Test File**: `backend/tests/test_phase8_review_workflow.py`
- **Results**: 12/12 Phase 8 workflow tests **PASSED**.
- **Full Backend Baseline**: **339 PASSED**, 1 skipped, 0 failed.

### Frontend TypeScript Build
- **Command**: `npm run build` inside `drishtigis/`
- **Result**: **Clean build with 0 TypeScript errors**.

### Dataset Integrity Verification
- 30 UAVPal RGB GeoTIFF tiles: **UNCHANGED**.
- 30 ground-truth label masks: **UNCHANGED**.
- 834 AI building footprints: **UNCHANGED**.
- 35 synthetic parcels: **UNCHANGED** (Disclaimers intact).
- 2,933 OSM roads & 98 land-use polygons: **UNCHANGED** (Read-only).

---

## 10. Capability Classification Matrix

| Capability | Classification | Notes |
|---|---|---|
| UAV Orthomosaic Imagery (30 tiles) | `AI-DERIVED` | Real UAVPal dataset |
| AI Building Footprints (834 features) | `AI-DERIVED` | Real U-Net + ResNet18 outputs |
| Synthetic Parcels (35 features) | `SYNTHETIC_DEMO` | Synthetic demo data for SIH prototype |
| OSM Reference Layers (Roads, Water, Land-Use) | `REFERENCE_GIS` | Read-only reference GIS |
| Historical Capture Epochs (2024 vs 2025) | `TEST_FIXTURE` | Temporal engine test fixtures |
| Review Queue & Audit Trail | `IMPLEMENTED` | Phase 8 workflow engine |
| Geometry Editing & Topology Engine | `IMPLEMENTED` | Shapely validation & recomputation |
| Field Verification Observation Recording | `FIELD_VERIFIED` | Structured ground-truthing records |
| Reviewed Cadastral GeoJSON Export | `IMPLEMENTED` | Includes CRS & disclaimers |
| Official Legal Land Title Records | `PLANNED` | Out of scope for SIH AI prototype |

---

## 11. Demonstration Scenario

1. Navigate to `/app/review` or `/app/map`.
2. Select parcel `DRS-BPL-DEMO-001` (or click `DISC-55-00000` with `BUILDING_CROSSES_PARCEL_BOUNDARY` issue).
3. Open **ContextSidebar** -> Click **"Review Issue"**.
4. View AI Evidence (`AI_DERIVED_UAVPAL`), confidence score, building area in m², and synthetic disclaimer.
5. Edit boundary -> Click **"Validate & Save Reviewed Geometry"**.
6. System runs Shapely topology validation, recomputes `FULLY_WITHIN`/`CROSSES_BOUNDARY` status, and stores adjusted geometry as `REVIEWED_AI_GEOMETRY`.
7. Click **"+ Record Observation"** -> Select `GNSS` method -> Record neutral observation text -> Save.
8. Update status to `FIELD_VERIFICATION_REQUIRED` -> View complete audit trail timeline.
9. Click **"Export Reviewed GIS"** -> Download GeoJSON feature collection.

---

## 12. Known Limitations & Future Improvements

1. **CAD/DXF File Import**: Direct importing of surveyor DXF/DWG survey files can be added in future phases.
2. **Direct GNSS NMEA Stream**: Direct Bluetooth GNSS receiver streaming into WebGIS UI planned for mobile field application.
3. **Role-based Auth Persistence**: Role abstraction (`VIEWER`, `SURVEYOR`, `REVIEWER`, `ADMIN`) is implemented; full OAuth/Keycloak integration can be attached in production deployment.
