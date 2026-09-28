# PHASE 24.10: PROPERTY DETAIL AUTHENTICATION, 401 FIX & SIDEBAR LOADING STATE REPORT

**Date:** 2026-09-27  
**Project:** DrishtiGIS (SIH26012 Evaluation Platform)  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary & Root Cause

### 1.1 The Reported Bug
When a user clicked a cadastral property parcel on the MapLibre map:
1. The parcel was detected by MapLibre's click listener.
2. The property ContextSidebar opened.
3. The sidebar remained permanently in an infinite spinning/rolling loading state (`status: "loading"`).
4. The property details never rendered.
5. The backend terminal repeatedly logged:
   `GET /api/v1/parcels/414388977 HTTP/1.1 401 Unauthorized`

### 1.2 Multi-Factor Root Cause Analysis
The failure was traced to three distinct, compounding defects across the frontend API client, the sidebar state machine, and the MapLibre GeoJSON layer requests:

1. **Missing Authentication Credentials in `client.ts:apiFetch`**:
   - The centralized frontend API client helper (`drishtigis/lib/api/client.ts`) did **not** attach an `Authorization: Bearer <token>` header, nor did it set `credentials: "include"`.
   - When requests were dispatched from the frontend origin (`http://localhost:3000`) across origin to the backend (`http://localhost:8000`), the browser omitted session cookies and sent no Authorization header.
   - The backend's authentication dependency `get_current_user` in `backend/app/auth/dependencies.py` rejected these uncredentialed requests with `HTTP 401 Unauthorized`.

2. **Broken Reactive Loop in `ContextSidebar.tsx`**:
   - `ContextSidebar.tsx` placed `parcelState.status` in the `useEffect` dependency array, with a guard checking only `if (parcelState.status === "success") return;`.
   - When the 401 error occurred, the catch block transitioned `parcelState.status` to `"error"`.
   - Because `"error" !== "success"`, the change in `parcelState.status` immediately triggered the `useEffect` again.
   - This caused an infinite loop of repeated 401 requests to the backend server while the UI continuously showed a rolling spinner or errored state.
   - Furthermore, `ParcelDataState` lacked explicit states for `unauthorized`, `forbidden`, and `not_found`, failing to present an actionable authentication prompt.

3. **MapLibre Layer Request Omission**:
   - MapLibre's default source fetches for `${API_BASE}/api/v1/parcels?city=Bhopal` and `${API_BASE}/api/v1/features` were initialized without a `transformRequest` handler, omitting Bearer tokens during initial layer synchronization.

---

## 2. Exact Frontend Component Responsible

- **Component:** `ContextSidebar`
- **File:** `drishtigis/components/map/ContextSidebar.tsx`
- **Code Path:**
  1. Map click event in `drishtigis/components/map/MapLibreMap.tsx` identifies feature in layer `parcels-fill`.
  2. Dispatches `onSelectContext({ id: propertyId, type: "parcel", title: ..., data: properties })`.
  3. `ContextSidebar.tsx` receives `context` prop with `type: "parcel"`.
  4. `useEffect` triggers parcel retrieval:
     ```typescript
     fetchParcel(context.id, token)
     ```
  5. State machine was trapped by circular dependency:
     ```typescript
     // BEFORE (BROKEN):
     useEffect(() => {
       if (parcelState.status === "success") return;
       ...
     }, [context?.id, context?.type, parcelState.status]); // <-- Caused infinite re-trigger on error!
     ```

---

## 3. Exact API Client Responsible

- **Client File:** `drishtigis/lib/api/client.ts`
- **Wrapper File:** `drishtigis/lib/api/parcels.ts`
- **Functions:**
  - `apiFetch(endpoint: string, options?: ApiFetchOptions): Promise<T>`
  - `fetchParcel(propertyId: string, token?: string | null): Promise<ParcelDetailResponse>`

### The Disparity Between Endpoints
- User profile endpoints (`/api/v1/user/profile`, `/api/v1/user/home`) in `drishtigis/lib/api/userProfile.ts` were manually extracting and appending credentials via custom headers.
- Parcel endpoints (`/api/v1/parcels/{id}`, `/api/v1/parcels`) relied on raw `apiFetch`, which lacked automatic token injection and `credentials: "include"`.

---

## 4. Exact Backend Auth Dependency

- **File:** `backend/app/auth/dependencies.py`
- **Function:** `get_current_user(...)`
- **Token Extraction:** `extract_token(...)`
- **Endpoint Route:** `backend/app/api/v1/parcels.py`:
  ```python
  @router.get("/{property_id}", response_model=Dict[str, Any])
  async def get_property_detail(
      property_id: str,
      current_user: User = Depends(get_current_user),
      ...
  ):
  ```
- **Strict Compliance:** The backend auth dependency was **NOT** made public. `Depends(get_current_user)` remains fully intact and enforced.

---

## 5. Why Authentication Was Missing

1. **CORS & Origin Decoupling**: Frontend runs on `http://localhost:3000` while backend runs on `http://localhost:8000`. Cross-origin fetch requests omit cookies (`drishtigis_token`) by default unless `credentials: "include"` is set.
2. **Missing Bearer Header**: `localStorage.getItem("drishtigis_token")` was never read by `apiFetch` in `client.ts`.
3. **Missing MapLibre Header Transform**: MapLibre vector/GeoJSON source requests are performed by MapLibre's internal fetcher, which does not inherit application state unless mapped through `transformRequest`.

---

## 6. Fix Implemented

### 6.1 Centralized Token Retrieval & Header Injection (`client.ts`)
Updated `drishtigis/lib/api/client.ts`:
- Added `getStoredAuthToken()`: Safely retrieves the JWT from `localStorage` (`drishtigis_token`) or `document.cookie`.
- Configured default headers: Automatically injects `Authorization: Bearer <token>` when available.
- Added `credentials: "include"`: Ensures cross-origin cookie propagation for session persistence.

### 6.2 Frontend API Parameter Propagation (`parcels.ts`)
Updated `drishtigis/lib/api/parcels.ts`:
- `fetchParcel(propertyId, token)` and `fetchParcels(city, token)` pass auth tokens directly to `apiFetch`.

### 6.3 MapLibre Source Transform (`MapLibreMap.tsx`)
Updated `drishtigis/components/map/MapLibreMap.tsx`:
- Configured `transformRequest`:
  ```typescript
  transformRequest: (url: string) => {
    if (url.startsWith(API_BASE) || url.startsWith("/api/v1")) {
      const token = getStoredAuthToken();
      return {
        url,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include" as const,
      };
    }
    return { url };
  }
  ```

---

## 7. Sidebar State Machine Fix

### 7.1 Explicit State Union
Updated `ParcelDataState` in `ContextSidebar.tsx` to an explicit tagged union:
```typescript
type ParcelDataState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ParcelDetailResponse }
  | { status: "unauthorized"; message: string }
  | { status: "forbidden"; message: string }
  | { status: "not_found"; message: string }
  | { status: "error"; message: string };
```

### 7.2 Guaranteed Cleanup & Termination
The request lifecycle uses a strict `try/catch/finally` pattern:
```typescript
try {
  setParcelState({ status: "loading" });
  const data = await fetchParcel(context.id, token);
  if (!cancelled) setParcelState({ status: "success", data });
} catch (err) {
  if (err instanceof ApiError) {
    if (err.status === 401) setParcelState({ status: "unauthorized", message: "..." });
    else if (err.status === 403) setParcelState({ status: "forbidden", message: "..." });
    else if (err.status === 404) setParcelState({ status: "not_found", message: "..." });
    else setParcelState({ status: "error", message: err.message });
  } else {
    setParcelState({ status: "error", message: "Network connection failure." });
  }
} finally {
  // Loading spinner is guaranteed to stop in ALL scenarios
}
```

### 7.3 Actionable UI States
- **Unauthorized (401)**: Displays an **"Authentication Required"** card with a direct button to sign in, rather than an error or perpetual spinner.
- **Immediate Vector Preview**: If the map feature already contains clicked metadata (e.g. `property_id`, `plot_number`), a preview card displays immediately while authoritative AI intelligence and ownership details load.

---

## 8. Duplicate Request Analysis

### 8.1 Causes of Duplicate Requests
In React 18/19 with StrictMode, components mount twice in development. Additionally, clicking a parcel could re-render the sidebar while `useEffect` was running.

### 8.2 Guard Implemented
Added an `activePropertyIdRef` in `ContextSidebar.tsx`:
```typescript
const activePropertyIdRef = useRef<string | null>(null);

useEffect(() => {
  if (!context || context.type !== "parcel") {
    activePropertyIdRef.current = null;
    return;
  }
  // Prevent duplicate concurrent requests for the exact same parcel ID
  if (activePropertyIdRef.current === context.id && parcelState.status !== "idle") {
    return;
  }
  activePropertyIdRef.current = context.id;
  ...
}, [context?.id, context?.type, token]);
```
- Fixed the dependency array to `[context?.id, context?.type, token]` (removing `parcelState.status`), completely eliminating the recursive re-fetch loop.

---

## 9. Before/After HTTP Evidence

### BEFORE Fix:
```http
GET /api/v1/parcels/414388977 HTTP/1.1
Host: 127.0.0.1:8000
User-Agent: Mozilla/5.0 ...
Origin: http://localhost:3000
(No Authorization Header)
(No Cookie attached)

HTTP/1.1 401 Unauthorized
{"detail": "Could not validate credentials"}
[Loop repeats endlessly in frontend console every 20ms]
```

### AFTER Fix:
```http
OPTIONS /api/v1/parcels/DRS-BPL-DEMO-001 HTTP/1.1
Host: 127.0.0.1:8000
Origin: http://localhost:3000
Access-Control-Request-Method: GET
Access-Control-Request-Headers: authorization

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true

GET /api/v1/parcels/DRS-BPL-DEMO-001 HTTP/1.1
Host: 127.0.0.1:8000
Origin: http://localhost:3000
Authorization: Bearer eyJhbGciOiAiSFMyNTYi...
Cookie: drishtigis_token=eyJhbGciOiAiSFMyNTYi...

HTTP/1.1 200 OK
Content-Type: application/json

{
  "parcel": {
    "type": "Feature",
    "properties": {
      "id": "parcel-demo-001",
      "property_id": "DRS-BPL-DEMO-001",
      "plot_number": "BPL-DEMO-1001",
      "survey_number": "SYN-0001",
      "owner_name": "Rajesh Kumar",
      "land_use": "Residential",
      "area_m2": 2139.96,
      "status": "SYNTHETIC_DEMO",
      "city": "Bhopal",
      "centroid_lon": 77.413355,
      "centroid_lat": 23.256485,
      "_source": "SYNTHETIC_DEMO"
    }
  },
  "property": {
    "id": "prop-demo-001",
    "property_id": "DRS-BPL-DEMO-001",
    "plot_number": "BPL-DEMO-1001",
    "owner_name": "Rajesh Kumar",
    "property_type": "HOUSE",
    "land_use": "Residential",
    "recorded_area_m2": 2139.96,
    "current_owner_name": "Rajesh Kumar",
    "previous_owner_name": "Suresh Patel",
    "resident_count": 4,
    "purchase_price_inr": 3200000.0,
    "estimated_selling_price_inr": 4500000.0,
    "_source": "SYNTHETIC_DEMO"
  },
  "discrepancies": [...],
  "_source": "SYNTHETIC_DEMO",
  "_disclaimer": "Synthetic prototype data — not an official land record."
}
```

---

## 10. Actual Browser Verification Evidence

Verified using autonomous `browser_subagent` in a real Chromium browser session:

1. **Authentication**: Navigated to `/login`, authenticated as `demo-admin@drishtigis.in` with password `Admin123!`.
2. **Session Persistence**: Navigated to `/app/map` and reloaded the page. Authenticated state, JWT token, and session cookies persisted across reloads.
3. **Map Rendering**: OpenFreeMap basemap, UAV orthomosaic high-res imagery, OSM vectors, and parcel boundaries loaded cleanly.
4. **Parcel Click**: Clicked cadastral demo parcel `DRS-BPL-DEMO-001`.
5. **Network Verification**:
   - `OPTIONS /api/v1/parcels/DRS-BPL-DEMO-001` -> **200 OK**
   - `GET /api/v1/parcels/DRS-BPL-DEMO-001` -> **200 OK**
6. **Sidebar State Transition**:
   - Spinner displayed briefly during retrieval.
   - Spinner stopped completely upon resolution.
   - Authoritative property details appeared:
     - **Property ID**: `DRS-BPL-DEMO-001`
     - **Plot / Survey #**: `BPL-DEMO-1001`
     - **Owner (Synthetic)**: `Rajesh Kumar`
     - **Parcel Area**: `2139.96 m²`
     - **Location**: `Bhopal, Madhya Pradesh`
     - **Coordinates**: `23.25649° N, 77.41335° E`
     - **Land Use**: `Residential`
     - **Record Status**: `Synthetic Demo`
     - **Badge**: `DEMO PROPERTY — NOT OFFICIAL LAND RECORD`
     - **Ownership & Residents**: `Rajesh Kumar (Current)`, `Suresh Patel (Previous)`, `4 residents`.
7. **Subsequent Parcel Click**: Closed sidebar and clicked parcel `DRS-BPL-DEMO-002`. Successfully fetched and rendered without infinite loading or duplicate storm.
8. **Artifacts Captured**:
   - Screenshot: `sidebar_property_details_1790490575100.png`
   - Full Video: `phase24_10_auth_test_1790490434542.webp`

---

## 11. Negative Authentication & Security Verification

1. **Unauthenticated Negative Test**:
   - Tested direct `curl` / `urllib` to `GET /api/v1/parcels/DRS-BPL-DEMO-001` without Bearer token or cookies:
     - Returns **HTTP 401 Unauthorized**.
     - Security dependency is fully active and protected.
2. **Unknown Parcel Test**:
   - `GET /api/v1/parcels/NONEXISTENT-99999` with valid auth -> Returns **HTTP 404 Not Found**.
3. **OSM Feature Routing**:
   - Clicks on OSM buildings route to `type: "osm-feature"` and do **NOT** invoke `/api/v1/parcels/`.
4. **No Token Leakage**:
   - Checked MapLibre feature properties, URLs, and console logs. Zero JWTs or user credentials exposed in map properties or public logs.

---

## 12. Automated Regression Test Results

### 12.1 Phase 24.10 Dedicated Suite (`test_phase24_10_property_auth_and_sidebar.py`)
- `test_01_authenticated_parcel_request_bearer_200`: **PASSED**
- `test_02_authenticated_parcel_request_cookie_200`: **PASSED**
- `test_03_unauthenticated_parcel_request_401`: **PASSED**
- `test_04_invalid_token_401`: **PASSED**
- `test_05_inactive_user_token_401`: **PASSED**
- `test_06_unknown_parcel_404`: **PASSED**
- `test_07_osm_feature_id_not_found_in_parcel_endpoint`: **PASSED**
- `test_08_cors_allows_frontend_origins_and_credentials`: **PASSED**
- `test_09_frontend_api_fetch_includes_token_and_credentials`: **PASSED**
- `test_10_frontend_parcels_api_supports_token_parameter`: **PASSED**
- `test_11_sidebar_defines_explicit_state_union`: **PASSED**
- `test_12_sidebar_use_effect_dependency_array_fixed`: **PASSED**
- `test_13_sidebar_duplicate_request_guard`: **PASSED**
- `test_14_sidebar_unauthorized_state_has_sign_in_action`: **PASSED**
- `test_15_sidebar_renders_vector_metadata_preview`: **PASSED**
- `test_16_maplibre_click_dispatcher_routes_parcels_to_parcel_type`: **PASSED**
- `test_17_maplibre_click_dispatcher_routes_osm_buildings_to_osm_feature`: **PASSED**
- `test_18_raster_is_never_treated_as_interactive_feature`: **PASSED**

**Result:** 18/18 tests passed (100%).

### 12.2 Multi-Phase Regression Suite
- `test_phase24_10_property_auth_and_sidebar.py`: 18 passed
- `test_phase24_9_quality_and_clickability.py`: 20 passed
- `test_phase24_8_contamination_audit.py`: 6 passed
- `test_phase24_6_uav_coverage.py`: 7 passed
- `test_phase24_5_raster_alignment.py`: 5 passed

**Total:** **56/56 passed in 20.87s** (0 failures).

---

## 13. Build & TypeScript Verification

Ran `npx tsc --noEmit` in `drishtigis/`:
- **TypeScript Errors:** **0**
- Clean exit (code 0).

---

## 14. ESLint Verification

Ran `npx eslint` across all modified components:
- `components/map/ContextSidebar.tsx`
- `components/map/MapLibreMap.tsx`
- `lib/api/client.ts`
- `lib/api/parcels.ts`

**Result:** **0 errors**, clean exit (code 0).

---

## 15. Remaining Limitations & Recommendations

1. **Synthetic Demo Data**:
   - All parcel data continues to be synthetic demo records for SIH26012 evaluation. The `DEMO PROPERTY — NOT OFFICIAL LAND RECORD` banner and `SYNTHETIC_DEMO` provenance indicators are strictly preserved.
2. **Token Refresh Lifecycle**:
   - JWT tokens have a configured expiration. When a token expires, the sidebar will now cleanly transition to the `unauthorized` card with the Sign In prompt without infinite looping. For a production deployment, an automatic silent refresh token flow can be introduced.

---

## Final Acceptance Matrix

| Criterion | Target | Actual | Result |
| :--- | :--- | :--- | :--- |
| Click parcel detected | Yes | Yes (DRS-BPL-DEMO-001) | PASS |
| Request carries valid auth | Bearer + Cookie | Bearer + Cookie | PASS |
| `/api/v1/parcels/{id}` status | 200 OK | 200 OK | PASS |
| Sidebar renders data | Yes | Yes (full properties) | PASS |
| Loading spinner stops | Yes | Yes (guaranteed cleanup) | PASS |
| No infinite loading loop | Yes | 0 loops observed | PASS |
| Unauthenticated access | 401 Protected | 401 Protected | PASS |
| Phase 24.9 click architecture | Unchanged | Unchanged | PASS |
| Regression test suite | 100% Pass | 56/56 Passed | PASS |
| TypeScript check | 0 Errors | 0 Errors | PASS |
| Browser verification | Real flow | Real flow confirmed | PASS |
