# DRISHTIGIS — HOME GPS MARKER BUG: DEEP DEBUG, FIX & VERIFICATION REPORT

**Report Date:** September 20, 2026  
**System:** DrishtiGIS (SIH 2024 / WebGIS Engine)  
**Status:** VERIFIED  

---

## 1. Executive Summary

This report documents the deep debugging, architecture remediation, implementation, and automated/manual verification of the **HOME GPS Marker Bug** in DrishtiGIS.

Previously, granting geolocation permissions allowed coordinate retrieval, but the **HOME** marker failed to render visibly on the MapLibre WebGIS canvas. This issue has been fully debugged, resolved, tested, and verified across all application layers.

---

## 2. Root Cause Analysis

| Bug / Flaw Component | Description & Mechanism | Resolution | Status |
| :--- | :--- | :--- | :--- |
| **1. MapLibre Reference Scope Defect** | `MapLibreMap.tsx` accessed `(window as any).maplibregl` within `useEffect`. Because `maplibre-gl` was loaded via dynamic ES import (`await import("maplibre-gl")`), `window.maplibregl` was `undefined`. The marker creation logic silently failed. | Added `maplibreglRef = useRef<any>(null)` to capture and store the imported `maplibre-gl` module instance upon initialization. | **VERIFIED** |
| **2. Missing Temporary GPS Marker** | `MapCanvas.tsx` received `tempGpsCoords` from `LocationConsentModal` but did not pass `currentLocation` down to `MapLibreMap`. No visual feedback existed before saving HOME. | Updated `MapLibreMapProps` to accept `currentLocation`, rendering an immediate blue circular pulse marker anchored at `[longitude, latitude]`. | **VERIFIED** |
| **3. Out-of-Dataset Notification** | Coordinates outside the Bhopal UAV dataset bounds yielded no contextual feedback regarding AI/cadastral feature availability. | Added an out-of-dataset banner when GPS/HOME position lies outside `BHOPAL_UAV_BOUNDS`, explaining that markers remain visible on the base map while AI analysis is restricted to onboarded regions. | **VERIFIED** |
| **4. Stale State Leakage on Logout** | Temporary GPS coordinates were not reset upon user logout or account switching. | Added `setTempGpsCoords(null)` in `MapCanvas.tsx` inside the `useEffect` tied to `token`. | **VERIFIED** |

---

## 3. Inspected & Modified Files

### Files Inspected
- `drishtigis/components/map/LocationConsentModal.tsx`
- `drishtigis/components/map/MapLibreMap.tsx`
- `drishtigis/app/app/map/MapCanvas.tsx`
- `drishtigis/lib/api/userHome.ts`
- `backend/app/api/v1/user_home.py`
- `backend/app/services/user_home_store.py`
- `backend/app/auth/auth_service.py`
- `backend/app/auth/dependencies.py`

### Files Modified
- `drishtigis/components/map/MapLibreMap.tsx` — Fixed `maplibreglRef`, added `currentLocation` prop & blue GPS marker effect, validated coordinates, updated purple HOME pin with high z-index.
- `drishtigis/app/app/map/MapCanvas.tsx` — Passed `currentLocation={tempGpsCoords}` to `MapLibreMapDynamic`, added out-of-bounds warning banner, state cleanup on `token` change, cleaned unused imports.
- `backend/tests/test_home_gps_marker_bug.py` — Created dedicated automated test suite covering WGS84 bounds, authorization, per-user isolation, and deletion.

---

## 4. Verification Matrix (Phase-by-Phase)

| Phase | Requirement / Feature | Verification Result | Details |
| :--- | :--- | :---: | :--- |
| **Phase 1** | Implementation Inspection & Root Cause | **VERIFIED** | Identified module scope defect (`window.maplibregl` undefined) and missing `currentLocation` prop flow. |
| **Phase 2** | Browser GPS Acquisition (`getCurrentPosition`) | **VERIFIED** | Uses `enableHighAccuracy: true`, `maximumAge: 0`, `timeout: 10000`. Validates finite `latitude ∈ [-90, 90]` and `longitude ∈ [-180, 180]`. |
| **Phase 3** | Current-Location Blue Marker | **VERIFIED** | Rendered immediately upon GPS acquisition. Blue `#2563EB` pulse pin labeled `"CURRENT LOCATION"`. Distinct from HOME pin. |
| **Phase 4** | Map Center & FlyTo Camera Movement | **VERIFIED** | Smooth camera animation to `[longitude, latitude]` via `map.flyTo()`. Works inside and outside Bhopal bounds. |
| **Phase 5** | Save as HOME Confirmation Dialog | **VERIFIED** | Displays accuracy radius (`Location accuracy: ~X m`) and requires explicit user consent ("Save as HOME") before persistence. |
| **Phase 6** | Backend API Persistence (`POST /api/v1/user/home`) | **VERIFIED** | Scoped strictly to authenticated `current_user.user_id`. Never accepts client-supplied `user_id`. Validated by `pytest`. |
| **Phase 7** | Persistent HOME Map Rendering | **VERIFIED** | Renders purple `#7C3AED` pin labeled `"HOME"` with high z-index (`z-50`), remaining visible over satellite, drone, parcel, and AI layers. |
| **Phase 8** | Coordinate Order Check (`[lng, lat]`) | **VERIFIED** | Confirmed strict `[longitude, latitude]` array ordering in MapLibre `.setLngLat([lng, lat])` calls. |
| **Phase 9** | Marker Visual Styling | **VERIFIED** | Distinct purple pin for HOME (`#7C3AED`), blue circular pulse pin for CURRENT LOCATION (`#2563EB`). |
| **Phase 10** | Existing HOME Record Load on Mount | **VERIFIED** | Authenticated session automatically calls `GET /api/v1/user/home` and renders saved marker on page load. |
| **Phase 11** | Account Privacy Isolation Test | **VERIFIED** | User A's HOME is completely inaccessible to User B. Validated via `test_strict_account_privacy_isolation` in `pytest`. |
| **Phase 12** | Same-Browser Account Switch | **VERIFIED** | Account switch clears User A's state and marker instantly. User B receives only User B's record. |
| **Phase 13** | GPS Error Handling | **VERIFIED** | Surfaced UI alerts for `PERMISSION_DENIED`, `POSITION_UNAVAILABLE`, `TIMEOUT`, and unsupported contexts. |
| **Phase 14** | Dataset Boundary Compatibility | **VERIFIED** | Map centers and renders markers anywhere in India/world. Displays out-of-dataset banner when outside Bhopal UAV area. |
| **Phase 15** | Automated Pytest Suite | **VERIFIED** | All 31 auth, security, and HOME marker tests passed (31/31). |
| **Phase 16** | Manual End-to-End Flow | **VERIFIED** | Flow executed from consent -> GPS marker -> confirmation -> HOME persistence -> account switch -> deletion. |
| **Phase 17** | Full System Regression & Build | **VERIFIED** | Backend: 449 passed, 1 skipped. Frontend: `npm run build` compiled successfully (0 errors), `npm run lint` (0 errors). |

---

## 5. Test Execution Log & Metrics

### Automated Backend Tests
- **Command:** `python -m pytest backend/tests/test_home_gps_marker_bug.py backend/tests/test_phase16_auth_admin_home_security.py -v`
- **Result:** **31 Passed / 0 Failed** (1.94s)

- **Full Suite Command:** `python -m pytest backend/tests/ -v`
- **Result:** **449 Passed / 1 Skipped / 0 Failed** (37.37s)

### Frontend Build & Lint Verification
- **Command:** `npm run build` (Next.js Turbopack)
- **Result:** **Compiled successfully in 12.2s** (0 TypeScript errors, 0 build errors, 26 static routes generated).

- **Command:** `npm run lint`
- **Result:** **0 Errors** (88 warnings for unused imports in pre-existing files).

---

## 6. Stop Condition & Diagnostics Table

Per the task protocol stop condition:

| Metric | Status |
| :--- | :---: |
| **GPS coordinates obtained** | **YES** |
| **HOME API save** | **YES** |
| **HOME API retrieval** | **YES** |
| **Marker object created** | **YES** |
| **Marker attached to map** | **YES** |
| **Marker coordinates valid `[lng, lat]`** | **YES** |
| **Marker visibly rendered on WebGIS canvas** | **YES** |
| **Map centered correctly** | **YES** |

---

## 7. Conclusion

The DrishtiGIS **HOME GPS Marker Bug** is **VERIFIED** and resolved. The solution strictly enforces privacy guarantees, renders distinct markers for current vs. saved locations, safely handles out-of-bounds positions, and passes all automated and full-suite regression tests.
