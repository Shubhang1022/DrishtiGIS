# Spec: DrishtiGIS Foundation and Bhopal Prototype Data Pipeline
## Technical Design

**Spec ID:** foundation-and-data-pipeline  
**Version:** 0.2  
**Status:** DRAFT — Awaiting approval before implementation  
**Alignment:** CLAUDE.md · DOC/PRD.md · DOC/requirements.md  
**Changelog:** v0.2 — AI geometry correction, historical snapshot nullability, GDAL overlap strategy, GIS environment isolation, tile verification strengthening, phased execution, data integrity preservation

---

## 1. Architecture Overview

DrishtiGIS is a map-first geospatial intelligence platform. This spec establishes the scaffolding for a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js / TypeScript / Tailwind / MapLibre)             │
│  drishtigis/                                                        │
│  - App Router pages                                                 │
│  - MapLibre GL JS (client-only)                                     │
│  - shadcn/ui component system                                       │
│  - Anime.js animations                                              │
│  - Demo data layer (lib/demo-data/)                                 │
└────────────────────┬────────────────────────────────────────────────┘
                     │ HTTP (REST / JSON)
┌────────────────────▼────────────────────────────────────────────────┐
│  BACKEND  (FastAPI / Python)                                        │
│  backend/                                                           │
│  - REST API v1                                                      │
│  - GIS services (rasterio, geopandas, shapely)                      │
│  - Raster tile server (interim)                                     │
│  - Processing pipeline (placeholder → real in later spec)           │
│  - Gemini assistant (later spec)                                     │
└────────────────────┬────────────────────────────────────────────────┘
                     │ asyncpg / SQLAlchemy
┌────────────────────▼────────────────────────────────────────────────┐
│  DATABASE  (PostgreSQL 15 + PostGIS 3 / Supabase)                  │
│  - Spatial tables (parcels, ai_features, discrepancies...)          │
│  - GIST spatial indexes                                             │
│  - EPSG:4326 geometry storage                                       │
│  - Alembic migrations                                               │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  DATA LAYER  (static files, pre-processed)                         │
│  data/processed/                                                    │
│  - XYZ raster tiles (MapLibre raster source)                        │
│  - COG (Cloud Optimized GeoTIFF)                                    │
│  - Bounds GeoJSON                                                   │
│  data/osm/                                                          │
│  - Bhopal OSM extracts (buildings, roads, waterways)               │
│  drishtigis/lib/demo-data/                                          │
│  - Demo parcels, AI features, discrepancies, properties            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Repository Structure Design

```
DrishtiGIS(SIH)/
├── .gitignore                         ← first file committed
├── .env.example                       ← safe env variable template
├── progress.md                        ← implementation status
│
├── CLAUDE.md                          ← project instructions (existing)
├── DOC/
│   ├── PRD.md                         ← product spec (existing)
│   └── requirements.md                ← software requirements (existing)
│
├── Dataset/                           ← RAW DATA — READ ONLY
│   └── Drone-Images/
│       ├── BHOPAL/          ← 30 × GeoTIFF tiles (EPSG:32643, RGB, 2.17cm/px)
│       ├── DEM FILES/       ← 5 × Cartosat-P5 DEMs (Delhi/Lucknow/Mumbai/TN)
│       ├── WATER_REGION(GEOJSON)/  ← OSM drinking water points
│       ├── india-260905.osm.pbf    ← 1.706 GB India OSM (READ ONLY, NO BROWSER)
│       └── planet_12.87,...zip     ← European Mapsforge (irrelevant, keep)
│
├── data/
│   ├── processed/                     ← pipeline outputs (gitignored if large)
│   │   ├── bhopal_validation_report.json
│   │   ├── pipeline.log
│   │   ├── bhopal_mosaic.vrt          ← GDAL virtual mosaic (references originals)
│   │   ├── bhopal_cog.tif             ← Cloud Optimized GeoTIFF
│   │   ├── bhopal_bounds.geojson      ← coverage bounding box in WGS84
│   │   └── tiles/
│   │       └── bhopal/                ← XYZ tile pyramid {z}/{x}/{y}.png
│   └── osm/
│       └── bhopal-extract/
│           ├── bhopal-buildings.geojson
│           ├── bhopal-roads.geojson
│           ├── bhopal-waterways.geojson
│           └── bhopal-landuse.geojson
│
├── scripts/
│   ├── data_prep/
│   │   ├── 01_validate_bhopal_tiffs.py
│   │   ├── 02_build_mosaic_vrt.py
│   │   ├── 03_build_cog.py
│   │   ├── 04_generate_xyz_tiles.py
│   │   ├── 05_extract_bhopal_bounds.py
│   │   └── 06_extract_osm_bhopal.py
│   ├── seed/
│   │   └── seed_demo_data.py
│   └── README.md                      ← how to run the pipeline
│
├── drishtigis/                        ← Next.js frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── .env.local                     ← gitignored
│   ├── .env.example
│   ├── app/
│   │   ├── layout.tsx                 ← root layout with fonts
│   │   ├── page.tsx                   ← landing page (placeholder)
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── app/
│   │   │   ├── location/page.tsx
│   │   │   ├── map/page.tsx           ← MapLibre integration test
│   │   │   ├── property/[id]/page.tsx
│   │   │   ├── history/page.tsx
│   │   │   ├── reports/page.tsx
│   │   │   └── assistant/page.tsx
│   │   └── admin/
│   │       ├── page.tsx
│   │       ├── datasets/
│   │       │   ├── page.tsx
│   │       │   └── upload/page.tsx
│   │       ├── processing/page.tsx
│   │       └── review/page.tsx
│   ├── components/
│   │   ├── ui/                        ← shadcn/ui generated components
│   │   └── map/
│   │       └── MapLibreMap.tsx        ← base MapLibre component (client-only)
│   ├── lib/
│   │   ├── demo-data/
│   │   │   ├── types.ts               ← TypeScript interfaces + DataSource enum
│   │   │   ├── index.ts               ← barrel export
│   │   │   ├── bhopal-parcels.geojson
│   │   │   ├── bhopal-ai-features.geojson
│   │   │   ├── bhopal-discrepancies.json
│   │   │   └── properties.json
│   │   ├── gis/
│   │   │   └── bounds.ts              ← Bhopal coverage constants
│   │   └── utils/
│   │       └── cn.ts                  ← classnames utility
│   └── public/
│       └── fonts/                     ← self-hosted typefaces
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       ├── parcels.py
│   │   │       ├── features.py
│   │   │       └── datasets.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── parcel.py
│   │   │   ├── ai_feature.py
│   │   │   ├── discrepancy.py
│   │   │   ├── dataset.py
│   │   │   ├── processing_job.py
│   │   │   ├── historical_snapshot.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── parcel.py
│   │   │   ├── feature.py
│   │   │   └── common.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── gis/
│   │   │       ├── __init__.py
│   │   │       └── raster.py          ← raster inspection utilities
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   └── utils/
│   │       └── data_source.py         ← DataSource enum (matches frontend)
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
│
└── .kiro/
    └── specs/
        └── foundation-and-data-pipeline/
            ├── requirements.md        ← this spec
            ├── design.md
            └── tasks.md
```

---

## 3. Frontend Technical Design

### 3.1 Next.js Configuration

Next.js 14 with App Router. TypeScript strict mode. The `next.config.ts` must:
- Configure a `@` path alias pointing to `drishtigis/` root
- Exclude MapLibre from SSR via webpack externals or `transpilePackages`
- Set `images.domains` for any external raster tile providers used temporarily

```typescript
// next.config.ts (outline)
const config: NextConfig = {
  transpilePackages: ['maplibre-gl'],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'maplibre-gl': path.resolve('./node_modules/maplibre-gl/dist/maplibre-gl.js'),
    };
    return config;
  },
};
```

### 3.2 Tailwind Design Tokens

The `tailwind.config.ts` must extend the default theme with the DrishtiGIS color palette from `DOC/PRD.md §4`:

```typescript
// tailwind.config.ts color extension (design values)
colors: {
  cream:  { DEFAULT: '#F7F3EC', light: '#FBF9F5', dark: '#EDE8DE' },
  beige:  { DEFAULT: '#E8E0D0', light: '#F0EBE1' },
  forest: { DEFAULT: '#2D5016', light: '#3A6B1E', dark: '#1E360F' },
  olive:  { DEFAULT: '#6B7C45', light: '#7D9154', dark: '#566235' },
  ochre:  { DEFAULT: '#C4922A', light: '#D4A84B', dark: '#A67820' },
  gold:   { DEFAULT: '#D4A017', light: '#E0B030' },
  charcoal: { DEFAULT: '#2C2C2C', light: '#3D3D3D', dark: '#1A1A1A' },
  'soft-gray': { DEFAULT: '#8A8A8A', light: '#A0A0A0', dark: '#6B6B6B' },
},
```

Font families:
```typescript
fontFamily: {
  display: ['var(--font-display)', 'Georgia', 'serif'],
  ui:      ['var(--font-ui)', 'system-ui', 'sans-serif'],
},
```

### 3.3 Typography Implementation

Fonts are loaded via `next/font` in the root layout. Options for Google Fonts (no self-hosting friction):
- Display: **Playfair Display** or **Libre Baskerville** — editorial serif matching PRD intent
- UI: **Inter** or **DM Sans** — modern, clean, highly legible

The root `layout.tsx` applies font CSS variables:
```typescript
const displayFont = Playfair_Display({ ... variable: '--font-display' });
const uiFont = Inter({ ... variable: '--font-ui' });
```

### 3.4 MapLibre Integration Design

MapLibre must be loaded **client-side only**. The canonical pattern:

```typescript
// components/map/MapLibreMap.tsx
'use client';
import { useEffect, useRef } from 'react';
import type { Map } from 'maplibre-gl';

export function MapLibreMap({ /* props */ }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);

  useEffect(() => {
    // Dynamic import — avoids SSR
    import('maplibre-gl').then(({ Map, NavigationControl }) => {
      if (!containerRef.current || mapRef.current) return;
      mapRef.current = new Map({
        container: containerRef.current,
        style: FREE_BASE_STYLE,
        center: [BHOPAL_CENTER_LNG, BHOPAL_CENTER_LAT],
        zoom: 17,
      });
    });
    return () => mapRef.current?.remove();
  }, []);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
}
```

The page uses dynamic import:
```typescript
// app/app/map/page.tsx
import dynamic from 'next/dynamic';
const MapLibreMap = dynamic(
  () => import('@/components/map/MapLibreMap').then(m => m.MapLibreMap),
  { ssr: false, loading: () => <MapSkeleton /> }
);
```

**Base map tile source (free, no API key required):**  
Use OpenFreeMap (https://openfreemap.org/) or MapLibre's demotiles. This avoids MapTiler/Mapbox API key requirements during development.

**Bhopal coverage constants** (`lib/gis/bounds.ts`):
```typescript
export const BHOPAL_UAV_BOUNDS = {
  // Computed from TIFF metadata (EPSG:4326)
  minLng: 77.4130,
  maxLng: 77.4227,
  minLat: 23.2557,
  maxLat: 23.2567,
  centerLng: 77.4178,
  centerLat: 23.2562,
  epsg: 'EPSG:32643',
  tileCount: 30,
  resolutionM: 0.02171,
} as const;

export const BHOPAL_CITY = {
  centerLng: 77.4126,
  centerLat: 23.2599,
  zoom: 12,
} as const;
```

### 3.5 Demo Data Module Design

```typescript
// lib/demo-data/types.ts

export enum DataSource {
  OFFICIAL_REFERENCE      = 'OFFICIAL_REFERENCE',
  AI_DERIVED              = 'AI_DERIVED',
  OSM_OPENSTREETMAP       = 'OSM_OPENSTREETMAP',
  DEMO_DATA_PROTOTYPE_ONLY = 'DEMO_DATA_PROTOTYPE_ONLY',
  RAW_RASTER_UAV          = 'RAW_RASTER_UAV',
  PROCESSED_RASTER        = 'PROCESSED_RASTER',
  AI_DERIVED_DEMO         = 'AI_DERIVED_DEMO',
}

export interface DemoParcel {
  type: 'Feature';
  geometry: GeoJSON.MultiPolygon | GeoJSON.Polygon;
  properties: {
    id: string;
    property_id: string;       // DRS-BPL-XXXXX
    plot_number: string;
    survey_number: string;
    area_m2: number;
    land_type: 'Residential' | 'Commercial' | 'Agricultural' | 'Industrial';
    status: 'Verified' | 'Pending' | 'Disputed';
    city: 'Bhopal';            // type literal — never another city
    state: 'Madhya Pradesh';
    _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
    _disclaimer: string;
    _datasetLabel: 'Prototype Dataset — Bhopal';
  };
}

export interface DemoAIFeature {
  type: 'Feature';
  geometry: GeoJSON.Polygon;
  properties: {
    id: string;
    feature_type: 'building' | 'road' | 'tree' | 'water';
    confidence: number;        // 0–1
    area_m2: number;
    model: string;
    model_version: string;
    dataset: string;
    _source: DataSource.AI_DERIVED_DEMO;
    _disclaimer: string;
  };
}

export interface DemoDiscrepancy {
  id: string;
  parcel_id: string;
  feature_id: string;
  type: 'area_mismatch' | 'boundary_mismatch' | 'new_structure';
  official_value: number;
  ai_value: number;
  difference: number;
  difference_pct: number;
  severity: 'low' | 'medium' | 'high';
  status: 'pending_review';
  description: string;         // "Potential discrepancy — requires verification"
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
}

export interface DemoProperty {
  id: string;
  parcel_id: string;
  property_id: string;
  address: string;
  city: 'Bhopal';
  state: 'Madhya Pradesh';
  land_type: string;
  status: string;
  record_status: 'Demo record';
  last_updated: string;
  source_label: 'Prototype Dataset — Bhopal';
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
  _disclaimer: string;
}
```

### 3.6 Route Structure and Placeholder Strategy

All routes are created at initialization with clear placeholder content, ensuring no 404s during development and allowing progressive enhancement:

| Route | Initial Content | Real Content Phase |
|---|---|---|
| `/` | Hero text + CTA placeholder | Phase 1 UI |
| `/login` | Minimal form skeleton | Phase 1 UI |
| `/register` | Minimal form skeleton | Phase 1 UI |
| `/app/location` | "Location onboarding — coming soon" | Phase 1 UI |
| `/app/map` | MapLibre test map (Bhopal bounds) | Phase 2 UI |
| `/app/property/[id]` | "Property view — coming soon" | Phase 2 UI |
| `/app/history` | "History — coming soon" | Phase 3 UI |
| `/app/reports` | "Reports — coming soon" | Phase 3 UI |
| `/app/assistant` | "Assistant — coming soon" | Phase 3 UI |
| `/admin` | "Admin — coming soon" | Phase 4 UI |
| `/admin/datasets` | "Datasets — coming soon" | Phase 4 UI |
| `/admin/datasets/upload` | "Upload — coming soon" | Phase 4 UI |
| `/admin/processing` | "Processing — coming soon" | Phase 4 UI |
| `/admin/review` | "Review — coming soon" | Phase 4 UI |

---

## 4. Backend Technical Design

### 4.1 FastAPI Application Structure

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import health, parcels, features, datasets
from app.core.config import settings

app = FastAPI(
    title="DrishtiGIS API",
    version="0.1.0",
    description="AI-powered urban geospatial intelligence platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(parcels.router, prefix="/api/v1/parcels", tags=["parcels"])
app.include_router(features.router, prefix="/api/v1/features", tags=["features"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
```

### 4.2 Configuration Design

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import list

class Settings(BaseSettings):
    APP_NAME: str = "DrishtiGIS API"
    VERSION: str = "0.1.0"
    DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    GEMINI_API_KEY: str = ""
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SECRET_KEY: str
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 4.3 Database Connection Design

Using SQLAlchemy async engine with asyncpg driver. This works with both Supabase (standard PostgreSQL connection string) and a self-hosted PostGIS instance — fully portable.

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 4.4 SQLAlchemy Model Design

Models use `geoalchemy2` for PostGIS geometry columns when available, or fall back to text storage of WKT for environments without PostGIS. For this spec, the models are written for PostGIS.

```python
# backend/app/models/parcel.py (representative)
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.core.database import Base
import uuid

class Parcel(Base):
    __tablename__ = "parcels"
    
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id   = Column(String, unique=True, nullable=True)
    plot_number   = Column(String, nullable=True)
    survey_number = Column(String, nullable=True)
    area_m2       = Column(Numeric, nullable=True)
    land_type     = Column(String, nullable=True)
    geometry      = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=True)
    source        = Column(String, nullable=False)  # DataSource enum value
    dataset_id    = Column(UUID(as_uuid=True), ForeignKey('datasets.id'), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at    = Column(DateTime(timezone=True), server_default=text('now()'))
```

**HistoricalSnapshot model note:** The `change_type` column must be explicitly `nullable=True`. A `NULL` value means "no historical change classification is available because real multi-temporal imagery is not available for the prototype dataset." The prototype seed record MUST use `change_type=None`. Do not fabricate a classification value.

```python
# backend/app/models/historical_snapshot.py (excerpt)
class HistoricalSnapshot(Base):
    __tablename__ = "historical_snapshots"
    ...
    change_type = Column(String, nullable=True)  # NULL = no real multi-temporal data
    # Valid non-null values: 'new_structure', 'boundary_change', 'demolition', 'land_use_change'
    ...
```

### 4.5 DataSource Enum (Backend)

```python
# backend/app/utils/data_source.py
from enum import Enum

class DataSource(str, Enum):
    OFFICIAL_REFERENCE       = "OFFICIAL_REFERENCE"
    AI_DERIVED               = "AI_DERIVED"
    OSM_OPENSTREETMAP        = "OSM_OPENSTREETMAP"
    DEMO_DATA_PROTOTYPE_ONLY = "DEMO_DATA_PROTOTYPE_ONLY"
    RAW_RASTER_UAV           = "RAW_RASTER_UAV"
    PROCESSED_RASTER         = "PROCESSED_RASTER"
    AI_DERIVED_DEMO          = "AI_DERIVED_DEMO"
```

This enum is shared between models, schemas, and seeding scripts. It mirrors the TypeScript `DataSource` enum in the frontend exactly.

### 4.6 Health Endpoint Design

```python
# backend/app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "ok",
        "version": settings.VERSION,
        "database": db_status,
    }
```

---

## 5. Database Design

### 5.1 Migration Strategy

Alembic is configured with async support. The initial migration (version `001_initial_schema`) creates:
1. The PostGIS extension (if not exists)
2. All 8 tables with constraints
3. GIST spatial indexes on all geometry columns
4. Trigger functions for `updated_at` auto-update

```sql
-- Spatial index pattern applied to all geometry columns
CREATE INDEX idx_parcels_geometry ON parcels USING GIST (geometry);
CREATE INDEX idx_ai_features_geometry ON ai_features USING GIST (geometry);
CREATE INDEX idx_discrepancies_parcel_id ON discrepancies (parcel_id);
-- etc.
```

### 5.2 Supabase vs Self-Hosted Portability

The schema uses only standard PostgreSQL + PostGIS constructs. The only Supabase-specific items (if used) are:
- The connection string format (uses `pooler.supabase.com` for connection pooling)
- The `supabase` Python SDK (used only for auth in a later spec, not for DB queries)

All database access uses SQLAlchemy + asyncpg directly. If the project moves to a self-hosted PostGIS instance, only the `DATABASE_URL` environment variable changes.

### 5.3 Seed Data Design

The seed script (`scripts/seed/seed_demo_data.py`) inserts:
1. A demo `datasets` record for the Bhopal prototype
2. 3–5 demo `parcels` records (geometries within confirmed TIFF bounds)
3. 3–5 demo `properties` records
4. Demo `ai_features` records (building polygons, labeled `AI_DERIVED_DEMO`)
5. 1–2 demo `discrepancies` records

All seeded records carry `source = DataSource.DEMO_DATA_PROTOTYPE_ONLY`.

The seed script is idempotent: it checks for existing records by `source = 'DEMO_DATA_PROTOTYPE_ONLY'` and skips if already seeded.

**Demo parcel geometry coordinates** (within confirmed TIFF bounds, in WGS84):

The 30 tiles cover approximately `77.413°E–77.423°E, 23.2557°N–23.2567°N`. Demo parcel polygons are small rectangles within this area. Example parcel DRS-BPL-00101 at approximately `77.4155°E, 23.2563°N`.

---

## 6. Data Pipeline Design

### 6.1 Processing Script Sequence

```
scripts/data_prep/
│
├── 01_validate_bhopal_tiffs.py
│     Input:  Dataset/Drone-Images/BHOPAL/*.tiff (READ ONLY)
│     Output: data/processed/bhopal_validation_report.json
│     Tools:  rasterio or Pillow (already installed)
│
├── 02_build_mosaic_vrt.py
│     Input:  Dataset/Drone-Images/BHOPAL/*.tiff (READ ONLY)
│     Output: data/processed/bhopal_mosaic.vrt
│     Tools:  gdalbuildvrt (GDAL CLI) or rasterio
│
├── 03_build_cog.py
│     Input:  data/processed/bhopal_mosaic.vrt
│     Output: data/processed/bhopal_cog.tif
│     Tools:  gdal_translate (GDAL CLI) or rasterio
│
├── 04_generate_xyz_tiles.py
│     Input:  data/processed/bhopal_cog.tif
│     Output: data/processed/tiles/bhopal/{z}/{x}/{y}.png
│     Tools:  gdal2tiles.py (GDAL CLI)
│     CRS:    Reproject EPSG:32643 → EPSG:3857 during tiling
│
├── 05_extract_bhopal_bounds.py
│     Input:  data/processed/bhopal_validation_report.json
│     Output: data/processed/bhopal_bounds.geojson
│     Tools:  Python (json + geojson construction)
│
└── 06_extract_osm_bhopal.py
      Input:  Dataset/Drone-Images/india-260905.osm.pbf (READ ONLY)
      Output: data/osm/bhopal-extract/{buildings,roads,waterways,landuse}.geojson
      Tools:  osmium-tool CLI or pyosmium
```

### 6.2 GDAL Dependency Strategy

GDAL on Windows must be installed in an **isolated GIS environment** (see REQ-DATA-09). Do NOT install into the global Python environment.

**Option A (preferred for this project): conda environment**
```bash
conda create -n drishtigis-gis python=3.11
conda activate drishtigis-gis
conda install -c conda-forge gdal rasterio geopandas shapely pyproj fiona
# Then verify:
gdalinfo --version
python -c "import rasterio; print(rasterio.__version__)"
```

**Option B: OSGeo4W shell (Windows)**
- Download the OSGeo4W installer from https://trac.osgeo.org/osgeo4w/
- Install: `gdal`, `python3-gdal`, `gdal-python-tools`
- Run all pipeline scripts from within the OSGeo4W shell — this provides its own isolated Python + GDAL environment
- The OSGeo4W Python does not interfere with the system Python 3.14 installation

The chosen option must be documented in `scripts/README.md`. All pipeline scripts include a header comment identifying the required environment.

### 6.3 GDAL VRT Overlap Strategy

`gdalbuildvrt` resolves overlapping pixels using a **last-file-wins** rule by default: the last file in the input list whose extent covers a given pixel is used. This is the only overlap behavior natively supported by `gdalbuildvrt` without additional processing.

For the Bhopal dataset, the ~1.37m tile overlap is small relative to the tile size (44.5m). Last-file-wins produces a visually acceptable mosaic without visible seams for this dataset.

The implementation must:
1. List input files in a deterministic sort order (`sorted(glob(...))`) so the last-wins result is reproducible
2. Log the overlap strategy to `pipeline.log`: `"Overlap strategy: gdalbuildvrt last-file-wins (default). Files sorted lexicographically."`
3. NOT claim blending or averaging unless a separate `gdalwarp -r average` blending step is explicitly implemented and verified
4. After tiling, visually inspect a tile at the seam between two overlapping tiles to confirm no hard edge artefact

If seam artefacts are visible after inspection, a blending step via `gdalwarp` must be added as a new pipeline stage (documented separately, not silently assumed).

### 6.4 Rasterio-First Fallback Strategy

Since Pillow already confirmed the GeoTIFF metadata during the audit, the data pipeline scripts will be written in two modes:

1. **With rasterio/GDAL** — full pipeline including mosaic, COG, and XYZ tiles
2. **Pillow fallback** — validation only, with clear instructions for next steps

This ensures that the frontend can be developed in parallel while GIS tool installation is sorted out. MapLibre can display the individual tile GeoTIFFs via a simple FastAPI static file server as an interim until the XYZ tile pyramid is ready.

### 6.5 OSM Extraction Design

Target bbox for osmium extraction (2 km buffer around UAV coverage area):
```
Left:   77.38°E
Bottom: 23.24°N
Right:  77.44°E
Top:    23.27°N
```

osmium command pattern (run inside the GIS environment, NOT in the main application environment):
```bash
osmium extract \
  --bbox 77.38,23.24,77.44,23.27 \
  Dataset/Drone-Images/india-260905.osm.pbf \
  --output data/osm/bhopal-extract/bhopal-area.osm.pbf

# Then convert to GeoJSON by feature type:
osmium export --geometry-types=polygon \
  --output-format=geojson \
  data/osm/bhopal-extract/bhopal-area.osm.pbf \
  --output data/osm/bhopal-extract/bhopal-all.geojson
```

The Python script then filters by OSM tags (building=*, highway=*, waterway=*, landuse=*) into separate files.

---

## 7. Demo Data Geometry Design

### 7.1 Parcel Geometries

Three demo parcels designed to fall within the verified TIFF coverage bounds:

**DRS-BPL-00101** — "Plot 101"
- Center: 77.4155°E, 23.2563°N
- Approximate footprint: ~30m × 20m rectangle
- Area: ~600 m²
- Land type: Residential

**DRS-BPL-00102** — "Plot 102"
- Center: 77.4165°E, 23.2562°N
- Approximate footprint: ~25m × 22m
- Area: ~550 m²
- Land type: Residential

**DRS-BPL-00103** — "Plot 103"
- Center: 77.4175°E, 23.2563°N
- Approximate footprint: ~40m × 18m
- Area: ~720 m²
- Land type: Commercial

All three parcels labeled `"_source": "DEMO_DATA_PROTOTYPE_ONLY"` and `"_disclaimer": "This parcel is prototype demonstration data only. It is not derived from official government cadastral records."`.

### 7.2 AI Feature Geometries

Building footprints that **partially extend outside** the parcel boundary to create a spatially correct discrepancy. This is the only geometrically honest way to represent an AI-detected structure whose footprint exceeds the recorded parcel area — the excess area must appear in the map geometry, not only as a number in a record.

**AI-BLD-00101** — Building footprint for Plot 101
- The AI-detected polygon starts from within the parcel DRS-BPL-00101 and extends ~3–4 metres beyond one parcel edge
- Computed area of AI polygon: ~672 m²
- Parcel recorded area: 600 m²
- The polygon intersection with the parcel is visually clear; the portion outside is also visible
- Confidence: 0.91
- Model: "demo_placeholder_v0.1"
- Discrepancy: +72 m² (+12.0%) — this number must match the actual computed difference between parcel area and AI polygon area

**AI-BLD-00102** — Building footprint for Plot 102
- The AI-detected polygon partially overlaps the boundary of parcel DRS-BPL-00102 along one edge
- Computed area of AI polygon: ~575 m²
- Parcel recorded area: 550 m²
- Confidence: 0.87
- Discrepancy: +25 m² (+4.5%)

All labeled `"_source": "AI_DERIVED_DEMO"` with explicit `"_disclaimer": "AI-derived observation — requires verification. Not a legal or official determination."`.

The `area_m2` field in each AI feature GeoJSON record must be the computed area of the polygon geometry, not an arbitrary number chosen to match the discrepancy value. The discrepancy values in `bhopal-discrepancies.json` are then derived from `(ai_area - parcel_area)`.

All discrepancy records use the exact UI language prescribed in `DOC/PRD.md §16` and `CLAUDE.md §26`:

```json
{
  "description": "The AI-derived building footprint differs from the recorded property area. This is a potential discrepancy that requires field verification.",
  "ui_label": "Potential discrepancy — Requires verification",
  "severity_label": "Medium",
  "legal_status": null,
  "_disclaimer": "This potential discrepancy was detected by an AI model and is not a legal determination. It should be verified by a qualified surveyor before any action is taken."
}
```

---

## 8. Security Design

### 8.1 Environment Variable Boundaries

| Variable | Frontend (NEXT_PUBLIC_) | Backend Only |
|---|---|---|
| `SUPABASE_URL` | ✅ (anon key operations) | ✅ (service key operations) |
| `SUPABASE_ANON_KEY` | ✅ | — |
| `SUPABASE_SERVICE_KEY` | ❌ NEVER | ✅ |
| `GEMINI_API_KEY` | ❌ NEVER | ✅ |
| `DATABASE_URL` | ❌ NEVER | ✅ |
| `SECRET_KEY` | ❌ NEVER | ✅ |
| `MAP_TILE_URL` | ✅ | — |
| `API_URL` | ✅ | — |

### 8.2 File Upload Security (Future)
Though dataset upload is not implemented in this spec, the backend structure anticipates it. When implemented:
- Validate MIME type server-side (not just extension)
- Validate file size before reading
- Validate CRS before processing
- Never execute uploaded files
- Store uploads outside the web root

---

## 9. Testing Design

### 9.1 Frontend Verification

At the end of this spec's implementation:
```bash
cd drishtigis
npm run build        # must exit 0, zero TypeScript errors
npm run lint         # must exit 0
npm run dev          # must start without error
```

Manual check: Open `http://localhost:3000/app/map` — MapLibre map must render, centered on Bhopal, showing the UAV tile coverage bounds.

### 9.2 Backend Verification

```bash
cd backend
uvicorn app.main:app --reload
curl http://localhost:8000/health
# Expected: {"status": "ok", "version": "0.1.0", "database": "connected"}
curl http://localhost:8000/docs
# Expected: Swagger UI loads
```

### 9.3 Data Pipeline Verification

```bash
cd scripts/data_prep
python 01_validate_bhopal_tiffs.py
# Expected: all 30 tiles PASS, JSON report generated

python 05_extract_bhopal_bounds.py
# Expected: bhopal_bounds.geojson generated with correct WGS84 bounds
```

Verification of bounds GeoJSON: open in https://geojson.io — the polygon should appear in Bhopal, MP, India.

### 9.4 Demo Data Verification

Manual checks:
- Open `drishtigis/lib/demo-data/bhopal-parcels.geojson` in geojson.io — parcels must appear in Bhopal
- Confirm no feature has `city` != `"Bhopal"`
- Confirm every feature has `_source` field
- Confirm every feature has `_disclaimer` field
- TypeScript: `lib/demo-data/index.ts` must compile without type errors

---

## 10. Dependency Installation Plan

### Frontend (`drishtigis/`)
```bash
npx create-next-app@latest . --typescript --tailwind --app --src-dir=false --import-alias="@/*"
npx shadcn-ui@latest init
npm install maplibre-gl
npm install @types/maplibre-gl
npm install animejs
npm install @types/animejs
npm install next-fonts  # if needed for self-hosted fonts
```

### Backend (`backend/`) — main application environment
```bash
# Install into the existing system Python 3.14 environment
# These packages do NOT require GDAL or binary GIS dependencies
pip install geoalchemy2==0.15.2
pip install pyproj==3.7.0
# All other packages are already installed: fastapi, uvicorn, sqlalchemy, asyncpg, etc.
```

### GIS Data Pipeline — ISOLATED environment (do NOT mix with backend)
```bash
# Option A: conda (preferred)
conda create -n drishtigis-gis python=3.11
conda activate drishtigis-gis
conda install -c conda-forge gdal rasterio geopandas shapely pyproj fiona osmium-tool

# Option B: OSGeo4W shell (Windows)
# Download https://trac.osgeo.org/osgeo4w/ — installs isolated Python + GDAL
# Run all data_prep/ scripts from within the OSGeo4W shell

# Verify after installation (run inside the GIS environment):
gdalinfo --version            # must show 3.x+
python -c "import rasterio"   # must not error
python -c "import geopandas"  # must not error
# Then cross-check one tile:
# gdalinfo Dataset/Drone-Images/BHOPAL/00_00.tiff
```

The main application (`backend/`, `drishtigis/`) and the GIS pipeline scripts run in separate environments. They never share a Python interpreter during the pipeline phase.

---

## 11. Deferred Decisions

The following architectural decisions are explicitly deferred to later specs:

| Decision | Deferred Until |
|---|---|
| Authentication implementation (Supabase Auth vs custom JWT) | Phase 1 UI spec |
| Vector tile generation (PostGIS → MVT → MapLibre) | Phase 2 scaling spec |
| YOLO model selection and weights | AI pipeline spec |
| SAM2.1 integration | AI pipeline spec |
| Gemini assistant grounding strategy | Assistant spec |
| AWS deployment and cost controls | Deployment spec |
| Report generation (PDF format) | Reports spec |
| Admin dataset upload validation API | Admin spec |
| Production CORS and security hardening | Deployment spec |
