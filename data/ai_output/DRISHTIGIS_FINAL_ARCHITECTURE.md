# DRISHTIGIS — FINAL SYSTEM ARCHITECTURE
## Production Architecture, AI/GIS Processing Pipelines, Security & Governance Framework

### Executive Overview
DrishtiGIS is a Pan-India AI-powered urban parcel mapping and cadastral intelligence platform. It processes high-resolution UAV drone imagery into structured vector features using deep-learning segmentation, evaluates spatial discrepancies against cadastral parcel boundaries, enforces a multi-role human-in-the-loop review workflow, and provides a grounded natural-language geospatial AI assistant interface.

---

### 1. End-to-End System Architecture Diagram

```
                       ┌──────────────────────────────────────────────┐
                       │           UAV / DRONE AERIAL DATA            │
                       │    (30 RGB GeoTIFF Tiles @ 0.0217m Res)      │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │          RASTER INGESTION ENGINE             │
                       │    (GDAL / Rasterio / CRS Reprojection)      │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │          AI FEATURE EXTRACTION               │
                       │   (U-Net + ResNet18 Semantic Segmentation)   │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │        VECTORIZATION & TOPOLOGY ENGINE       │
                       │   (OpenCV Contour Vectorization / Shapely)   │
                       │          [834 AI Building Footprints]        │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │        PARCEL ASSOCIATION & SPATIAL OVERLAY  │
                       │  (Spatial Join vs 35 Synthetic Demo Parcels) │
                       └──────────────────────┬───────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
         ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
         │ ROAD ACCESS ENGINE │    │  LAND-USE OBSERVER │    │ DISCREPANCY ENGINE │
         │ (2,933 OSM Roads)  │    │(98 Land-Use Polys) │    │(CROSSES_BOUNDARY)  │
         └──────────┬─────────┘    └──────────┬─────────┘    └──────────┬─────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │         HUMAN-IN-THE-LOOP REVIEW QUEUE       │
                       │ (Surveyor Edit / Field Verification Evidence)│
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │          GOVERNED EXPORT & WebGIS            │
                       │  (GeoJSON / GeoPackage / PDF / Evidence ZIP) │
                       └──────────────────────────────────────────────┘

                                      PARALLEL SYSTEM:
                       ┌──────────────────────────────────────────────┐
                       │        GROUNDED GEOSPATIAL AI ASSISTANT      │
                       │  (Read-Only GIS Tool Registry & Provenance)  │
                       └──────────────────────────────────────────────┘
```

---

### 2. Deep Learning AI Feature Extraction Pipeline

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  Georeferenced RGB Tile │ ──► │ U-Net + ResNet18 Model  │ ──► │  Binary Segmentation    │
│  (512x512 Window)       │     │ (Building Class)        │     │  Probability Mask       │
└─────────────────────────┘     └─────────────────────────┘     └────────────┬────────────┘
                                                                             │
                                                                             ▼
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│ Valid OGC MultiPolygon  │ ◄── │ Shapely Vector Clean    │ ◄── │ OpenCV Vectorization    │
│ (EPSG:4326 WGS84)       │     │ (Topology Smoothing)    │     │ (Contour Extraction)    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

---

### 3. Spatial Discrepancy & Human Review Engine Architecture

```
                                  ┌───────────────────────────┐
                                  │  AI Building Geometry +   │
                                  │  Cadastral Parcel Polygon │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │ Spatial Intersection Test │
                                  └─────────────┬─────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          │                                           │
                          ▼                                           ▼
            [No Spatial Discrepancy]                     [CROSSES_BOUNDARY / Area Mismatch]
                     │                                                │
                     ▼                                                ▼
         Auto-Assigned "VALIDATED"                   Flagged as "REQUIRES_REVIEW"
                                                                      │
                                                                      ▼
                                                         Surveyor Review Queue (/app/review)
                                                                      │
                                                  ┌───────────────────┴───────────────────┐
                                                  │                                       │
                                                  ▼                                       ▼
                                       [Original AI Geom]                       [Surveyor Geom Edit]
                                          (IMMUTABLE)                           (Saved Separately)
                                                  │                                       │
                                                  └───────────────────┬───────────────────┘
                                                                      │
                                                                      ▼
                                                          Field Verification Evidence
                                                          (GNSS / RTK / Field Photos)
                                                                      │
                                                                      ▼
                                                          Reviewer Approval & Export
```

---

### 4. Security, Authentication & Role-Based Access Control (RBAC)

```
                                      ┌──────────────────────┐
                                      │   User Login Request │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                      ┌──────────────────────┐
                                      │  PBKDF2 Password Check│
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                      ┌──────────────────────┐
                                      │  JWT Token Generation│
                                      └──────────┬───────────┘
                                                 │
                  ┌──────────────────────────────┼──────────────────────────────┐
                  ▼                              ▼                              ▼
        ┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
        │   PUBLIC ROLE    │           │  SURVEYOR ROLE   │           │  REVIEWER ROLE   │
        │ - View Maps      │           │ - Public Access  │           │ - Surveyor Access│
        │ - Query Assistant│           │ - Submit Edits   │           │ - Final Approval │
        │ - Search Parcels │           │ - Field Evidence │           │ - Export Reports │
        └──────────────────┘           └──────────────────┘           └──────────────────┘
                                                 │
                                                 ▼
                                      ┌──────────────────────┐
                                      │  REGION GOVERNANCE   │
                                      │  (bhopal_mp scoping) │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                      ┌──────────────────────┐
                                      │  SECURITY AUDIT LOG  │
                                      │ (Append-Only JSONL)  │
                                      └──────────────────────┘
```

---

### 5. Implemented vs Future Enhancement Architecture Matrix

| Architectural Layer | Implemented Feature Set | Future Production Scope |
| :--- | :--- | :--- |
| **Raster Ingestion** | 30 high-res UAV RGB GeoTIFF tiles (0.0217m) | Automated multi-band satellite (Sentinel/Landsat) ingestion |
| **AI Segmentation** | U-Net + ResNet18 building footprint extraction | Multi-class segmentation (vegetation, water, roads) |
| **Cadastral Layer** | 35 synthetic prototype cadastral parcels | Direct state SWAMITVA & revenue PostGIS API integration |
| **Discrepancy Engine** | `CROSSES_BOUNDARY` & area mismatch spatial join | 3D volumetric building height violation detection |
| **Review Engine** | Immutable AI geometry + surveyor edits + field evidence | Mobile offline survey tablet sync application |
| **AI Assistant** | Grounded read-only tool registry + provenance | Multi-lingual voice interface for field surveyors |
| **Exports** | GeoJSON, GeoPackage, PDF reports, Evidence ZIP packages | National Land Records Modernisation Programme (NLRMP) API sync |
