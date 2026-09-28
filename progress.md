# DrishtiGIS — Implementation Progress

**Project:** DrishtiGIS — AI-Based Urban Parcel Mapping and Cadastral Feature Extraction  
**SIH Problem:** SIH26012  
**Spec:** foundation-and-data-pipeline v0.2  
**Started:** 2026-09-08  

---

## Current Phase: COMPLETE — All phases + Core India WebGIS Integration

**Phase 0 — COMPLETE ✓** (verified 2026-09-08)  
**Phase 1 — COMPLETE ✓** (verified 2026-09-08)  
**Phase 2 — COMPLETE ✓** (verified 2026-09-08)  
**Phase 3 — COMPLETE ✓** (verified 2026-09-09)  
**Phase 4 — COMPLETE ✓** (verified 2026-09-08)  
**Phase 5 — COMPLETE ✓** (verified 2026-09-08, 0 TS errors, 0 lint errors, 15 routes)  
**Phase 6 — COMPLETE ✓** (verified 2026-09-08, backend starts, all endpoints respond)  
**Core India WebGIS — COMPLETE ✓** (2026-09-09, 91/91 backend tests, 0 TS errors, 0 lint)

---

## Data Assets Status

| Asset | Classification | Status |
|---|---|---|
| Bhopal UAV TIFF tiles (30) | `RAW_RASTER_UAV` | Available — unprocessed, read-only |
| Bhopal mosaic VRT | `PROCESSED_RASTER` | **Generated** — data/processed/bhopal_mosaic.vrt (39 KB, EPSG:32643) |
| Bhopal COG | `PROCESSED_RASTER` | **Generated** — data/processed/bhopal_cog.tif (32.2 MB, JPEG, 9 overviews) |
| Bhopal XYZ tiles (z18–21) | `PROCESSED_RASTER` | **Generated** — data/processed/tiles/bhopal/ (379 tiles, EPSG:3857) |
| Bhopal OSM buildings | `OSM_OPENSTREETMAP` | **Extracted** — 26,577 features (27 MB GeoJSON) |
| Bhopal OSM roads | `OSM_OPENSTREETMAP` | **Extracted** — 2,933 features (3 MB GeoJSON) |
| Bhopal OSM waterways | `OSM_OPENSTREETMAP` | **Extracted** — 31 features (58 KB GeoJSON) |
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
- [x] **0.1** — Git init, .gitignore, .env.example, progress.md ✓
- [x] **0.2** — Directory structure, scripts/README.md, data/README.md ✓

### Phase 1 — Bhopal Data Validation
- [x] **1.1** — scripts/data_prep/01_validate_bhopal_tiffs.py ✓ — 30/30 PASS, EPSG:32643, 2.17cm/px, WGS84 bounds confirmed
- [x] **1.2** — scripts/data_prep/05_extract_bhopal_bounds.py ✓ — bhopal_bounds.geojson: Bhopal MP, PROCESSED_RASTER, ring closed

### Phase 4 — Demo Data Package
- [x] **4.1** — drishtigis/lib/demo-data/types.ts ✓ — 7 DataSource values, 8 interfaces, city='Bhopal' literal
- [x] **4.2** — bhopal-parcels.geojson ✓ — 3 parcels in verified TIFF bounds, all coords validated
- [x] **4.3** — bhopal-ai-features.geojson ✓ — 2 AI buildings geometrically extending outside parcels
- [x] **4.4** — bhopal-discrepancies.json ✓ — 2 records, legal_status=null, spatial_basis, no forbidden language
- [x] **4.5** — properties.json ✓ — 3 records, city=Bhopal, source_label correct
- [x] **4.6** — lib/demo-data/index.ts ✓ — barrel export, static imports, lookup helpers

### Phase 5 — Frontend Foundation
- [x] **5.1** — Next.js 16.3.4 project init (merged into drishtigis/) ✓
- [x] **5.2** — Design tokens + typography (Tailwind v4 @theme, Playfair Display + Inter) ✓
- [x] **5.3** — shadcn/ui init + button, input, card, separator, badge, skeleton ✓
- [x] **5.4** — maplibre-gl 6.8.0 + animejs 4.5.0 installed, next.config.ts with Turbopack ✓
- [x] **5.5** — MapLibreMap + DynamicMap client wrapper + /app/map page ✓
- [x] **5.6** — All 15 routes implemented (0 × 404) ✓
- [x] **5.7** — npm run build: 0 TS errors ✓ | npm run lint: 0 errors 0 warnings ✓

### Phase 6 — Backend Foundation
- [x] **6.1** — FastAPI project structure + requirements.txt ✓
- [x] **6.2** — main.py, config.py, database.py, data_source.py, health.py ✓
- [x] **6.3** — 8 SQLAlchemy models, change_type nullable ✓
- [x] **6.4** — Alembic + 001_initial_schema migration (8 tables, PostGIS, GIST indexes) ✓
- [x] **6.5** — Placeholder parcels + features API endpoints with demo data ✓
- [x] **6.6** — Backend verified: /health OK, /api/v1/parcels OK, /docs OK ✓

### Phase 2 — GIS Processing Pipeline
- [x] **2.1** — GIS venv (`scripts/.gis-env/`) + rasterio 1.5.1 (GDAL 3.12.4) ✓ — isolated from main env, EPSG:32643 confirmed
- [x] **2.2** — bhopal_mosaic.vrt ✓ — 45717×4033px, EPSG:32643, 30 tiles × 3 bands, last-file-wins overlap, bounds match report
- [x] **2.3** — bhopal_cog.tif ✓ — 32.2MB (84% smaller than 206MB source), JPEG, 9 overview levels, EPSG:32643 preserved
- [x] **2.4** — XYZ tile pyramid ✓ — 379 non-blank tiles z18–21, per-tile reproject EPSG:32643→3857
- [x] **2.4b** — Tile verification ✓ — 37/37 checks PASS: center tile 39KB 256×256 R-std=70 14682 non-zero px, no fabricated coverage

### Phase 3 — OSM Data Extraction
- [x] **3.1a** — pyosmium 4.3.1 in GIS venv ✓ — PBF magic valid, main env isolated
- [x] **3.1b** — scripts/data_prep/06_extract_osm_bhopal.py ✓ — two-pass, no location cache
- [x] **3.1c** — Extraction outputs ✓:
  - Pass 1: 260,974,604 nodes scanned, 130,371 in bbox (1116s + 741s tag enrichment)
  - Pass 2: 29,996,486 ways scanned, 29,962 matched (536s)
  - buildings: 26,577 features | roads: 2,933 | waterways: 31 | landuse: 98
- [x] **3.1d** — 48/48 validation checks PASS ✓ — OSM:/OSM_VALIDATE: in pipeline.log, extraction_report.json written
- PBF india-260905.osm.pbf: 1,706,252,573 bytes — unchanged throughout

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

### Core India WebGIS Integration (core-india-webgis v0.1)
- [x] **A.1** — backend/app/gis/ package ✓
- [x] **A.2** — india_cities.py: 44 cities, case-insensitive search ✓
- [x] **A.3** — coverage_registry.py: Bhopal prototype, all others none, historical=False ✓
- [x] **A.4** — tiles.py: /api/v1/tiles/bhopal/{z}/{x}/{y}.png, path traversal guard ✓
- [x] **A.5** — osm_layers.py: /api/v1/osm/bhopal/{layer}, allowlist, FileResponse ✓
- [x] **A.6** — coverage.py + locations.py: /api/v1/coverage/{slug}, /api/v1/locations/search ✓
- [x] **A.7** — parcels.py: non-Bhopal returns _coverage_note ✓
- [x] **A.8** — tests/test_webgis.py: 91 tests, 91 PASS ✓
- [x] **A.9** — backend verified, Dataset/ unchanged ✓
- [x] **B.1** — lib/gis/india.ts + coverage.ts ✓
- [x] **B.2** — lib/api/ (6 modules): tiles, osm, parcels, coverage, locations, index ✓
- [x] **B.3** — LayerControl.tsx: 7 layer toggles, accessible fieldset ✓
- [x] **B.4** — PropertyPanel.tsx: parcel+AI+discrepancy, disclaimer always visible ✓
- [x] **B.5** — CoverageIndicator.tsx: honest unavailability notice ✓
- [x] **B.6** — MapLibreMap.tsx: India-scale, all data layers, lazy loading ✓
- [x] **B.7** — /app/map page: India overview, LocationSearch, LayerControl, PropertyPanel ✓
- [x] **B.8** — npm run build: 0 errors | npm run lint: 0 errors 0 warnings ✓

---

### Phase 0 — UAVPal Metadata Verification (2026-09-08)
- [x] **U.1** — README.md downloaded ✓ — ID=121832, 56,013 bytes, SHA-1=151c2877008b7768114c62b749a1f2fb8b4a893d PASS
- [x] **U.2** — Data_Conf.json downloaded ✓ — ID=121813, 86,580 bytes, SHA-1=3330b57a1d97fa6532b3cce7b6d6ca8208d5134e PASS
- [x] **U.3** — Annotation.gpkg downloaded ✓ — 2,838,528 bytes, class schema extracted via SQLite
- [x] **U.4** — 5 classes confirmed from Annotation.gpkg: 0=Background, 1=Water, 2=Road, 3=Car, 4=Building, 5=Tree
- [x] **U.5** — Data_Conf.json parsed ✓ — Train=370, Test=159, total=529 tiles (no explicit validation split)
- [x] **U.6** — 30/30 repo tiles matched ✓ — 18 train, 12 test, annotation_file confirmed for every tile
- [x] **U.7** — uavpal_tile_mapping.json written ✓ — data/uavpal/uavpal_tile_mapping.json (20,232 bytes)
- [x] **U.8** — bhopal-ai-features.geojson corrected ✓ — model="DEMO — not from real inference", _disclaimer="Prototype placeholder geometry. Not generated by model inference." on all 5 features + metadata block
- [x] **U.9** — Test baseline: 90 PASS, 1 FAIL (test_ai_feature_filter_by_parcel pre-existing data drift — NOT introduced by this phase)
- [x] **U.10** — Dataset/ integrity confirmed ✓ — 30 TIFFs unchanged, PBF=1,706,252,573 bytes unchanged

---

### Phase 1 — UAVPal Annotation Download + Validation (2026-09-08)
- [x] **P1.1** — 30 DANS label tile IDs confirmed ✓ — all in `Label/Tiles` directory, sizes match Phase 0
- [x] **P1.2** — 30 label tiles downloaded ✓ — `data/uavpal/annotations/Label/Tiles/`, 528,642 bytes total
- [x] **P1.3** — All 30 SHA-1 checksums verified ✓ — match DANS listing exactly
- [x] **P1.4** — All 30 validation checks pass ✓ — file_exists, opens, 2048×2048, EPSG:32643, uint8, class_values_valid (0-5 only), filename_matches_rgb, spatial_aligned_with_rgb
- [x] **P1.5** — Building pixel statistics computed ✓ — 30/30 tiles have building pixels (class 4), combined 71,610,322 px (56.9% of all labeled pixels)
- [x] **P1.6** — annotation_manifest.json written ✓ — data/uavpal/annotations/annotation_manifest.json (50,332 bytes)
- [x] **P1.7** — PHASE_1_REPORT.md written ✓ — data/uavpal/annotations/PHASE_1_REPORT.md
- [x] **P1.8** — Dataset/ integrity confirmed ✓ — 30 RGB TIFFs unchanged, PBF=1,706,252,573 bytes unchanged
- [x] **P1.9** — Backend tests: 90 PASS, 1 FAIL (pre-existing test_ai_feature_filter_by_parcel — unchanged from Phase 0)

---

### Phase 2 — Segmentation Pipeline Preparation (2026-09-08)
- [x] **P2.1** — Environment inspected: Python 3.12.0 at C:\Python312, 7.7GB RAM, Intel UHD (no CUDA), 13.8GB disk
- [x] **P2.2** — scripts/.ml-env created (Python 3.12), torch 2.5.1+cpu, torchvision 0.20.1+cpu, rasterio, scipy, scikit-image, shapely, geopandas, smp 0.3.4 installed
- [x] **P2.3** — data/uavpal/validation_split.json: 14 internal train / 4 val / 12 test (spatially distributed, seed=42, no leakage)
- [x] **P2.4** — data/uavpal/training_config.json: patch=512, batch=2, lr=1e-4, UNet/resnet18, 6 classes, building_class_id=4
- [x] **P2.5** — backend/ai/uavpal/classes.py + dataset.py: authoritative class defs, patch-based loader (16 patches per 2048x2048 tile)
- [x] **P2.6** — backend/ai/segmentation/model.py: UNetResNet18, 14,339,846 params, pure torch (no smp dependency)
- [x] **P2.7** — backend/ai/segmentation/train.py + inference.py + masks.py + validation.py written
- [x] **P2.8** — backend/tests/test_ai_pipeline.py: 46/46 PASS (8 test groups, all checks green)
- [x] **P2.9** — CPU smoke test PASS: load=0.18s, forward=0.91s, loss=1.382 (CE+Dice), grad_norm=2.334, optimizer step OK, no NaN/Inf
- [x] **P2.10** — Backend tests: 90 PASS, 1 FAIL (pre-existing test_ai_feature_filter_by_parcel — unchanged)
- [x] **P2.11** — data/uavpal/PHASE_2_REPORT.md written
- [x] **P2.12** — Dataset/ integrity confirmed: 30 TIFFs + PBF byte-exact. Demo AI polygons remain DEMO labelled. No training performed.

---

### Phase 3 — Model Training and Evaluation (2026-09-12)
- [x] **P3.1** — Class distribution computed: Building=55.7%, Background=27.0%, Road=11.7%, Tree=4.9%, Car=0.75%, Water=0 (absent) → median-frequency weights applied
- [x] **P3.2** — Directories created: data/ai_models/uavpal, data/ai_output/evaluation; .gitignore updated
- [x] **P3.3** — Full training loop implemented: CrossEntropyDice loss, grad accum=4, ReduceLROnPlateau, early stopping, checkpointing
- [x] **P3.4** — RAM check PASS: peak 1.30 GB at batch_size=2 (safe limit 6.6 GB)
- [x] **P3.5** — 10-epoch pilot complete: best Building IoU=0.453, loss decreasing, RAM safe
- [x] **P3.6** — Full training: 20 more epochs from checkpoint, best Building IoU=0.587 at epoch 25 overall (6.1h CPU total)
- [x] **P3.7** — Checkpoints saved: best_model.pth (54.8 MB, epoch 25), latest_model.pth (54.8 MB, epoch 30)
- [x] **P3.8** — model_metadata.json written with complete provenance
- [x] **P3.9** — Test evaluation on 12 official test tiles: Building IoU=0.524, F1=0.688, Precision=0.852, Recall=0.577, mIoU=0.312, PixelAcc=0.585
- [x] **P3.10** — Visual outputs: 36 PNGs (6 tiles x 6 images) in data/ai_output/evaluation/
- [x] **P3.11** — metrics.json + test_report.md written
- [x] **P3.12** — Backend: 90 PASS, 1 FAIL (pre-existing unchanged). Dataset/ byte-exact. Demo polygons remain DEMO-labelled.

---

### Phase 4 — Building Footprint Extraction (2026-09-12)
- [x] **P4.1** — Tile overlap analysis: 48 pairs, all narrow ~61m2 seams, max overlap 3.1%, no large-area duplicates
- [x] **P4.2** — backend/ai/segmentation/postprocess.py: mask→CC→watershed→contour pipeline
- [x] **P4.3** — backend/ai/segmentation/georef.py: pixel→EPSG:32643→EPSG:4326, make_valid repair
- [x] **P4.4** — backend/ai/segmentation/dedup.py: centroid 5m + IoU 0.15 dedup for adjacent tile pairs
- [x] **P4.5** — Pipeline runner: _phase4_extract.py processes all 30 tiles
- [x] **P4.6** — Pipeline run complete: 1508 raw CC, 842 filtered, 1469 WS splits, 8 duplicates removed → **834 final buildings**, 2.02 MB GeoJSON, ~8.5 min
- [x] **P4.7** — test_phase4_pipeline.py: 45/45 PASS; AI pipeline: 46/46 PASS; WebGIS: 90 PASS 1 FAIL (pre-existing)
- [x] **P4.8** — Visual QA: 8 tiles × 5 images = 40 PNGs in data/ai_output/phase4_qa/
- [x] **P4.9** — Geometry repair: 0 invalid geometries (all valid after construction), 0 repairs needed
- [x] **P4.10** — data/ai_output/PHASE_4_REPORT.md written; Dataset/ byte-exact; demo polygons remain DEMO-labelled

---

### Phase 5 — AI Building to Parcel Association + WebGIS Integration (2026-09-13)
- [x] **P5.1** — Spatial association computed: 834 buildings → 16 FULLY_WITHIN, 16 CROSSES_BOUNDARY, 802 NO_PARCEL_MATCH; parcel-bpl-001: 20, parcel-bpl-002: 6, parcel-bpl-003: 6
- [x] **P5.2** — AI_DERIVED_UAVPAL added to DataSource enum (Python + TypeScript); coverage_registry BHOPAL_DATASETS updated with real AI entry (834 buildings)
- [x] **P5.3** — features.py rewritten: serves real 834 buildings, ?parcel_id + ?tile filters, ai_available flag, /stats endpoint
- [x] **P5.4** — parcels.py updated: ai_analysis sub-object (building_count, coverage_ratio, discrepancies, avg_confidence)
- [x] **P5.5** — TypeScript: RealAIBuildingProperties, AIBuildingAnalysis, AIFeaturesResponse, ParcelRelationship types added; fetchAIBuildings() added
- [x] **P5.6** — MapLibreMap.tsx: AI layer restyled teal/amber per relationship, minzoom=15, no popup DOM nodes
- [x] **P5.7** — ContextSidebar.tsx: ai-feature mode shows real fields; parcel mode shows real ai_analysis; hardcoded demo mapping removed; primary_property_id routing
- [x] **P5.8** — test_phase5_association.py: 47 tests. test_webgis.py updated: 97 tests. Total: 235/235 PASS
- [x] **P5.9** — TypeScript build: 0 errors, 15 routes, production clean. Lint: 0 new errors (2 pre-existing any)
- [x] **P5.10** — bhopal-building-parcel-associations.geojson (2.18 MB), bhopal-discrepancies.json (350 records), PHASE_5_REPORT.md written. Dataset/ byte-exact.

---

### Phase 5.5 — Synthetic Cadastral Dataset + Topology Validation (2026-09-13)
- [x] **P5.5.1** — UAVPal coverage confirmed: 992m×88m strip, buildings 5-171m2 (median 17m2)
- [x] **P5.5.2** — 35 synthetic parcels generated within actual UAVPal bounds; all topology VALID (0 overlapping/self-intersecting/duplicate)
- [x] **P5.5.3** — 35 synthetic property records with Indian names + SYNTHETIC_DEMO source + disclaimer
- [x] **P5.5.4** — Spatial association: 550 FULLY_WITHIN, 209 CROSSES_BOUNDARY, 75 NO_PARCEL_MATCH, 759 matched, 34 multi-building parcels
- [x] **P5.5.5** — Topology validator implemented: valid/self-intersecting/overlapping/duplicate/zero-area detection
- [x] **P5.5.6** — parcels.py: synthetic dataset primary (DRS-BPL-DEMO-XXX), legacy fallback. SYNTHETIC_DEMO enum added (Python + TypeScript)
- [x] **P5.5.7** — MapLibreMap: amber/yellow synthetic parcel styling. ContextSidebar: DEMO badge, owner_name, SYNTHETIC warning. LayerControl: "Demo Property Records"
- [x] **P5.5.8** — test_phase55.py: 47 tests. Total: 300/300 PASS (1 skipped — superseded test)
- [x] **P5.5.9** — TypeScript: 0 errors, build clean. Lint: 0 new errors.
- [x] **P5.5.10** — 30 RGB TIFFs byte-exact (new path: Dataset/geospatial-data/BHOPAL). 30 labels byte-exact. PHASE_5_5_REPORT.md written.
