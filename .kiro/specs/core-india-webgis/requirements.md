# Spec: Core India WebGIS Integration
## Requirements

**Spec ID:** core-india-webgis  
**Version:** 0.1  
**Status:** APPROVED — ready for implementation  
**Alignment:** CLAUDE.md · DOC/PRD.md · DOC/requirements.md  
**Depends on:** foundation-and-data-pipeline v0.2 (all phases complete)

---

## 1. Purpose and Scope

This spec connects the verified GIS data assets produced in Phases 1–3 to the running DrishtiGIS application. It establishes an India-scale geographic architecture where Bhopal is the first fully-populated prototype intelligence area, without pretending that detailed intelligence exists for all of India.

**In scope:**
- Geographic coverage data model (India-wide vs prototype-detail)
- City/location search backend contract
- Bhopal dataset/coverage registry
- Raster tile API serving verified XYZ tiles through FastAPI
- OSM layer API exposing extracted Bhopal GeoJSON (bbox-bounded)
- Parcel, AI feature, and discrepancy API integration with MapLibre
- MapLibre layer wiring: UAV tiles + OSM layers + parcels + AI features
- Zoom-dependent layer visibility
- Property selection data flow (click → detail panel contract)
- Honest unavailability states for non-Bhopal areas
- Path traversal protection and raw dataset access prevention
- Backend tests covering all new endpoints
- Frontend source configuration for all new layers

**Not in scope:**
- Gemini assistant
- Historical imagery comparison
- AWS GPU processing
- Production cadastral ingestion
- Reports generation
- UI redesign or visual polish
- India-wide property datasets
- Authentication

---

## 2. Source-of-Truth Alignment

| Document | Role |
|---|---|
| `CLAUDE.md` | Engineering behavior, data integrity rules, layer labeling |
| `DOC/PRD.md` | Map-first principle, layer architecture, city search flow |
| `DOC/requirements.md` | API contracts, data model, coverage requirements |

All three documents take precedence over this spec if any conflict arises.

---

## 3. Data Reality Statement

This spec integrates **real verified data** that already exists on disk. The following is the ground truth that must be reflected throughout:

| Asset | Status | Classification |
|---|---|---|
| Bhopal XYZ tiles — 379 tiles, z18–21 | Real, verified, on disk at `data/processed/tiles/bhopal/` | `PROCESSED_RASTER` |
| Bhopal OSM buildings — 26,577 features | Real OSM data, on disk at `data/osm/bhopal-extract/bhopal-buildings.geojson` (27 MB) | `OSM_OPENSTREETMAP` |
| Bhopal OSM roads — 2,933 features | Real OSM data, on disk at `data/osm/bhopal-extract/bhopal-roads.geojson` (3 MB) | `OSM_OPENSTREETMAP` |
| Bhopal OSM waterways — 31 features | Real OSM data, on disk | `OSM_OPENSTREETMAP` |
| Bhopal OSM landuse — 98 features | Real OSM data, on disk | `OSM_OPENSTREETMAP` |
| Demo parcels — 3 records | Demo prototype data | `DEMO_DATA_PROTOTYPE_ONLY` |
| Demo AI features — 2 records | Demo placeholder AI output | `AI_DERIVED_DEMO` |
| Demo discrepancies — 2 records | Demo prototype data | `DEMO_DATA_PROTOTYPE_ONLY` |
| India OSM PBF — 1.71 GB | Source only — must NEVER reach browser | Offline only |
| Raw UAV TIFFs — 30 files | Read-only source — must NEVER be served directly | `RAW_RASTER_UAV` |

**The 27 MB buildings GeoJSON must NOT be sent wholesale to the browser.** It must be bbox-bounded before delivery (the extraction bbox 77.38–77.44°E, 23.24–23.27°N is already appropriate and safe to deliver as-is, but the response must confirm this and include the bounding metadata).

---

## 4. Geographic Coverage Data Model

### REQ-COV-01 — Coverage Availability Interface
The system must expose a coverage availability model that allows any geographic coordinate or city to be queried for what types of intelligence are available.

### REQ-COV-02 — Coverage Levels
The model must distinguish exactly these coverage levels (not more, not fewer without spec revision):

```typescript
interface CoverageAvailability {
  city: string;
  state: string;
  country: "India";
  center: { lat: number; lon: number };
  map_available: boolean;           // Always true for India (base map)
  osm_available: boolean;           // OSM context available
  imagery_available: boolean;       // UAV/satellite imagery available
  parcel_data_available: boolean;   // Cadastral/parcel data available
  ai_analysis_available: boolean;   // AI feature analysis available
  historical_data_available: boolean; // Multi-temporal comparison available
  coverage_source: string;          // "prototype" | "production" | "none"
  disclaimer?: string;              // Required when any prototype data is reported
}
```

### REQ-COV-03 — Bhopal Coverage Record
Bhopal must report:
```json
{
  "city": "Bhopal",
  "state": "Madhya Pradesh",
  "country": "India",
  "map_available": true,
  "osm_available": true,
  "imagery_available": true,
  "parcel_data_available": true,
  "ai_analysis_available": true,
  "historical_data_available": false,
  "coverage_source": "prototype",
  "disclaimer": "Parcel and AI data are prototype demonstration records only. They are not official government cadastral data."
}
```

`historical_data_available: false` — no second time epoch exists. This must never be fabricated.

### REQ-COV-04 — Other Indian Cities
All other cities (Delhi, Lucknow, Mumbai, Chennai, Kanpur, Jammu, Srinagar, Hyderabad, Bengaluru, Pune, etc.) must report:
- `map_available: true` (base map always available across India)
- `osm_available: true` (OSM context available but not pre-extracted)
- `imagery_available: false`
- `parcel_data_available: false`
- `ai_analysis_available: false`
- `historical_data_available: false`
- `coverage_source: "none"`
- No disclaimer needed (no prototype data claimed)

### REQ-COV-05 — No Fabrication
The coverage model must NEVER claim imagery, parcel, or AI availability for any city where it does not exist. Fabricating coverage records violates the data integrity rules in CLAUDE.md.

---

## 5. City / Location Search

### REQ-SEARCH-01 — India-Wide Search Endpoint
```
GET /api/v1/locations/search?q={query}&country=India
```
Must support searching for any Indian city or location without hard-coding a list. Must return coverage availability for each result.

### REQ-SEARCH-02 — Search Response Shape
```json
{
  "query": "Bhopal",
  "results": [
    {
      "name": "Bhopal",
      "state": "Madhya Pradesh",
      "country": "India",
      "center": { "lat": 23.2599, "lon": 77.4126 },
      "zoom_level": 12,
      "coverage": { /* CoverageAvailability */ }
    }
  ],
  "total": 1
}
```

### REQ-SEARCH-03 — Data Source for Search
City/location coordinates must come from a static data file (`lib/gis/india-cities.ts` or equivalent) containing at minimum: Bhopal, Delhi, Mumbai, Lucknow, Chennai, Kanpur, Jammu, Srinagar, Hyderabad, Bengaluru, Pune, Kolkata, Ahmedabad, Jaipur, Nagpur. This list must be extensible without code changes to the search endpoint.

The static city list must NOT be confused with the coverage registry. City list = geography; coverage registry = data availability.

### REQ-SEARCH-04 — No Fabricated Intelligence
Search results for non-Bhopal cities must return `coverage_source: "none"` and must not imply AI, parcel, or imagery data is available.

---

## 6. Bhopal Dataset Registry

### REQ-REGISTRY-01 — Registry Endpoint
```
GET /api/v1/coverage/{city_slug}
```
Returns the full `CoverageAvailability` record for a city. `city_slug` is lowercase, hyphenated (e.g., `bhopal`, `new-delhi`).

### REQ-REGISTRY-02 — Bhopal Registry Data
The Bhopal registry must additionally expose dataset metadata:
```json
{
  "datasets": [
    {
      "id": "dataset-bpl-uav-001",
      "type": "orthomosaic",
      "name": "Bhopal UAV Prototype",
      "tile_url_template": "/api/v1/tiles/bhopal/{z}/{x}/{y}.png",
      "zoom_min": 18,
      "zoom_max": 21,
      "bounds": [77.41299311, 23.25573135, 77.42267457, 23.25667101],
      "resolution_m": 0.021713,
      "tile_count": 379,
      "source": "PROCESSED_RASTER",
      "_disclaimer": "Prototype UAV imagery. Not a production surveying product."
    },
    {
      "id": "dataset-bpl-osm-001",
      "type": "osm_extract",
      "name": "Bhopal OSM Extract",
      "extraction_bbox": [77.38, 23.24, 77.44, 23.27],
      "layers": ["buildings", "roads", "waterways", "landuse"],
      "source": "OSM_OPENSTREETMAP",
      "_attribution": "© OpenStreetMap contributors, ODbL"
    }
  ]
}
```

### REQ-REGISTRY-03 — Prototype Classification
All prototype records in the registry must carry explicit `source` classifications using the existing `DataSource` enum values. No record may omit the `source` field.

---

## 7. Raster Tile API

### REQ-TILES-01 — Tile Endpoint
```
GET /api/v1/tiles/bhopal/{z}/{x}/{y}.png
```

### REQ-TILES-02 — Tile Source
Serves only from `data/processed/tiles/bhopal/{z}/{x}/{y}.png`. Must use an absolute, computed path from the backend application root — not a user-controlled path.

### REQ-TILES-03 — Path Traversal Protection
- `z`, `x`, `y` must each be validated as non-negative integers in a safe range
- No path components may contain `..`, `/`, `\`, or `%2e`
- The resolved file path must be confirmed to be inside `data/processed/tiles/bhopal/` before reading
- Any path that resolves outside this directory must return HTTP 403

### REQ-TILES-04 — 404 on Missing Tile
If the tile file does not exist at the computed path, return HTTP 404. Do not fall back to serving other files.

### REQ-TILES-05 — Content Type
Response `Content-Type` must be `image/png`.

### REQ-TILES-06 — Raw Data Protection
The endpoint must NEVER serve:
- Files from `Dataset/` (raw TIFFs)
- `data/processed/bhopal_cog.tif`
- `data/processed/bhopal_mosaic.vrt`
- Any file outside `data/processed/tiles/bhopal/`
- Any `.env` or secrets file

### REQ-TILES-07 — Zoom Range
Only serve tiles for zoom levels 18–21. Any request outside this range returns HTTP 404.

### REQ-TILES-08 — Bhopal-Only
The tile endpoint path includes `bhopal` explicitly. Future cities would be added as additional endpoint paths, not via a parameter that could be manipulated.

### REQ-TILES-09 — Caching Headers
Include `Cache-Control: public, max-age=3600` on successful tile responses. Tiles are static and safe to cache.

---

## 8. OSM Layer API

### REQ-OSM-01 — Layer Endpoint Per Type
```
GET /api/v1/osm/bhopal/buildings
GET /api/v1/osm/bhopal/roads
GET /api/v1/osm/bhopal/waterways
GET /api/v1/osm/bhopal/landuse
```

### REQ-OSM-02 — Data Source
Serves from `data/osm/bhopal-extract/bhopal-{layer}.geojson`. Absolute path, computed at startup.

### REQ-OSM-03 — Attribution Preserved
Every response must include the OSM attribution in the response body and in an `X-OSM-Attribution` response header:
```
X-OSM-Attribution: © OpenStreetMap contributors, ODbL
```

### REQ-OSM-04 — Source Classification
Every response body must include `"_source": "OSM_OPENSTREETMAP"` at the top level.

### REQ-OSM-05 — Not Cadastral
Every response must include:
```json
"_disclaimer": "OSM data is supplementary geographic context only. It is NOT authoritative cadastral data."
```

### REQ-OSM-06 — Size-Aware Delivery
The buildings layer (27 MB uncompressed) must be served with `Content-Encoding: gzip` when the client supports it, or a streaming response. The response must not load the entire 27 MB file into RAM eagerly for every request. Use `FileResponse` (FastAPI native, uses `sendfile` internally) for efficient delivery.

### REQ-OSM-07 — India PBF Protection
The `data/osm/bhopal-extract/` path must only expose the 4 thematic GeoJSON files. Requests for `_bbox_nodes.json`, `extraction_report.json`, or any other file must return HTTP 404.

### REQ-OSM-08 — No Dynamic PBF Conversion
The OSM endpoints must NEVER trigger any runtime conversion of the India PBF. All GeoJSON was pre-extracted in Phase 3.

---

## 9. Parcel API — Integration Contract

### REQ-PARCEL-01 — Existing Endpoints Preserved
The existing parcel endpoints must continue to function exactly as specified and tested in Phase 6:
- `GET /api/v1/parcels?city=Bhopal` → returns 3 demo parcels
- `GET /api/v1/parcels/{property_id}` → returns full parcel detail

### REQ-PARCEL-02 — Non-Bhopal City Behavior
`GET /api/v1/parcels?city=Lucknow` (or any non-Bhopal city) must return an empty FeatureCollection with an explicit coverage unavailability message — not a 404, not an error:
```json
{
  "type": "FeatureCollection",
  "total": 0,
  "features": [],
  "_source": "DEMO_DATA_PROTOTYPE_ONLY",
  "_coverage_note": "No parcel data is available for Lucknow. DrishtiGIS currently has prototype data for Bhopal only.",
  "_disclaimer": "..."
}
```

### REQ-PARCEL-03 — Prototype Classification Unchanged
All parcel responses must continue to carry `X-Data-Status: demo-placeholder` and `_source: "DEMO_DATA_PROTOTYPE_ONLY"`.

### REQ-PARCEL-04 — Discrepancy Language
Discrepancy records in parcel detail responses must continue to use only the approved language — never "illegal", "fraud", "encroachment", "violation". `legal_status: null` must remain null.

---

## 10. AI Feature API — Integration Contract

### REQ-AI-01 — Existing Endpoint Preserved
`GET /api/v1/features?parcel_id={id}` must continue to function as in Phase 6.

### REQ-AI-02 — OSM vs AI Distinction
API responses for AI features must carry `_source: "AI_DERIVED_DEMO"`. This must be distinct and non-overlapping with OSM building responses which carry `_source: "OSM_OPENSTREETMAP"`.

### REQ-AI-03 — Not Official Cadastral Data
AI feature responses must include the existing disclaimer: "AI-derived observation — prototype demonstration model only. Not a legal determination. Requires field verification."

---

## 11. MapLibre Layer Integration

### REQ-MAP-01 — India Base Map
The MapLibre map must start with an India-appropriate zoom level when no specific dataset area is loaded. Suggested: center on India (~20°N, 79°E), zoom 5. This is the default India-scale context.

### REQ-MAP-02 — Bhopal UAV Raster Tiles
When the Bhopal area is active, add a `raster` source pointing to:
```
/api/v1/tiles/bhopal/{z}/{x}/{y}.png
```
Add a corresponding `raster` layer visible only at zoom 17–21. Tile size: 256. Tile scheme: `xyz`.

### REQ-MAP-03 — OSM Layers
Add four GeoJSON sources for the Bhopal OSM extract:
- `osm-buildings` → `/api/v1/osm/bhopal/buildings`
- `osm-roads` → `/api/v1/osm/bhopal/roads`
- `osm-waterways` → `/api/v1/osm/bhopal/waterways`
- `osm-landuse` → `/api/v1/osm/bhopal/landuse`

Each source must be loaded only when the map is zoomed into the Bhopal area (zoom ≥ 13). Do not fetch 27 MB of buildings data when the user is viewing India at zoom 5.

### REQ-MAP-04 — Parcel Layer
Add a GeoJSON source `parcels-bhopal` pointing to `/api/v1/parcels?city=Bhopal`. Render as a `fill` + `line` layer, visible zoom ≥ 15. Use the DrishtiGIS forest/ochre palette for distinction from OSM layers.

### REQ-MAP-05 — AI Feature Layer
Add a GeoJSON source `ai-features-bhopal` pointing to `/api/v1/features`. Render as a `fill` layer with distinct styling (e.g., ochre/amber, lower opacity), visible zoom ≥ 15. Must be visually distinct from parcel layer.

### REQ-MAP-06 — Layer Visibility Control
A layer control panel must allow toggling visibility of:
- UAV Imagery (raster)
- Parcels
- AI Features
- OSM Buildings
- OSM Roads
- OSM Waterways
- OSM Landuse

Default visibility: UAV Imagery ON, Parcels ON, AI Features ON, OSM Roads ON, OSM Buildings OFF (too dense at initial zoom), OSM Waterways ON, OSM Landuse OFF.

### REQ-MAP-07 — Zoom-Dependent Rendering
- OSM buildings: visible only at zoom ≥ 16 (line rendering), zoom ≥ 17 (fill rendering)
- OSM roads: visible at zoom ≥ 13
- OSM waterways: visible at zoom ≥ 13
- OSM landuse: visible at zoom ≥ 14, fill only (no overwhelming polygon fills at low zoom)
- Parcels: visible at zoom ≥ 15
- AI features: visible at zoom ≥ 15
- UAV raster: visible at zoom ≥ 17

OSM layers must not visually dominate the parcel/AI layers when both are visible.

### REQ-MAP-08 — Coverage Unavailability UI
When the user navigates to an area outside Bhopal's coverage (based on map center/bounds), the UI must show a non-intrusive indicator: "Detailed AI/property analysis is not yet available for this area. Showing map context only." This must appear when the user is more than ~10 km from the Bhopal UAV coverage center.

---

## 12. Property Selection Data Flow

### REQ-PROP-01 — Parcel Click Handler
Clicking a parcel polygon on the map must trigger a data fetch to `GET /api/v1/parcels/{property_id}` and display the result.

### REQ-PROP-02 — Property Panel Contract
The property detail panel must display, using only data returned from the API:
- Property ID (`DRS-BPL-XXXXX`)
- Plot number and survey number
- Area (m²)
- Land type
- Status
- Source label (e.g., "Prototype Dataset — Bhopal")
- Record status (e.g., "Demo record")
- AI analysis section (confidence, detected area, discrepancy if present)
- Discrepancy detail (using safe language only)
- Prototype disclaimer

### REQ-PROP-03 — Disclaimer Always Visible
The prototype/demo disclaimer must be permanently visible in the property panel whenever prototype data is shown. It must never be hidden behind a toggle or collapsed by default.

### REQ-PROP-04 — No Visual Design Work
Focus on correct data flow and component contracts. The property panel does not need to match the final PRD visual design at this stage.

---

## 13. Security Requirements

### REQ-SEC-01 — Raw Dataset Protection
No endpoint may serve files from `Dataset/`. This directory is read-only source data, never a web asset.

### REQ-SEC-02 — Path Traversal Prohibition
All file-serving endpoints must validate that the final resolved path is inside the intended directory before reading. Use `Path.resolve()` comparison, not string prefix matching.

### REQ-SEC-03 — No Secret Exposure
No endpoint may return environment variables, config values, filesystem paths outside the application's public data directories, or database connection strings.

### REQ-SEC-04 — No PBF Exposure
The `india-260905.osm.pbf` file must never be served via any API endpoint. The OSM endpoints serve only the pre-extracted thematic GeoJSON files.

---

## 14. Testing Requirements

### REQ-TEST-01 — Test Suite Location
Tests at `backend/tests/test_webgis.py`. Use pytest + httpx `TestClient` (sync) for all tests. No new test frameworks.

### REQ-TEST-02 — Required Test Coverage

**Coverage/search:**
- India location search returns results for any Indian city
- Bhopal returns correct coverage flags (imagery=true, parcel=true, ai=true)
- Non-Bhopal city returns correct coverage flags (imagery=false, parcel=false, ai=false)
- Coverage unavailability does not fabricate data

**Tile API:**
- Valid tile request returns 200 with `image/png` content type
- Invalid z/x/y (non-integer, negative, string) returns 4xx
- Request outside zoom 18–21 returns 404
- Path traversal attempt returns 403 or 404
- Dataset/ path cannot be accessed through tile endpoint
- Non-existent tile returns 404

**OSM API:**
- All 4 layers return 200 with `_source: "OSM_OPENSTREETMAP"`
- All 4 layers include `X-OSM-Attribution` header
- All 4 layers include `_disclaimer` in response body
- Unknown layer (e.g., `bhopal/schools`) returns 404
- `_bbox_nodes.json` returns 404 (not exposed)
- `extraction_report.json` returns 404 (not exposed)

**Parcel API:**
- `?city=Bhopal` returns 3 features
- `?city=Lucknow` returns 0 features with coverage note
- `DRS-BPL-00101` returns parcel + property + discrepancy + AI features
- Unknown property_id returns 404
- Response includes `X-Data-Status: demo-placeholder`

**AI Feature API:**
- `?parcel_id=parcel-bpl-001` returns 1 feature
- Response `_source = "AI_DERIVED_DEMO"` (distinct from OSM)
- Discrepancy data has `legal_status: null`

**Source classification:**
- OSM and AI source fields are never confused
- Demo parcels never have `_source: "OFFICIAL_REFERENCE"`

---

## 15. Data Integrity Requirements (Non-Negotiable)

### REQ-INTEGRITY-01 — Dataset/ Read-Only
No script, test, or application code in this spec may write to or modify any file under `Dataset/`. All 30 UAV TIFFs and the India PBF must remain byte-for-byte identical to their Phase 2/3 baselines throughout this spec's implementation.

### REQ-INTEGRITY-02 — Phase 2 Outputs Preserved
The generated raster pipeline outputs (`bhopal_cog.tif`, `bhopal_mosaic.vrt`, tile pyramid) must not be modified unless a specific integration bug requires it, and any modification must be explicitly documented.

### REQ-INTEGRITY-03 — Phase 3 Outputs Preserved
The OSM GeoJSON files must not be regenerated or overwritten unless explicitly required, and any change must be documented.

### REQ-INTEGRITY-04 — No New Fabricated Data
This spec does not introduce any new fabricated city records, property records, AI detections, or historical imagery. The existing 3 demo parcels and 2 AI features remain the full extent of prototype property intelligence for Bhopal.

---

## 16. Out of Scope (Explicitly)

These items are excluded from this spec:

- Gemini AI assistant
- Historical imagery comparison
- AWS GPU or cloud inference
- Production cadastral ingestion from government sources
- Report generation
- UI visual redesign or PRD visual spec implementation
- India-wide property database
- Authentication / user management
- Supabase Auth integration
- Multi-city UAV dataset pipeline
