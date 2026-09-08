# DrishtiGIS — Implementation Progress

**Project:** DrishtiGIS — AI-Based Urban Parcel Mapping and Cadastral Feature Extraction  
**SIH Problem:** SIH26012  
**Spec:** foundation-and-data-pipeline v0.2  
**Started:** 2026-09-08  

---

## Current Phase: Phase 0 — Repository Bootstrap (IN PROGRESS)

---

## Data Assets Status

| Asset | Classification | Status |
|---|---|---|
| Bhopal UAV TIFF tiles (30) | `RAW_RASTER_UAV` | Available — unprocessed, read-only |
| Bhopal mosaic VRT | `PROCESSED_RASTER` | Not yet generated (requires GIS env) |
| Bhopal COG | `PROCESSED_RASTER` | Not yet generated (requires GIS env) |
| Bhopal XYZ tiles (z18–21) | `PROCESSED_RASTER` | Not yet generated (requires GIS env) |
| Bhopal OSM buildings | `OSM_OPENSTREETMAP` | Not yet extracted |
| Bhopal OSM roads | `OSM_OPENSTREETMAP` | Not yet extracted |
| Bhopal OSM waterways | `OSM_OPENSTREETMAP` | Not yet extracted |
| Bhopal parcel data | — | **NOT AVAILABLE** — Demo data will be used (labeled DEMO_DATA_PROTOTYPE_ONLY) |
| AI feature annotations | — | **NOT AVAILABLE** — Demo data will be used (labeled AI_DERIVED_DEMO) |
| Historical imagery (2nd epoch) | — | **NOT AVAILABLE** — Feature deferred, not fabricated |
| Bhopal DEM/DSM | — | **NOT AVAILABLE** — No Bhopal tile in DEM collection |
| Cartosat DEMs (5 tiles) | `RAW_RASTER_UAV` | Available — cover Delhi/Lucknow/Mumbai/TN, NOT Bhopal |
| India OSM PBF (1.71 GB) | `OSM_OPENSTREETMAP` | Available — server-side only, never browser |
| European Mapsforge ZIP | — | Present — geographically irrelevant, kept for reference |

---

## What Is Missing Before Full Demo Works

- **Real cadastral parcel data** — government source (Bhopal Municipal Corporation / Bhulekh MP) required for production
- **Real AI model output** — YOLO/SAM2.1 inference on Bhopal tiles required
- **Historical imagery** — second time epoch required for comparison feature
- **Bhopal DEM/DSM** — needed for terrain features (no N23 E077 tile in dataset)
- **GIS environment** — GDAL/rasterio/osmium not yet installed (required for Phase 2 + 3)

---

## Task Completion Log

### Phase 0 — Repository Bootstrap
- [ ] **0.1** — Git init, .gitignore, .env.example, progress.md
- [ ] **0.2** — Directory structure, scripts/README.md, data/README.md

### Phase 1 — Bhopal Data Validation
- [ ] **1.1** — scripts/data_prep/01_validate_bhopal_tiffs.py
- [ ] **1.2** — scripts/data_prep/05_extract_bhopal_bounds.py + bhopal_bounds.geojson

### Phase 2 — GIS Processing (requires GIS environment)
- [ ] **2.1** — GIS environment setup (conda or OSGeo4W)
- [ ] **2.2** — bhopal_mosaic.vrt
- [ ] **2.3** — bhopal_cog.tif
- [ ] **2.4** — XYZ tile pyramid + verification

### Phase 3 — OSM Extraction (requires GIS environment)
- [ ] **3.1** — bhopal-buildings/roads/waterways/landuse GeoJSON

### Phase 4 — Demo Data Package
- [ ] **4.1** — lib/demo-data/types.ts
- [ ] **4.2** — bhopal-parcels.geojson
- [ ] **4.3** — bhopal-ai-features.geojson
- [ ] **4.4** — bhopal-discrepancies.json
- [ ] **4.5** — properties.json
- [ ] **4.6** — lib/demo-data/index.ts

### Phase 5 — Frontend Foundation
- [ ] **5.1** — Next.js project init
- [ ] **5.2** — Design tokens + typography
- [ ] **5.3** — shadcn/ui
- [ ] **5.4** — MapLibre + Anime.js
- [ ] **5.5** — Base MapLibre component + /app/map
- [ ] **5.6** — All route placeholder pages
- [ ] **5.7** — Build verification

### Phase 6 — Backend Foundation
- [ ] **6.1** — FastAPI project structure
- [ ] **6.2** — Core config + database + health endpoint
- [ ] **6.3** — SQLAlchemy models (8 entities)
- [ ] **6.4** — Alembic + initial migration
- [ ] **6.5** — Placeholder API endpoints
- [ ] **6.6** — Backend verification

### Phase 7 — Integration + Documentation
- [ ] **7.1** — Full stack smoke test
- [ ] **7.2** — progress.md final update
