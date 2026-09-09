# Spec: Core India WebGIS Integration
## Technical Design

**Spec ID:** core-india-webgis  
**Version:** 0.1  
**Alignment:** CLAUDE.md · DOC/PRD.md · DOC/requirements.md

---

## 1. Architecture Overview

This spec adds a data-serving layer between the verified disk assets and the running MapLibre frontend. No new infrastructure is introduced. All serving happens through the existing FastAPI backend (`backend/`) and the existing Next.js frontend (`drishtigis/`).

```
BROWSER
  MapLibreMap (client component)
    ├── raster source → GET /api/v1/tiles/bhopal/{z}/{x}/{y}.png
    ├── geojson source → GET /api/v1/osm/bhopal/roads
    ├── geojson source → GET /api/v1/osm/bhopal/buildings  (zoom-gated)
    ├── geojson source → GET /api/v1/osm/bhopal/waterways
    ├── geojson source → GET /api/v1/osm/bhopal/landuse
    ├── geojson source → GET /api/v1/parcels?city=Bhopal
    └── geojson source → GET /api/v1/features
  LayerControl (new client component)
  PropertyPanel (new client component, shown on parcel click)
  LocationSearch (new client component)
  CoverageIndicator (new client component)

FASTAPI BACKEND (backend/)
  New routers:
  ├── /api/v1/tiles/bhopal/{z}/{x}/{y}.png  → tiles.py
  ├── /api/v1/osm/bhopal/{layer}            → osm_layers.py
  ├── /api/v1/coverage/{city_slug}          → coverage.py
  └── /api/v1/locations/search              → locations.py
  Extended routers:
  ├── /api/v1/parcels (extended for coverage note on non-Bhopal)

DATA LAYER (disk — gitignored, not served directly from Dataset/)
  data/processed/tiles/bhopal/{z}/{x}/{y}.png  (379 tiles)
  data/osm/bhopal-extract/bhopal-{layer}.geojson  (4 files)
  drishtigis/lib/demo-data/*.geojson|json  (demo data, source-controlled)
```

---

## 2. New File Structure

### Backend additions
```
backend/app/api/v1/
  tiles.py          ← NEW: raster tile endpoint
  osm_layers.py     ← NEW: OSM GeoJSON layer endpoints
  coverage.py       ← NEW: coverage availability endpoints
  locations.py      ← NEW: India city search endpoint

backend/app/gis/
  __init__.py       ← NEW: GIS utilities package
  coverage_registry.py  ← NEW: coverage data model + Bhopal registry
  india_cities.py   ← NEW: static India city list

backend/tests/
  test_webgis.py    ← NEW: all tests for this spec

backend/app/core/
  config.py         ← MODIFIED: add DATA_DIR and TILES_DIR settings
```

### Frontend additions
```
drishtigis/lib/gis/
  bounds.ts         ← EXISTING: no change
  india.ts          ← NEW: India-scale geographic constants
  coverage.ts       ← NEW: TypeScript types mirroring backend coverage model

drishtigis/components/map/
  MapLibreMap.tsx   ← MODIFIED: add UAV tiles + OSM + parcel + AI sources/layers
  DynamicMap.tsx    ← UNCHANGED
  LayerControl.tsx  ← NEW: layer visibility toggle panel
  PropertyPanel.tsx ← NEW: property detail display component
  CoverageIndicator.tsx ← NEW: unavailability notice component

drishtigis/lib/api/
  __init__.ts       ← NEW: API client barrel
  tiles.ts          ← NEW: tile URL builder
  osm.ts            ← NEW: OSM layer fetcher
  parcels.ts        ← NEW: parcel API client
  features.ts       ← NEW: AI features API client
  coverage.ts       ← NEW: coverage API client
  locations.ts      ← NEW: location search API client

drishtigis/app/app/map/
  page.tsx          ← MODIFIED: India-scale initial view, layer control, property panel
```

---

## 3. Backend Design

### 3.1 Settings additions (`backend/app/core/config.py`)

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Data paths — computed relative to backend/ working directory
    # These are read at startup and used by tile/OSM endpoints
    DATA_DIR: str = "../data"          # relative to backend/ working dir
    TILES_DIR: str = "../data/processed/tiles"
    OSM_DIR: str = "../data/osm/bhopal-extract"
```

Path resolution in endpoints uses `Path(__file__).resolve().parents[3]` (repo root) to build absolute paths, not relative working-directory strings.

### 3.2 Tile Endpoint (`backend/app/api/v1/tiles.py`)

```python
from fastapi import APIRouter, HTTPException, Path as FPath
from fastapi.responses import FileResponse
from pathlib import Path
import re

router = APIRouter()

REPO_ROOT  = Path(__file__).resolve().parents[4]
TILES_BASE = REPO_ROOT / "data" / "processed" / "tiles" / "bhopal"
ZOOM_MIN, ZOOM_MAX = 18, 21

@router.get("/bhopal/{z}/{x}/{y}.png", summary="Bhopal UAV raster tile")
async def get_bhopal_tile(
    z: int = FPath(ge=0, le=30),
    x: int = FPath(ge=0),
    y: int = FPath(ge=0),
) -> FileResponse:
    # Zoom range check
    if not (ZOOM_MIN <= z <= ZOOM_MAX):
        raise HTTPException(404, "Tile not available at this zoom level")

    # Build safe path
    tile_path = TILES_BASE / str(z) / str(x) / f"{y}.png"

    # Path traversal guard — resolve and confirm prefix
    try:
        resolved = tile_path.resolve()
    except Exception:
        raise HTTPException(403, "Invalid tile path")
    
    if not str(resolved).startswith(str(TILES_BASE.resolve())):
        raise HTTPException(403, "Path traversal detected")

    if not resolved.exists():
        raise HTTPException(404, "Tile not found")

    return FileResponse(
        str(resolved),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )
```

FastAPI's `Path(ge=0)` validators with `int` type annotations reject non-integer, negative, and string inputs at the framework level before the handler body runs, eliminating most injection vectors.

### 3.3 OSM Layer Endpoint (`backend/app/api/v1/osm_layers.py`)

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]
OSM_BASE  = REPO_ROOT / "data" / "osm" / "bhopal-extract"

# Allowlist — only these filenames may be served
ALLOWED_LAYERS = frozenset(["buildings", "roads", "waterways", "landuse"])

OSM_HEADERS = {
    "X-OSM-Attribution": "\u00a9 OpenStreetMap contributors, ODbL",
    "X-Data-Source": "OSM_OPENSTREETMAP",
    "Cache-Control": "public, max-age=1800",  # 30 min — OSM extracts are stable
}

@router.get("/bhopal/{layer}", summary="Bhopal OSM thematic layer")
async def get_bhopal_osm_layer(layer: str) -> FileResponse:
    # Strict allowlist — no dynamic path construction beyond this
    if layer not in ALLOWED_LAYERS:
        raise HTTPException(404, f"Layer '{layer}' not available")

    file_path = OSM_BASE / f"bhopal-{layer}.geojson"
    
    if not file_path.exists():
        raise HTTPException(404, "Layer data not found on disk. Run Phase 3 extraction.")

    return FileResponse(
        str(file_path),
        media_type="application/geo+json",
        headers=OSM_HEADERS,
    )
```

The allowlist (`ALLOWED_LAYERS`) is the primary security control — no path construction from user input. The file name is `f"bhopal-{layer}.geojson"` where `layer` is drawn only from the allowlist, making injection impossible.

**Note on buildings file size (27 MB):** `FileResponse` uses the OS `sendfile` syscall where available — it does not load the file into application memory. This is safe for large GeoJSON. FastAPI/Starlette's `FileResponse` handles this correctly.

### 3.4 Coverage Registry (`backend/app/gis/coverage_registry.py`)

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CoverageSource(str, Enum):
    PROTOTYPE = "prototype"
    PRODUCTION = "production"
    NONE = "none"

@dataclass(frozen=True)
class CoverageAvailability:
    city: str
    state: str
    country: str
    center_lat: float
    center_lon: float
    map_available: bool
    osm_available: bool
    imagery_available: bool
    parcel_data_available: bool
    ai_analysis_available: bool
    historical_data_available: bool
    coverage_source: CoverageSource
    disclaimer: Optional[str] = None

# Bhopal — the only city with prototype intelligence data
BHOPAL_COVERAGE = CoverageAvailability(
    city="Bhopal",
    state="Madhya Pradesh",
    country="India",
    center_lat=23.2599,
    center_lon=77.4126,
    map_available=True,
    osm_available=True,
    imagery_available=True,          # UAV XYZ tiles exist
    parcel_data_available=True,      # 3 demo parcels exist
    ai_analysis_available=True,      # 2 demo AI features exist
    historical_data_available=False, # No second epoch — never fabricate
    coverage_source=CoverageSource.PROTOTYPE,
    disclaimer=(
        "Parcel and AI analysis data are prototype demonstration records only. "
        "They are not official government cadastral data and have no legal status."
    ),
)

def get_coverage(city_name: str) -> CoverageAvailability:
    """
    Return coverage availability for a city.
    Only Bhopal has prototype data. All other cities have base map only.
    """
    if city_name.strip().lower() == "bhopal":
        return BHOPAL_COVERAGE
    # All other Indian cities: base map + OSM context only
    # Never fabricate imagery/parcel/ai coverage for cities without real data
    from backend.app.gis.india_cities import get_city
    city = get_city(city_name)
    return CoverageAvailability(
        city=city.name if city else city_name.title(),
        state=city.state if city else "India",
        country="India",
        center_lat=city.lat if city else 20.5937,
        center_lon=city.lon if city else 78.9629,
        map_available=True,
        osm_available=True,
        imagery_available=False,
        parcel_data_available=False,
        ai_analysis_available=False,
        historical_data_available=False,
        coverage_source=CoverageSource.NONE,
        disclaimer=None,
    )
```

### 3.5 India Cities (`backend/app/gis/india_cities.py`)

Static data file. Contains at minimum 20+ major Indian cities. Structured as a list of dataclasses:

```python
@dataclass(frozen=True)
class IndiaCity:
    name: str
    state: str
    lat: float
    lon: float
    zoom: int = 12     # default zoom level when navigating to this city

INDIA_CITIES: list[IndiaCity] = [
    IndiaCity("Bhopal",     "Madhya Pradesh", 23.2599, 77.4126),
    IndiaCity("Delhi",      "Delhi",          28.6139, 77.2090),
    IndiaCity("Mumbai",     "Maharashtra",    19.0760, 72.8777),
    IndiaCity("Lucknow",    "Uttar Pradesh",  26.8467, 80.9462),
    IndiaCity("Chennai",    "Tamil Nadu",     13.0827, 80.2707),
    IndiaCity("Kanpur",     "Uttar Pradesh",  26.4499, 80.3319),
    IndiaCity("Jammu",      "Jammu & Kashmir",32.7266, 74.8570),
    IndiaCity("Srinagar",   "Jammu & Kashmir",34.0837, 74.7973),
    IndiaCity("Hyderabad",  "Telangana",      17.3850, 78.4867),
    IndiaCity("Bengaluru",  "Karnataka",      12.9716, 77.5946),
    IndiaCity("Pune",       "Maharashtra",    18.5204, 73.8567),
    IndiaCity("Kolkata",    "West Bengal",    22.5726, 88.3639),
    IndiaCity("Ahmedabad",  "Gujarat",        23.0225, 72.5714),
    IndiaCity("Jaipur",     "Rajasthan",      26.9124, 75.7873),
    IndiaCity("Nagpur",     "Maharashtra",    21.1458, 79.0882),
    IndiaCity("Patna",      "Bihar",          25.5941, 85.1376),
    IndiaCity("Indore",     "Madhya Pradesh", 22.7196, 75.8577),
    IndiaCity("Coimbatore", "Tamil Nadu",     11.0168, 76.9558),
    IndiaCity("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185),
    IndiaCity("Vadodara",   "Gujarat",        22.3072, 73.1812),
]
```

### 3.6 Coverage Endpoint (`backend/app/api/v1/coverage.py`)

```python
@router.get("/{city_slug}", summary="Coverage availability for a city")
async def get_city_coverage(city_slug: str) -> JSONResponse:
    # city_slug: lowercase, hyphenated (e.g., "bhopal", "new-delhi")
    city_name = city_slug.replace("-", " ").title()
    coverage = get_coverage(city_name)
    return JSONResponse(content=coverage_to_dict(coverage))
```

### 3.7 Location Search Endpoint (`backend/app/api/v1/locations.py`)

```python
@router.get("/search", summary="Search India cities/locations")
async def search_locations(q: str, country: str = "India") -> JSONResponse:
    """
    Fuzzy/substring search over the static India city list.
    Returns coverage availability for each result.
    Never fabricates intelligence for non-Bhopal results.
    """
    q_lower = q.lower().strip()
    matches = [c for c in INDIA_CITIES
               if q_lower in c.name.lower() or q_lower in c.state.lower()]
    
    results = []
    for city in matches[:10]:  # cap results
        coverage = get_coverage(city.name)
        results.append({
            "name": city.name,
            "state": city.state,
            "country": "India",
            "center": {"lat": city.lat, "lon": city.lon},
            "zoom_level": city.zoom,
            "coverage": coverage_to_dict(coverage),
        })
    
    return JSONResponse(content={"query": q, "results": results, "total": len(results)})
```

### 3.8 `main.py` Router Registration

Add to `backend/app/main.py`:
```python
from app.api.v1 import tiles, osm_layers, coverage, locations

app.include_router(tiles.router,      prefix="/api/v1/tiles",     tags=["tiles"])
app.include_router(osm_layers.router, prefix="/api/v1/osm",       tags=["osm"])
app.include_router(coverage.router,   prefix="/api/v1/coverage",  tags=["coverage"])
app.include_router(locations.router,  prefix="/api/v1/locations", tags=["locations"])
```

---

## 4. Frontend Design

### 4.1 India-Scale Constants (`drishtigis/lib/gis/india.ts`)

```typescript
/** India national center — used for default map load */
export const INDIA_CENTER = {
  lat: 20.5937,
  lon: 78.9629,
  zoom: 5,
} as const;

/** Bhopal city center — used for city-level navigation */
export const BHOPAL_CITY_CENTER = {
  lat: 23.2599,
  lon: 77.4126,
  zoom: 12,
} as const;

/** Distance threshold (km) for showing coverage unavailability notice */
export const COVERAGE_UNAVAILABLE_THRESHOLD_KM = 10;

/** Haversine distance between two points in km */
export function distanceKm(
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number { /* haversine formula */ }
```

### 4.2 Coverage Types (`drishtigis/lib/gis/coverage.ts`)

```typescript
export type CoverageSource = "prototype" | "production" | "none";

export interface CoverageAvailability {
  city: string;
  state: string;
  country: "India";
  center: { lat: number; lon: number };
  map_available: boolean;
  osm_available: boolean;
  imagery_available: boolean;
  parcel_data_available: boolean;
  ai_analysis_available: boolean;
  historical_data_available: boolean;
  coverage_source: CoverageSource;
  disclaimer?: string;
}
```

### 4.3 API Client (`drishtigis/lib/api/`)

Each file is a thin typed wrapper around `fetch`. All use `NEXT_PUBLIC_API_URL` from env.

**`tiles.ts`** — tile URL builder (no fetch needed, used directly by MapLibre):
```typescript
export function getBhopalTileUrl(): string {
  return `${process.env.NEXT_PUBLIC_API_URL}/api/v1/tiles/bhopal/{z}/{x}/{y}.png`;
}
```

**`osm.ts`** — OSM layer fetcher:
```typescript
export type OsmLayer = "buildings" | "roads" | "waterways" | "landuse";
export async function fetchOsmLayer(layer: OsmLayer): Promise<GeoJSON.FeatureCollection>
```

**`parcels.ts`**:
```typescript
export async function fetchParcels(city: string): Promise<ParcelListResponse>
export async function fetchParcel(propertyId: string): Promise<ParcelDetailResponse>
```

**`coverage.ts`**:
```typescript
export async function fetchCoverage(citySlug: string): Promise<CoverageAvailability>
```

**`locations.ts`**:
```typescript
export async function searchLocations(q: string): Promise<LocationSearchResponse>
```

### 4.4 MapLibreMap — Extended Props and Layer Architecture

The existing `MapLibreMapProps` interface is extended:

```typescript
export interface MapLibreMapProps {
  center?: [number, number];    // default: India center [78.97, 20.59]
  zoom?: number;                 // default: 5 (India overview)
  styleUrl?: string;
  height?: string;
  onLoad?: () => void;
  // New:
  onParcelClick?: (propertyId: string) => void;
  initialLayers?: LayerVisibility;
}

export interface LayerVisibility {
  uavImagery: boolean;
  parcels: boolean;
  aiFeatures: boolean;
  osmBuildings: boolean;
  osmRoads: boolean;
  osmWaterways: boolean;
  osmLanduse: boolean;
}
```

Default `center` changes from `BHOPAL_MAP_CONFIG.center` to `INDIA_CENTER` (`[78.9629, 20.5937]`). The map starts at India overview (zoom 5) and the user navigates to Bhopal, not the other way around.

**Layer loading strategy in `useEffect`:**

```
map.on("load") {
  // 1. Always add: UAV bounds indicator (existing)
  // 2. Lazy-load data sources on first zoom into Bhopal area:
  //    - Add raster source "uav-tiles-bhopal" → tile URL
  //    - Add OSM geojson sources (fetch from API)
  //    - Add parcel + AI feature sources (fetch from API)
  // 3. Layer visibility follows initialLayers prop
  // 4. Zoom threshold: OSM/parcel layers only populated at zoom >= 13
}

map.on("moveend") {
  // Check if we've entered/left Bhopal area
  // Trigger coverage indicator update
  // Lazy-load sources if zooming into Bhopal
}
```

**Layer z-order (back to front):**
1. Base map (style)
2. OSM landuse fill (very transparent)
3. UAV raster tiles (imagery, above landuse)
4. OSM buildings fill (light)
5. OSM buildings outline
6. OSM roads
7. OSM waterways
8. Parcel fills (ochre, translucent)
9. Parcel outlines (forest green)
10. AI feature fills (amber, translucent)
11. AI feature outlines
12. Bhopal bounds indicator (existing)

### 4.5 LayerControl Component (`drishtigis/components/map/LayerControl.tsx`)

```typescript
"use client";
interface LayerControlProps {
  visibility: LayerVisibility;
  onChange: (layer: keyof LayerVisibility, visible: boolean) => void;
}
export function LayerControl({ visibility, onChange }: LayerControlProps)
```

- Positioned absolute, top-right below navigation controls
- Minimal visual design — checkboxes or toggle buttons, DrishtiGIS color tokens
- Shows "UAV Imagery", "Parcels", "AI Features", "OSM Roads", "OSM Buildings", "OSM Water", "OSM Land Use"
- Accessibility: keyboard navigable, ARIA labels

### 4.6 PropertyPanel Component (`drishtigis/components/map/PropertyPanel.tsx`)

```typescript
"use client";
interface PropertyPanelProps {
  propertyId: string | null;    // null = panel closed
  onClose: () => void;
}
export function PropertyPanel({ propertyId, onClose }: PropertyPanelProps)
```

- Fetches `GET /api/v1/parcels/{propertyId}` on `propertyId` change
- Loading state: skeleton
- Error state: "Property data not available"
- Displays all fields from `REQ-PROP-02`
- Prototype disclaimer always visible
- Positioned as a slide-in panel from the right side of the map

### 4.7 CoverageIndicator Component (`drishtigis/components/map/CoverageIndicator.tsx`)

```typescript
"use client";
interface CoverageIndicatorProps {
  nearBhopal: boolean;  // computed from map center vs BHOPAL_CITY_CENTER
}
export function CoverageIndicator({ nearBhopal }: CoverageIndicatorProps)
```

- When `nearBhopal = false`: shows a translucent banner: "Detailed AI/property analysis is not yet available for this area. Showing India-wide map context."
- When `nearBhopal = true`: hidden (Bhopal data is available)
- Non-intrusive: bottom-left, small, auto-hides when near Bhopal

### 4.8 Updated `/app/map` Page

The map page transitions from a Bhopal-only page to an India-scale page:

```typescript
// app/app/map/page.tsx
export default function MapPage() {
  // Server Component
  // Passes no center/zoom → DynamicMap uses India defaults
  return (
    <div style={{ height: "100dvh", ... }}>
      <header>
        <span>DrishtiGIS</span>
        <LocationSearch />         {/* new: city search bar */}
      </header>
      <main style={{ flex: 1 }}>
        <DynamicMap
          height="100%"
          onParcelClick={...}       {/* wired to PropertyPanel */}
        />
        {/* PropertyPanel rendered as sibling, positioned absolute */}
      </main>
    </div>
  );
}
```

`LocationSearch` is a client component that calls `GET /api/v1/locations/search` and pans the map to the selected city.

---

## 5. Testing Design

### 5.1 Test File: `backend/tests/test_webgis.py`

Uses `starlette.testclient.TestClient` (sync). The FastAPI app is imported directly.

```python
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)
```

### 5.2 Tile Tests

```python
def test_valid_tile_returns_png():
    # Use a tile that exists: z=18, x=187445, y=113652
    response = client.get("/api/v1/tiles/bhopal/18/187445/113652.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 500  # non-empty

def test_tile_wrong_zoom_returns_404():
    response = client.get("/api/v1/tiles/bhopal/17/187445/113652.png")
    assert response.status_code == 404

def test_tile_nonexistent_coords_returns_404():
    response = client.get("/api/v1/tiles/bhopal/18/0/0.png")
    assert response.status_code == 404

def test_tile_path_traversal_rejected():
    # FastAPI's int type validation handles most cases
    # But test the response code for path-like strings
    response = client.get("/api/v1/tiles/bhopal/18/../../../etc/passwd.png")
    assert response.status_code in (404, 422)  # 422 = validation error from int cast

def test_tile_cache_header():
    response = client.get("/api/v1/tiles/bhopal/18/187445/113652.png")
    assert "public" in response.headers.get("cache-control", "")
```

### 5.3 OSM Tests

```python
def test_osm_roads_returns_geojson():
    response = client.get("/api/v1/osm/bhopal/roads")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["_source"] == "OSM_OPENSTREETMAP"
    assert "ODbL" in response.headers.get("x-osm-attribution", "")

def test_osm_all_layers_present():
    for layer in ["buildings", "roads", "waterways", "landuse"]:
        response = client.get(f"/api/v1/osm/bhopal/{layer}")
        assert response.status_code == 200, f"Layer {layer} failed"
        assert response.json()["_source"] == "OSM_OPENSTREETMAP"

def test_osm_disclaimer_present():
    response = client.get("/api/v1/osm/bhopal/roads")
    assert "NOT authoritative cadastral data" in response.json().get("_disclaimer", "")

def test_osm_unknown_layer_returns_404():
    response = client.get("/api/v1/osm/bhopal/schools")
    assert response.status_code == 404

def test_osm_bbox_nodes_not_exposed():
    # Internal file must not be served
    response = client.get("/api/v1/osm/bhopal/_bbox_nodes")
    assert response.status_code == 404

def test_osm_extraction_report_not_exposed():
    response = client.get("/api/v1/osm/bhopal/extraction_report")
    assert response.status_code == 404
```

### 5.4 Coverage / Location Tests

```python
def test_bhopal_coverage():
    response = client.get("/api/v1/coverage/bhopal")
    assert response.status_code == 200
    data = response.json()
    assert data["imagery_available"] is True
    assert data["parcel_data_available"] is True
    assert data["ai_analysis_available"] is True
    assert data["historical_data_available"] is False  # never fabricate
    assert data["coverage_source"] == "prototype"
    assert data["disclaimer"] is not None

def test_non_bhopal_city_coverage():
    response = client.get("/api/v1/coverage/lucknow")
    assert response.status_code == 200
    data = response.json()
    assert data["imagery_available"] is False
    assert data["parcel_data_available"] is False
    assert data["ai_analysis_available"] is False
    assert data["coverage_source"] == "none"

def test_location_search_bhopal():
    response = client.get("/api/v1/locations/search?q=Bhopal")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    bhopal = next(r for r in data["results"] if r["name"] == "Bhopal")
    assert bhopal["coverage"]["imagery_available"] is True

def test_location_search_non_bhopal():
    response = client.get("/api/v1/locations/search?q=Lucknow")
    data = response.json()
    lucknow = next(r for r in data["results"] if r["name"] == "Lucknow")
    assert lucknow["coverage"]["parcel_data_available"] is False

def test_location_search_arbitrary_city():
    # Must not crash or fabricate for cities not in the static list
    response = client.get("/api/v1/locations/search?q=Pune")
    assert response.status_code == 200
```

### 5.5 Integration / Source Classification Tests

```python
def test_parcel_source_classification():
    response = client.get("/api/v1/parcels?city=Bhopal")
    data = response.json()
    assert data["_source"] == "DEMO_DATA_PROTOTYPE_ONLY"
    assert response.headers.get("x-data-status") == "demo-placeholder"

def test_ai_feature_source_distinct_from_osm():
    ai_resp   = client.get("/api/v1/features")
    osm_resp  = client.get("/api/v1/osm/bhopal/buildings")
    assert ai_resp.json()["_source"] == "AI_DERIVED_DEMO"
    assert osm_resp.json()["_source"] == "OSM_OPENSTREETMAP"
    assert ai_resp.json()["_source"] != osm_resp.json()["_source"]

def test_parcel_non_bhopal_city_coverage_note():
    response = client.get("/api/v1/parcels?city=Lucknow")
    data = response.json()
    assert data["total"] == 0
    assert "_coverage_note" in data
    assert "not available for Lucknow" in data["_coverage_note"].lower() or "Lucknow" in data["_coverage_note"]

def test_discrepancy_legal_status_null():
    response = client.get("/api/v1/parcels/DRS-BPL-00101")
    data = response.json()
    for disc in data["discrepancies"]:
        assert disc["legal_status"] is None

def test_dataset_raw_data_not_exposed():
    # Dataset/ directory must never be reachable
    response = client.get("/api/v1/tiles/bhopal/../../Dataset/Drone-Images/BHOPAL/00_00.tiff")
    assert response.status_code in (404, 422)
```

---

## 6. Key Design Decisions

### 6.1 Why FileResponse for tiles and OSM?
FastAPI's `FileResponse` uses `sendfile` at the OS level, serving file bytes directly without reading them into the Python process heap. This is essential for the 27 MB buildings GeoJSON and for tile serving under load.

### 6.2 Why `int` path parameters for tiles?
FastAPI's type validation with `int` parameters rejects non-integer inputs at the Pydantic validation layer, returning HTTP 422 before any Python code runs. This handles most injection and traversal attempts automatically. The `Path.resolve()` prefix check is a defense-in-depth layer.

### 6.3 Why a static city list rather than a geocoding API?
- No external API dependency, no API key, no network failure risk
- Deterministic, testable behavior
- Prevents returning coordinates for fabricated or inappropriate locations
- Extensible by editing one file

### 6.4 Why lazy-load OSM sources at zoom ≥ 13?
Buildings GeoJSON is 27 MB. Fetching it when the user is at zoom 5 viewing all of India wastes bandwidth and slows the map. Loading is deferred until the user zooms into the Bhopal area. The `moveend` listener triggers source loading conditionally.

### 6.5 Why change default map center to India?
The application is India-scale (as stated in the requirements). Starting at Bhopal hardcodes a single-city mental model. Starting at India overview then navigating to Bhopal via search or direct navigation reflects the true scale of the product.

### 6.6 Why ALLOWED_LAYERS as frozenset rather than dynamic path?
Prevents any possibility of serving files outside the four known GeoJSON files. The allowlist is the primary security control, not path sanitization. Defense in depth: allowlist + `FileResponse` (no path injection via headers or query params).

---

## 7. Environment Configuration

Add to `.env.example` (root):
```bash
# GIS data paths — used by raster tile and OSM layer endpoints
# These are computed relative to repo root at startup; these env vars are optional overrides
BHOPAL_TILES_DIR=data/processed/tiles/bhopal
BHOPAL_OSM_DIR=data/osm/bhopal-extract

# Frontend API URL (already present, shown for reference)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

All path resolution in the backend uses `Path(__file__).resolve()` to build absolute paths — the env vars above are optional overrides for non-standard deployments.

---

## 8. Acceptance Verification Plan

The feature is considered complete when:

1. `python -m pytest backend/tests/test_webgis.py -v` passes with 0 failures
2. `cd drishtigis && npm run build` exits 0 with 0 TypeScript errors
3. `cd drishtigis && npm run lint` exits 0
4. `GET /api/v1/tiles/bhopal/18/187445/113652.png` returns a non-empty PNG
5. `GET /api/v1/osm/bhopal/roads` returns `_source: "OSM_OPENSTREETMAP"`
6. `GET /api/v1/coverage/bhopal` returns `historical_data_available: false`
7. `GET /api/v1/coverage/delhi` returns `imagery_available: false`
8. `GET /api/v1/parcels?city=Lucknow` returns `total: 0` with `_coverage_note`
9. Map loads centered on India (zoom 5), not hard-coded at Bhopal
10. Bhopal tiles render when zoomed to z17+
11. OSM roads visible at z13+, buildings at z16+
12. Parcel click loads property data in panel
13. `Dataset/` file size baseline unchanged
14. Working tree clean except intended committed files
