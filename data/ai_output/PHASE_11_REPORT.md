# DrishtiGIS — Phase 11 Technical & Governance Report
**Authentication, Role-Based Access Control (RBAC) & Geospatial Data Governance**

---

## 1. Executive Summary
Phase 11 transitions DrishtiGIS from an unauthenticated prototype WebGIS workflow into an institutional, multi-user geospatial platform for urban parcel mapping and cadastral feature intelligence.

The system introduces secure token-based authentication (JWT + PBKDF2-HMAC-SHA256 password hashing), explicit Role-Based Access Control (`PUBLIC`, `SURVEYOR`, `REVIEWER`, `ADMIN`), multi-level spatial region isolation (`India` &rarr; `State` &rarr; `City` &rarr; `Region`), backend API permission enforcement, append-only security audit logging, and Admin Console management interfaces (`/admin/users`, `/admin/regions`).

---

## 2. Authentication & Session Architecture

```
FRONTEND (Next.js AuthContext)
   ↓ (POST /api/v1/auth/login or /register)
BACKEND AUTH ROUTER
   ↓ (PBKDF2 Verification / Hash Generation)
USER STORE (data/governance/users.json)
   ↓ (Issue Signed JWT Token)
SECURE LOCAL STORAGE / HTTP AUTHORIZATION HEADER
   ↓ (Bearer Token validation on APIs)
ROLE + PERMISSION DEPENDENCY ENFORCEMENT
```

### Supported Authentication Flows:
1. **Email / Password Authentication**: Standard institutional login with PBKDF2-HMAC-SHA256 password hashing (100,000 iterations).
2. **Institutional Access Request (`/register`)**: Self-service registration for field officers, surveyors, and researchers.
3. **Session Validation (`/me`)**: Validates active JWT session tokens and returns account profile details.
4. **Pre-seeded SIH Demonstration Accounts**:
   - `demo-public@drishtigis.in` / `Public123!` (Role: `PUBLIC`)
   - `demo-surveyor@drishtigis.in` / `Surveyor123!` (Role: `SURVEYOR`, Region: `bhopal_mp`)
   - `demo-reviewer@drishtigis.in` / `Reviewer123!` (Role: `REVIEWER`, Region: `bhopal_mp`)
   - `demo-admin@drishtigis.in` / `Admin123!` (Role: `ADMIN`, Region: `*`)

---

## 3. User Model & Schema
Stored persistently in `data/governance/users.json`:
- `user_id`: Unique identifier (`usr-...`)
- `email`: Official email address
- `name`: User full name
- `role`: Assigned role (`PUBLIC`, `SURVEYOR`, `REVIEWER`, `ADMIN`)
- `organization`: Department / agency name
- `country`: Country (`India`)
- `state`: State / Union Territory
- `city`: City / Municipal Corporation
- `region_id`: Assigned spatial jurisdiction (`bhopal_mp`, `lucknow_up`, or `*`)
- `allowed_datasets`: Permitted dataset IDs
- `is_active`: Account status flag (`True` / `False`)
- `created_at`: Account creation timestamp
- `last_login`: Last authenticated login timestamp

---

## 4. Role-Based Access Control (RBAC) Matrix

| Permission | PUBLIC | SURVEYOR | REVIEWER | ADMIN |
| :--- | :---: | :---: | :---: | :---: |
| `VIEW_MAP` | ✓ | ✓ | ✓ | ✓ |
| `VIEW_PARCEL` / `BUILDING` / `ROAD` | ✓ | ✓ | ✓ | ✓ |
| `USE_AI_ASSISTANT` | ✓ | ✓ | ✓ | ✓ |
| `CREATE_REVIEW` | ✗ | ✓ | ✓ | ✓ |
| `EDIT_REVIEW_GEOMETRY` | ✗ | ✓ | ✓ | ✓ |
| `SUBMIT_FIELD_VERIFICATION` | ✗ | ✓ | ✓ | ✓ |
| `APPROVE_REVIEW` / `REJECT_REVIEW` | ✗ | ✗ | ✓ | ✓ |
| `VIEW_AUDIT_LOG` | ✗ | ✗ | ✓ | ✓ |
| `EXPORT_DATA` / `EXPORT_REPORT` | Public Data | Assigned Region | Validated Output | Full Access |
| `MANAGE_USERS` / `MANAGE_REGIONS` | ✗ | ✗ | ✗ | ✓ |
| `PUBLISH_DATASET` / `PROCESS_DATASET` | ✗ | ✗ | ✗ | ✓ |

---

## 5. Region Isolation & Dataset Governance
DrishtiGIS implements a multi-level Pan-India spatial governance hierarchy:

$$\text{India} \longrightarrow \text{State} \longrightarrow \text{City} \longrightarrow \text{Region ID}$$

- **Bhopal Demonstration Region**: `bhopal_mp` (Bhopal, Madhya Pradesh)
- **Extensible Regions**: Registered via `/admin/regions` (e.g. `lucknow_up`, `pune_mh`, `blr_ka`).
- **Dataset Visibility Rules**:
  - `PUBLIC`: Datasets marked `visibility: "PUBLIC"` (e.g., published base maps, public reports).
  - `RESTRICTED`: Datasets requiring `SURVEYOR` or `REVIEWER` role with matching `region_id`.
  - `PRIVATE`: Admin-only raw datasets during processing.

---

## 6. Security Audit Logging
All security-sensitive transactions are recorded in an append-only audit trail at `data/governance/security_audit_logs.json`.

Events logged:
- `LOGIN`, `LOGOUT`, `REGISTER`
- `ROLE_CHANGED`, `USER_UPDATED`
- `REGION_REGISTERED`
- `REVIEW_CREATED`, `GEOMETRY_EDITED`, `REVIEW_ACCEPTED`, `REVIEW_REJECTED`
- `FIELD_VERIFICATION_SUBMITTED`
- `EXPORT_GENERATED`

*Security Guarantee*: Audit logs strictly exclude passwords, JWT secrets, and tokens.

---

## 7. Grounded AI Assistant Permission Scoping
The Phase 10 AI Assistant tool execution registry (`backend/app/assistant/tool_registry.py`) receives the authenticated `user` context.
- Public users asking for restricted region datasets receive polite permission denial.
- Surveyors are scoped to their assigned regional datasets (`region_id`).
- Tool calls enforce region isolation before returning parcel, building, road, or review data.

---

## 8. Security Audit Findings
A basic security audit was performed across API endpoints:
1. **API Privilege Escalation**: Role values sent in HTTP bodies are strictly ignored; permissions are evaluated against the server-verified JWT session token.
2. **IDOR Prevention**: Regional queries check target `region_id` against the authenticated user's `region_id` assignment.
3. **No Secrets in Frontend**: `NEXT_PUBLIC_` environment variables contain zero tokens or secrets.
4. **Source Immutability**: All 30 UAV GeoTIFFs, 30 label masks, 834 AI building footprints, 35 synthetic parcels, and OSM reference vectors remain 100% immutable in read-only storage.

---

## 9. Verification & Test Baseline

### Backend Test Results (pytest):
```
=============== 376 passed, 1 skipped, 2860 warnings in 43.40s ================
```
- **Total Test Cases**: 377
- **Passed**: 376
- **Skipped**: 1 (GDAL native binary check on non-GIS environment)
- **Failed**: 0

### Frontend Production Build Results (Next.js):
```
✓ Compiled successfully in 4.9s
  Running TypeScript ...
  Finished TypeScript in 7.5s ...
✓ Generating static pages using 7 workers (26/26) in 947ms
```
- **TypeScript Errors**: 0
- **Build Errors**: 0

---

## 10. Data Source Classification

| Data Source | Classification Status |
| :--- | :--- |
| 30 UAVPal GeoTIFF Raster Tiles | `IMPLEMENTED` / `AI_DERIVED_UAVPAL` |
| 834 AI Building Footprints | `IMPLEMENTED` / `AI_DERIVED_UAVPAL` |
| 35 Demonstration Parcels | `SYNTHETIC_DEMO` (*"Synthetic prototype data — not an official land record."*) |
| 2,933 OSM Reference Roads | `REFERENCE_GIS` |
| 98 OSM Land-Use Polygons | `REFERENCE_GIS` |
| Reviewed Geometry Edits | `REVIEWED_AI_GEOMETRY` |
| Field Verification Records | `FIELD_VERIFIED` |
| Phase 11 Auth & Governance | `IMPLEMENTED` |

---

## 11. Known Limitations & Future Improvements
- **Google OAuth Integration**: Abstraction ready; requires production GCP Client ID & Secret configuration for live deployment.
- **Role Scoping Fine-Grained Policy**: Future iterations can add custom polygon boundary access constraints per surveyor.
