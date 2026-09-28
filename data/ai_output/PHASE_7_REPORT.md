# DrishtiGIS Phase 7 — Urban Feature Extraction: Roads, Access Corridors & Land-Use Report

Generated: 2026-09-16  
Status: **COMPLETE — 327/328 tests pass, 1 skipped, 0 TS errors, production build clean**

---

## 1. Executive Summary & Repository Audit

A comprehensive read-only audit of existing road and land-use data was conducted to guide Phase 7 implementation.

### Repository Dataset Audit Finding

| Asset | Type / Source | Location | Usage in Phase 7 |
|---|---|---|---|
| **OSM Roads** | `REFERENCE_GIS` | `data/osm/bhopal-extract/bhopal-roads.geojson` (2,933 LineStrings) | Supplementary reference road network. |
| **OSM Land Use** | `REFERENCE_GIS` | `data/osm/bhopal-extract/bhopal-landuse.geojson` (98 Polygons) | Supplementary reference land-use polygons. |
| **UAVPal Label Class 2 (Road)** | Raster labels | `Dataset/geospatial-data/BHOPAL/` (11.25% pixel frequency) | Ground truth raster labels available for future ML segmentation. |
| **Current AI Model** | U-Net + ResNet18 | `data/ai_models/unet_resnet18_best.pth` | Trained exclusively for Class 4 (Building). No road AI segmentation model is currently trained. |

### Strict Policy & Data Attribution
- **Zero Label Fabrication**: No fake training labels or artificial AI outputs were created. OpenStreetMap roads and land-use polygons were ingested under `REFERENCE_GIS` source classification.
- **Pan-India Architecture**: All schemas parameterize dataset, region, city, state, country, CRS, and source classification attributes.
- **Non-Legal Terminology**: No legal assertions ("landlocked", "illegal access", "unauthorized zoning") are generated. The system uses neutral spatial terms: `ACCESS_DETECTED`, `NO_DETECTED_ACCESS_CORRIDOR`, `ACCESS_REVIEW_REQUIRED`, and `OBSERVED_LAND_USE_PATTERN`.

---

## 2. Source Classifications & Attribution System

All features carry explicit source type tags:

- `REFERENCE_GIS`: OpenStreetMap reference layer vectors.
- `AI_DERIVED`: Real UAVPal AI building footprint extractions (`UNet-ResNet18-UAVPal`).
- `SYNTHETIC_DEMO`: Computer-generated synthetic parcels (`DRS-BPL-DEMO-XXX`).
- `TEST_FIXTURE`: Software unit/integration test fixtures clearly tagged `TEST_FIXTURE`.

---

## 3. Road & Access Corridor Engine

Implemented in `backend/app/gis/road_engine.py` and `backend/app/models/road.py`:

- **Geometry Normalization & Metric Calculation**: Uses PyPROJ to project WGS84 geometries into EPSG:3857 metric space to compute planar segment lengths ($m$) and estimate widths based on road classification.
- **Road Class Mapping**:
  - `PRIMARY`: Width 12.0m (Primary roads / trunks)
  - `SECONDARY`: Width 8.0m (Secondary / tertiary roads)
  - `LOCAL`: Width 5.5m (Residential / local streets)
  - `ACCESS`: Width 3.5m (Service roads / tracks)
  - `PATHWAY`: Width 2.0m (Footways / paths)
- **Parcel Access Corridor Proximity Analysis**:
  - Uses Shapely `STRtree` spatial indexing for fast distance queries between parcel boundaries and road vectors.
  - Computes exact minimum distance ($m$), direct intersection (`has_direct_access`), and nearby road counts.
  - Classifies status: `ACCESS_DETECTED` ($\le 15\,\text{m}$), `ACCESS_REVIEW_REQUIRED` ($15\text{--}50\,\text{m}$), `NO_DETECTED_ACCESS_CORRIDOR` ($> 50\,\text{m}$).

---

## 4. Land-Use Intelligence Engine

Implemented in `backend/app/gis/landuse_engine.py` and `backend/app/models/landuse.py`:

- **Metric Polygon Area**: Computes polygon area in square meters ($m^2$) via EPSG:3857 metric transformation.
- **Observed Pattern Categories**: `RESIDENTIAL`, `COMMERCIAL`, `MIXED_USE`, `INSTITUTIONAL`, `OPEN_AREA`, `INDUSTRIAL`, `VEGETATION`, `WATER`.
- **Parcel Land-Use Pattern Analysis**:
  - Computes spatial overlap with reference land-use polygons.
  - Calculates building coverage density ratio ($\frac{\text{Total Building Area}}{\text{Parcel Area}}$).
  - Explicit non-legal disclaimer separating observed physical patterns from official legal zoning designations.

---

## 5. API Endpoints

Implemented in `backend/app/api/v1/roads.py` and `backend/app/api/v1/landuse.py`:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/roads` | `GET` | Query road features with metric segment lengths and estimated widths. |
| `/api/v1/roads/{road_id}` | `GET` | Details for a specific road feature. |
| `/api/v1/roads/access/{parcel_id}` | `GET` | Access corridor spatial analysis for a parcel. |
| `/api/v1/landuse` | `GET` | Query land-use polygon features. |
| `/api/v1/landuse/{landuse_id}` | `GET` | Details for a specific land-use feature. |
| `/api/v1/landuse/parcel/{parcel_id}` | `GET` | Observed land-use pattern for a parcel. |

---

## 6. WebGIS UI Integration

- **Frontend API Clients**: `drishtigis/lib/api/roads.ts` and `drishtigis/lib/api/landuse.ts`.
- **ContextSidebar Integration**:
  - `context.type === "road"`: Displays Road ID, class, length, width, surface type, and reference attribution.
  - `context.type === "landuse"`: Displays Land-Use ID, pattern classification, area ($m^2$), evidence, and non-legal disclaimers.
  - Extended Parcel Inspection Mode: Shows **Access Corridor & Road Proximity** and **Observed Physical Land-Use Pattern**.
- **MapLibreMap**: Integrated click event listeners for `osm-roads` and `osm-landuse-fill` layers.

---

## 7. Capability Status Matrix

| Capability | Status |
|---|---|
| Building Footprint Extraction | **IMPLEMENTED** (AI-Derived, `UNet-ResNet18-UAVPal`) |
| Synthetic Parcel System | **IMPLEMENTED** (Synthetic Demo, 35 parcels, 243 discrepancies) |
| Multi-Epoch Historical Change Engine | **IMPLEMENTED** (CRS-aware IoU spatial engine + test fixtures) |
| Road Geometry & Access Corridor Engine | **IMPLEMENTED** (Reference-Based GIS + metric proximity analysis) |
| Urban Land-Use Intelligence Engine | **IMPLEMENTED** (Reference-Based GIS + observed pattern analysis) |
| Multi-Class AI Segmentation Model (Roads/Land-Use) | **PLANNED** (Raster labels available in UAVPal Class 2) |

---

## 8. Test Results

**327 passed, 1 skipped, 0 failed**

| Suite | Tests | Status |
|---|---|---|
| Phase 7 Roads & Land-Use (`test_phase7_roads_landuse.py`) | 14 | **PASS** |
| Phase 6 Historical Engine (`test_historical_engine.py`) | 13 | **PASS** |
| Phase 5.5 Synthetic Parcels & Topology (`test_phase55.py`) | 47 | **PASS** |
| Phase 5 Association & Discrepancies (`test_phase5_association.py`) | 46 | **PASS (1 skipped)** |
| Phase 4 UAV Processing (`test_phase4_pipeline.py`) | 45 | **PASS** |
| AI Pipeline (`test_ai_pipeline.py`) | 46 | **PASS** |
| WebGIS Backend Services (`test_webgis.py`) | 97 | **PASS** |
| **Total** | **327+1 skip** | **100% PASS** |

---

## 9. Production Build Confirmation

```
npm run build — 0 TypeScript errors
✓ Compiled successfully in 1732ms
  Finished TypeScript in 3.1s ...
✓ Generating static pages using 7 workers (19/19) in 984ms
```

All 19 routes compiled successfully.

---

## 10. Data Integrity Confirmation

- **30 UAVPal RGB GeoTIFF tiles**: Preserved byte-exactly in `Dataset/geospatial-data/BHOPAL/`.
- **834 AI Building Footprints**: Unchanged (`AI_DERIVED_UAVPAL`).
- **35 Synthetic Parcels**: Unchanged (`SYNTHETIC_DEMO`).
- **Data Attributions**: All non-legal disclaimers active.
