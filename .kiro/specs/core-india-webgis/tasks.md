# Spec: Core India WebGIS Integration
## Implementation Tasks

**Spec ID:** core-india-webgis  
**Version:** 0.1  
**Alignment:** CLAUDE.md · DOC/PRD.md · DOC/requirements.md

---

## Task Execution Rules

1. Execute tasks in order. Each task has acceptance criteria — verify before proceeding.
2. After each task: run acceptance checks, inspect git diff, update `progress.md`.
3. Stop if any acceptance criterion fails — diagnose before continuing.
4. `Dataset/` is read-only throughout. Verify byte-exact integrity after each task group.
5. No fabricated data may be introduced. Every data assertion is traceable to a real asset.
6. All backend tasks run in the main Python 3.14 environment (not the GIS venv).
7. All frontend tasks run in the `drishtigis/` directory with Node 24.

---

## Phase A — Backend Infrastructure

### Task A.1 — Backend GIS package structure + config additions

**Goal:** Create the `backend/app/gis/` package and add data path settings.

**Steps:**
1. Create `backend/app/gis/__init__.py` (empty package marker)
2. Add to `backend/app/core/config.py`:
   ```python
   # Data paths — resolved absolute from repo root at startup
   # These are not served directly; only specific processed outputs are served
   DATA_DIR: str = ""   # left empty — computed in endpoints using Path(__file__)
   ```
   No change needed to the existing settings — the path resolution is done per-endpoint using `Path(__file__).resolve().parents[N]`. Document this in config comments.
3. Verify: `python -c "from app.core.config import settings; print('config OK')"` (run from `backend/`)

**Acceptance Criteria:**
- [ ] `backend/app/gis/__init__.py` exists
- [ ] Config imports without error
- [ ] No hardcoded filesystem paths added to config values

---

### Task A.2 — India cities static data

**Goal:** Create the static India city list that backs city search and coverage lookups.

**Steps:**
1. Create `backend/app/gis/india_cities.py` with `IndiaCity` dataclass and `INDIA_CITIES` list (minimum 20 cities as per design.md §3.5)
2. Add `get_city(name: str) -> Optional[IndiaCity]` function (case-insensitive name match)
3. Add `search_cities(query: str, limit: int = 10) -> list[IndiaCity]` (substring match on name and state)
4. Verify: import and call `search_cities("Bhopal")` — must return exactly the Bhopal entry

**Acceptance Criteria:**
- [ ] `india_cities.py` exists with ≥ 20 cities
- [ ] Bhopal is in the list with correct coordinates (23.2599, 77.4126)
- [ ] `get_city("bhopal")` returns the Bhopal entry (case-insensitive)
- [ ] `search_cities("Delhi")` returns at least Delhi
- [ ] `search_cities("xyz_nonexistent")` returns empty list (no crash)
- [ ] No city in the list has `imagery_available=True` — that's the coverage registry's job

---

### Task A.3 — Coverage registry

**Goal:** Create the `CoverageAvailability` data model and Bhopal registry.

**Steps:**
1. Create `backend/app/gis/coverage_registry.py` with:
   - `CoverageSource` enum (`prototype`, `production`, `none`)
   - `CoverageAvailability` dataclass
   - `BHOPAL_COVERAGE` constant (with exact values from REQ-COV-03)
   - `get_coverage(city_name: str) -> CoverageAvailability` function
   - `coverage_to_dict(c: CoverageAvailability) -> dict` serializer
2. Verify Bhopal values:
   - `imagery_available = True`
   - `parcel_data_available = True`
   - `ai_analysis_available = True`
   - `historical_data_available = False` — must be False, never True
   - `coverage_source = "prototype"`
   - `disclaimer` is a non-empty string
3. Verify non-Bhopal: `get_coverage("Lucknow")` returns `imagery_available=False`, `coverage_source="none"`

**Acceptance Criteria:**
- [ ] `coverage_registry.py` exists
- [ ] `BHOPAL_COVERAGE.historical_data_available is False`
- [ ] `BHOPAL_COVERAGE.coverage_source == "prototype"`
- [ ] `get_coverage("lucknow").imagery_available is False`
- [ ] `get_coverage("lucknow").disclaimer is None`
- [ ] `coverage_to_dict` returns a JSON-serializable dict

---

### Task A.4 — Raster tile endpoint

**Goal:** Implement `GET /api/v1/tiles/bhopal/{z}/{x}/{y}.png` with full security controls.

**Steps:**
1. Create `backend/app/api/v1/tiles.py` as per design.md §3.2
2. Key implementation details:
   - `TILES_BASE = Path(__file__).resolve().parents[4] / "data" / "processed" / "tiles" / "bhopal"`
   - Use FastAPI `Path(ge=0, le=30)` validators for `z`; `Path(ge=0)` for `x`, `y`
   - Zoom range check: `if not (18 <= z <= 21): raise HTTPException(404)`
   - Path traversal guard: resolve path, confirm it starts with `TILES_BASE.resolve()`
   - `FileResponse` with `media_type="image/png"` and `Cache-Control: public, max-age=3600`
3. Register in `backend/app/main.py`:
   ```python
   from app.api.v1 import tiles
   app.include_router(tiles.router, prefix="/api/v1/tiles", tags=["tiles"])
   ```
4. Run backend and test manually:
   ```bash
   curl -I http://localhost:8000/api/v1/tiles/bhopal/18/187445/113652.png
   ```

**Acceptance Criteria:**
- [ ] `GET /api/v1/tiles/bhopal/18/187445/113652.png` returns HTTP 200 with `Content-Type: image/png`
- [ ] Response body is non-empty (> 500 bytes)
- [ ] `Cache-Control: public, max-age=3600` present in response headers
- [ ] `GET /api/v1/tiles/bhopal/17/187445/113652.png` returns HTTP 404 (zoom out of range)
- [ ] `GET /api/v1/tiles/bhopal/18/0/0.png` returns HTTP 404 (tile doesn't exist)
- [ ] `GET /api/v1/tiles/bhopal/18/abc/113652.png` returns HTTP 422 (non-integer)
- [ ] `Dataset/` files are inaccessible through this endpoint (tested with path traversal attempt)

---

### Task A.5 — OSM layer endpoints

**Goal:** Implement `GET /api/v1/osm/bhopal/{layer}` for four layers.

**Steps:**
1. Create `backend/app/api/v1/osm_layers.py` as per design.md §3.3
2. Key implementation:
   - `OSM_BASE = Path(__file__).resolve().parents[4] / "data" / "osm" / "bhopal-extract"`
   - `ALLOWED_LAYERS = frozenset(["buildings", "roads", "waterways", "landuse"])`
   - Strict allowlist check before any file access
   - `FileResponse` with `media_type="application/geo+json"` and OSM attribution headers
3. Register in `main.py`:
   ```python
   from app.api.v1 import osm_layers
   app.include_router(osm_layers.router, prefix="/api/v1/osm", tags=["osm"])
   ```
4. Verify headers on response:
   - `X-OSM-Attribution: © OpenStreetMap contributors, ODbL`
   - `X-Data-Source: OSM_OPENSTREETMAP`
   - `Cache-Control: public, max-age=1800`

**Note:** `FileResponse` does not add `_source` or `_disclaimer` fields to the JSON body — these are already present in the GeoJSON files themselves (added during Phase 3 extraction). The response headers carry the attribution separately for HTTP-level consumers.

**Acceptance Criteria:**
- [ ] All 4 layers return HTTP 200 with `Content-Type: application/geo+json` or `application/json`
- [ ] `X-OSM-Attribution` header present on all 4 layer responses
- [ ] `GET /api/v1/osm/bhopal/schools` returns HTTP 404
- [ ] `GET /api/v1/osm/bhopal/_bbox_nodes` returns HTTP 404
- [ ] `GET /api/v1/osm/bhopal/extraction_report` returns HTTP 404
- [ ] Response body is valid GeoJSON (parseable)
- [ ] Response body `_source == "OSM_OPENSTREETMAP"` (from file content)

---

### Task A.6 — Coverage and location search endpoints

**Goal:** Implement `GET /api/v1/coverage/{city_slug}` and `GET /api/v1/locations/search`.

**Steps:**
1. Create `backend/app/api/v1/coverage.py`:
   - Single endpoint: `GET /{city_slug}`
   - Normalizes slug: `city_name = city_slug.replace("-", " ").title()`
   - Calls `get_coverage(city_name)` from registry
   - Returns `JSONResponse(content=coverage_to_dict(coverage))`
2. Create `backend/app/api/v1/locations.py`:
   - `GET /search?q={query}&country=India`
   - Calls `search_cities(q)` from `india_cities.py`
   - For each match, calls `get_coverage(city.name)` for the coverage field
   - Returns `{"query": q, "results": [...], "total": N}`
3. Register both in `main.py`
4. Test Bhopal coverage returns `historical_data_available: false`
5. Test Lucknow coverage returns `imagery_available: false`

**Acceptance Criteria:**
- [ ] `GET /api/v1/coverage/bhopal` returns `imagery_available: true`, `historical_data_available: false`
- [ ] `GET /api/v1/coverage/lucknow` returns `imagery_available: false`, `parcel_data_available: false`
- [ ] `GET /api/v1/coverage/new-delhi` returns `coverage_source: "none"` (hyphenated slug)
- [ ] `GET /api/v1/locations/search?q=Bhopal` returns ≥ 1 result
- [ ] `GET /api/v1/locations/search?q=Bhopal` result has `coverage.imagery_available: true`
- [ ] `GET /api/v1/locations/search?q=Lucknow` result has `coverage.parcel_data_available: false`
- [ ] `GET /api/v1/locations/search?q=InvalidCity123` returns `total: 0`, no crash

---

### Task A.7 — Parcel endpoint: non-Bhopal coverage note

**Goal:** Add the `_coverage_note` field to parcel list responses for non-Bhopal cities (REQ-PARCEL-02).

**Steps:**
1. Modify `backend/app/api/v1/parcels.py` — update `list_parcels`:
   ```python
   if city and city.lower() != "bhopal":
       response_body = {
           "type": "FeatureCollection",
           "total": 0,
           "features": [],
           "_source": "DEMO_DATA_PROTOTYPE_ONLY",
           "_coverage_note": f"No parcel data is available for {city.title()}. DrishtiGIS currently has prototype data for Bhopal only.",
           "_disclaimer": _DISCLAIMER,
       }
   ```
2. Verify existing Bhopal behavior is unchanged

**Acceptance Criteria:**
- [ ] `GET /api/v1/parcels?city=Bhopal` still returns 3 features (unchanged)
- [ ] `GET /api/v1/parcels?city=Lucknow` returns `total: 0`, `_coverage_note` present
- [ ] `_coverage_note` for Lucknow mentions "Lucknow" in the message
- [ ] `GET /api/v1/parcels?city=Delhi` similarly returns coverage note
- [ ] All existing acceptance tests from Phase 6 still pass

---

### Task A.8 — Write backend tests

**Goal:** Implement all tests from design.md §5.

**Steps:**
1. Create `backend/tests/test_webgis.py` with all test functions from design.md §§5.2–5.5
2. Run: `cd backend && python -m pytest tests/test_webgis.py -v`
3. All tests must pass — no skips

**Note on tile test:** The test for `GET /api/v1/tiles/bhopal/18/187445/113652.png` requires the tile file to exist at `data/processed/tiles/bhopal/18/187445/113652.png`. This file was created in Phase 2. Verify it exists before running.

**Acceptance Criteria:**
- [ ] All tile tests pass (valid tile, wrong zoom, nonexistent coords, path traversal, cache header)
- [ ] All OSM tests pass (all 4 layers, unknown layer, internal files blocked)
- [ ] All coverage/location tests pass (Bhopal flags, non-Bhopal flags, search)
- [ ] All parcel/AI tests pass (source classification, non-Bhopal note, discrepancy legal_status)
- [ ] `python -m pytest backend/tests/test_webgis.py -v` exits 0

---

### Task A.9 — Backend verification: start + smoke tests

**Goal:** Verify backend starts, docs load, and all new endpoints respond.

**Steps:**
1. Start: `uvicorn app.main:app --reload` from `backend/`
2. Verify `/docs` shows all new routers (tiles, osm, coverage, locations)
3. Run `pytest` one more time
4. Verify `Dataset/` integrity: PBF and sample TIFFs unchanged

**Acceptance Criteria:**
- [ ] Backend starts without import errors
- [ ] `/docs` shows tiles, osm, coverage, locations tags
- [ ] All tests pass
- [ ] `Dataset/india-260905.osm.pbf` size = 1,706,252,573 bytes (unchanged)
- [ ] `Dataset/Drone-Images/BHOPAL/00_00.tiff` size = 7,358,913 bytes (unchanged)

---

## Phase B — Frontend Integration

### Task B.1 — India geographic constants and coverage types

**Goal:** Create India-scale constants and TypeScript coverage types.

**Steps:**
1. Create `drishtigis/lib/gis/india.ts` with:
   - `INDIA_CENTER` constant (lat 20.5937, lon 78.9629, zoom 5)
   - `BHOPAL_CITY_CENTER` constant (lat 23.2599, lon 77.4126, zoom 12)
   - `COVERAGE_UNAVAILABLE_THRESHOLD_KM = 10`
   - `distanceKm(lat1, lon1, lat2, lon2): number` — haversine formula
2. Create `drishtigis/lib/gis/coverage.ts` with:
   - `CoverageSource` type
   - `CoverageAvailability` interface (mirroring backend exactly)
3. Verify TypeScript compilation: `npm run build` exits 0

**Acceptance Criteria:**
- [ ] `india.ts` exports `INDIA_CENTER`, `BHOPAL_CITY_CENTER`, `distanceKm`
- [ ] `coverage.ts` exports `CoverageAvailability` interface
- [ ] `distanceKm(23.2599, 77.4126, 23.2599, 77.4126)` returns 0
- [ ] `distanceKm(23.2599, 77.4126, 28.6139, 77.2090)` returns ~595 km (Delhi–Bhopal)
- [ ] `npm run build` exits 0 after adding these files

---

### Task B.2 — API client modules

**Goal:** Create typed API clients for all new backend endpoints.

**Steps:**
1. Create `drishtigis/lib/api/` directory with `index.ts` barrel
2. Create individual client files:
   - `tiles.ts` — `getBhopalTileUrl(): string` — returns the tile URL template
   - `osm.ts` — `fetchOsmLayer(layer: OsmLayer)` — fetches a GeoJSON layer
   - `parcels.ts` — `fetchParcels(city: string)`, `fetchParcel(propertyId: string)`
   - `coverage.ts` — `fetchCoverage(citySlug: string) -> CoverageAvailability`
   - `locations.ts` — `searchLocations(q: string)`
3. All clients read `NEXT_PUBLIC_API_URL` from `process.env` for the base URL
4. Add `NEXT_PUBLIC_API_URL=http://localhost:8000` to `drishtigis/.env.example`

**Acceptance Criteria:**
- [ ] All 5 client files exist
- [ ] `getBhopalTileUrl()` returns a string containing `{z}/{x}/{y}.png`
- [ ] All client functions are typed with correct return types
- [ ] No `any` type in the API client functions (unless unavoidable with `// eslint-disable-next-line`)
- [ ] `npm run build` exits 0

---

### Task B.3 — LayerControl component

**Goal:** Create the layer visibility toggle panel.

**Steps:**
1. Create `drishtigis/components/map/LayerControl.tsx` as per design.md §4.5
2. Use DrishtiGIS color tokens (forest, ochre, cream, charcoal, soft-gray)
3. Accessibility: `<fieldset>` with `<legend>`, `<label>` for each toggle
4. Ensure `prefers-reduced-motion` is respected for any animations
5. Verify it compiles without TypeScript errors

**Acceptance Criteria:**
- [ ] `LayerControl.tsx` exists and exports `LayerControl`
- [ ] All 7 layers are represented (UAV Imagery, Parcels, AI Features, OSM Roads, OSM Buildings, OSM Water, OSM Land Use)
- [ ] Component accepts `visibility` and `onChange` props with correct types
- [ ] No TypeScript errors
- [ ] `npm run build` exits 0

---

### Task B.4 — PropertyPanel component

**Goal:** Create the property detail panel that displays on parcel click.

**Steps:**
1. Create `drishtigis/components/map/PropertyPanel.tsx` as per design.md §4.6
2. Uses `fetchParcel(propertyId)` from the API client
3. Shows loading → data → error states
4. Displays all fields from REQ-PROP-02
5. Prototype disclaimer is always visible and not collapsible
6. `legal_status: null` means never showing legal language
7. Panel is dismissable (onClose callback)

**Acceptance Criteria:**
- [ ] `PropertyPanel.tsx` exists and exports `PropertyPanel`
- [ ] Accepts `propertyId: string | null` and `onClose: () => void`
- [ ] When `propertyId = null`, panel is hidden
- [ ] Loading state is shown during fetch
- [ ] Prototype disclaimer renders unconditionally
- [ ] Discrepancy section uses only safe language (no "illegal", "fraud", etc.)
- [ ] TypeScript compiles without errors

---

### Task B.5 — CoverageIndicator component

**Goal:** Create the non-Bhopal area indicator.

**Steps:**
1. Create `drishtigis/components/map/CoverageIndicator.tsx` as per design.md §4.7
2. When `nearBhopal = false`: shows the approved message: "Detailed AI/property analysis is not yet available for this area. Showing India-wide map context."
3. When `nearBhopal = true`: hidden or returns null
4. Non-intrusive positioning: bottom-left, small font, semi-transparent background

**Acceptance Criteria:**
- [ ] `CoverageIndicator.tsx` exists
- [ ] When `nearBhopal = false`, renders the coverage unavailability message
- [ ] When `nearBhopal = true`, renders nothing
- [ ] TypeScript compiles without errors

---

### Task B.6 — MapLibreMap: extend with all data layers

**Goal:** Wire all data sources and layers into the existing MapLibreMap component.

**Steps:**
1. Extend `MapLibreMapProps` with `onParcelClick` and `initialLayers` props
2. Change default `center` to `INDIA_CENTER` (`[78.9629, 20.5937]`) and default `zoom` to `5`
3. Remove the hardcoded `minZoom: 14` restriction — India needs zoom 3–22 range. Set `minZoom: 3`.
4. In `map.on("load")`, add all sources and layers as per design.md §4.4:
   - UAV raster source (points to `getBhopalTileUrl()`)
   - OSM GeoJSON sources (load lazily at zoom ≥ 13)
   - Parcels GeoJSON source (load lazily at zoom ≥ 15)
   - AI features GeoJSON source (load lazily at zoom ≥ 15)
5. Add `map.on("moveend")` handler:
   - Compute distance from map center to Bhopal city center
   - If zoom ≥ 13 and within ~50 km of Bhopal: load OSM sources (if not already loaded)
   - If zoom ≥ 15 and within ~20 km of Bhopal: load parcel/AI sources (if not already loaded)
   - Update `nearBhopal` state for CoverageIndicator
6. Add `map.on("click", "parcels-bhopal-fill")` handler to invoke `onParcelClick`
7. Apply `initialLayers` visibility to all layers after adding them
8. Preserve the existing UAV bounds indicator (do not remove)

**Layer paint specs:**

```
UAV raster:      { "raster-opacity": 0.9 }, minzoom: 17, maxzoom: 22
OSM landuse fill: { "fill-color": "#6B7C45", "fill-opacity": 0.12 }, minzoom: 14
OSM buildings:   { "fill-color": "#EDE8DE", "fill-opacity": 0.6,
                   "line-color": "#8A8A8A", "line-width": 0.5 }, minzoom: 16
OSM roads:       { "line-color": "#C4922A", "line-width": ["interpolate",["linear"],["zoom"],13,0.5,17,2] }, minzoom: 13
OSM waterways:   { "line-color": "#3A6B1E", "line-width": 1.5 }, minzoom: 13
Parcels fill:    { "fill-color": "#D4A017", "fill-opacity": 0.25 }, minzoom: 15
Parcels line:    { "line-color": "#2D5016", "line-width": 1.5 }, minzoom: 15
AI features fill: { "fill-color": "#C4922A", "fill-opacity": 0.35 }, minzoom: 15
AI features line: { "line-color": "#A67820", "line-width": 1 }, minzoom: 15
```

**Acceptance Criteria:**
- [ ] Default map center is India (zoom 5), NOT Bhopal
- [ ] `minZoom` is 3 (allows full India view), not 14
- [ ] UAV raster tiles load when zoomed to z17+ near Bhopal
- [ ] Parcel layer visible at z15+ near Bhopal
- [ ] AI features layer visible at z15+ near Bhopal
- [ ] OSM roads visible at z13+ near Bhopal
- [ ] Layer visibility respects `initialLayers` prop
- [ ] Parcel click calls `onParcelClick` with property_id
- [ ] `npm run build` exits 0

---

### Task B.7 — Update `/app/map` page

**Goal:** Update the map page to be India-scale with location search, layer control, property panel, and coverage indicator.

**Steps:**
1. Modify `drishtigis/app/app/map/page.tsx`:
   - Top bar: replace static "Prototype Dataset — Bhopal" label with a location search component
   - Remove hardcoded tile count / cm/px / EPSG stats from the header (these are dataset-specific, not always visible)
   - Wire `DynamicMap` with `onParcelClick` → opens PropertyPanel
   - Add `LayerControl` (client component) overlaid on the map
   - Add `CoverageIndicator` with `nearBhopal` state computed from map events
2. Layer control state managed in a `"use client"` wrapper component
3. The map page Server Component renders the structure; interactive state lives in client components

**Acceptance Criteria:**
- [ ] Page renders without errors
- [ ] Map loads at India center (zoom 5) on first load
- [ ] Layer control visible on map
- [ ] Coverage indicator appears when map is not near Bhopal
- [ ] Property panel slides in on parcel click
- [ ] Page title remains "Map — DrishtiGIS"
- [ ] `npm run build` exits 0 with 0 TypeScript errors

---

### Task B.8 — Frontend build verification

**Goal:** Full frontend build + lint with zero errors.

**Steps:**
1. `cd drishtigis && npm run build` — must exit 0
2. `cd drishtigis && npm run lint` — must exit 0
3. Verify all 15 routes still present
4. Check browser console when loading in dev mode — no critical errors

**Acceptance Criteria:**
- [ ] `npm run build` exits 0
- [ ] `npm run lint` exits 0
- [ ] Zero TypeScript errors
- [ ] All 15 routes return valid pages (no 404s)

---

## Phase C — Integration Verification

### Task C.1 — Full integration smoke test

**Goal:** Verify frontend + backend work together with real data flowing end-to-end.

**Steps:**
1. Start backend: `uvicorn app.main:app --reload` (port 8000)
2. Start frontend: `npm run dev` (port 3000)
3. Create `drishtigis/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
4. Navigate to `http://localhost:3000/app/map`
5. Verify map loads at India overview
6. Zoom to Bhopal area (search "Bhopal" or navigate manually to 23.26N, 77.41E)
7. Verify UAV tiles load at z17+
8. Verify OSM roads appear at z13+
9. Verify parcels appear at z15+
10. Click a parcel → verify property panel loads with demo data
11. Check that coverage indicator disappears when near Bhopal

**Acceptance Criteria:**
- [ ] Backend and frontend start without errors
- [ ] Map loads at India zoom (zoom 5, centered on India)
- [ ] Navigation to Bhopal loads UAV tiles
- [ ] Parcel click triggers property panel with data from API
- [ ] Property panel shows "Demo record" and prototype disclaimer
- [ ] No CORS errors in browser console
- [ ] No `undefined` or `null` rendering errors for data fields

---

### Task C.2 — Dataset/ integrity final verification

**Goal:** Confirm all raw data assets are byte-for-byte unchanged from their Phase baselines.

**Steps:**
1. Run the integrity check script:
   ```python
   import os
   checks = {
       'Dataset/Drone-Images/BHOPAL/00_00.tiff': 7358913,
       'Dataset/Drone-Images/BHOPAL/01_06.tiff': 7259880,
       'Dataset/Drone-Images/india-260905.osm.pbf': 1706252573,
   }
   for path, expected in checks.items():
       actual = os.path.getsize(path)
       print(f'[{"OK" if actual==expected else "FAIL"}] {path.split("/")[-1]}: {actual:,}')
   ```
2. Verify `data/processed/tiles/bhopal/` still has 379 tiles
3. Verify `data/osm/bhopal-extract/` still has the 4 GeoJSON files

**Acceptance Criteria:**
- [ ] All 30 TIFF files: sizes unchanged
- [ ] `india-260905.osm.pbf`: 1,706,252,573 bytes
- [ ] XYZ tile pyramid: 379 tiles total
- [ ] 4 OSM GeoJSON files present on disk

---

### Task C.3 — Final git diff inspection and progress.md update

**Goal:** Verify the final committed changeset contains exactly the intended files and nothing else.

**Steps:**
1. `git diff HEAD~1 --name-only` — review all changed files
2. Confirm no changes to:
   - `Dataset/` (any file)
   - `data/processed/` (should be gitignored)
   - `data/osm/` (should be gitignored)
   - `.kiro/specs/foundation-and-data-pipeline/` (previous spec — read-only)
3. Update `progress.md` with core-india-webgis completion status

**Acceptance Criteria:**
- [ ] `git status` shows clean working tree (or only gitignored files)
- [ ] No unintended files in the commit
- [ ] `progress.md` updated with feature completion

---

## Task Dependency Summary

```
A.1 → A.2 → A.3 → A.4 → A.5 → A.6 → A.7 → A.8 → A.9
                                                        ↓
B.1 → B.2 → B.3 → B.4 → B.5 → B.6 → B.7 → B.8
                                                ↓
                                              C.1 → C.2 → C.3
```

Tasks A.4 and A.5 can proceed in parallel after A.3.
Tasks B.1 and B.2 can proceed in parallel with Phase A after B.1 is done.
Tasks B.3, B.4, B.5 can proceed in parallel after B.2 is done.
Phase C requires both Phase A and Phase B complete.

---

## Estimated Task Sizes

| Task | Complexity | Notes |
|---|---|---|
| A.1 | Trivial | Package init + config comment |
| A.2 | Small | Static data file, ~60 lines |
| A.3 | Small | Coverage registry, ~80 lines |
| A.4 | Medium | Tile endpoint with security, ~60 lines |
| A.5 | Small | OSM endpoints, ~40 lines |
| A.6 | Small | Coverage + search endpoints, ~60 lines |
| A.7 | Trivial | One-line change to parcels.py |
| A.8 | Medium | ~100 lines of tests |
| A.9 | Trivial | Start + verify |
| B.1 | Small | Two constants files, ~60 lines |
| B.2 | Small | 5 client files, ~80 lines total |
| B.3 | Small | Layer control UI, ~60 lines |
| B.4 | Medium | Property panel with fetch, ~120 lines |
| B.5 | Trivial | Coverage indicator, ~30 lines |
| B.6 | Large | MapLibre layer wiring, ~200 lines change |
| B.7 | Medium | Map page update, ~80 lines change |
| B.8 | Trivial | Build + lint verify |
| C.1–C.3 | Trivial | Smoke tests + verification |
