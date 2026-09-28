# DrishtiGIS — AI-Based Urban Parcel Mapping & Cadastral Feature Intelligence
**Problem Statement SIH26012 — Smart India Hackathon**  
*Ministry of Rural Development / Department of Land Resources*

---

## 📌 Executive Overview

**DrishtiGIS** is a Pan-India-ready geospatial AI platform for automated urban parcel mapping, cadastral feature extraction, and human-in-the-loop spatial verification.

> **Current Demonstration Region**: The current validated demonstration uses **Bhopal, Madhya Pradesh**. Its parcel/property layer is synthetic prototype data and is not an official land record.

```
DRONE IMAGERY (UAV RGB GeoTIFFs)
               ↓
AI FEATURE EXTRACTION (U-Net + ResNet18 Segmentation Engine)
               ↓
GIS TOPOLOGY & CADASTRAL INTELLIGENCE (Spatial Relationship Engine)
               ↓
SURVEYOR REVIEW & GROUND-TRUTHING (Immutable Audit Trail & Verifications)
               ↓
MULTI-USER GOVERNANCE & RBAC (Role-Scoped Scoping & Region Governance)
               ↓
GIS EXPORTS & GROUNDED AI ASSISTANT (GeoPackage, GeoJSON, LLM Tool Calling)
```

---

## 🎯 Key Features & Capabilities

1. **AI Building Footprint Segmentation**: Deep Learning pipeline (U-Net + ResNet18) extracting 834 high-precision building boundaries from 30 UAV GeoTIFF tiles.
2. **Cadastral Spatial Relationship Engine**: Calculates topological intersections (`FULLY_WITHIN`, `CROSSES_BOUNDARY`, `NO_PARCEL_MATCH`, `MULTIPLE_BUILDINGS`) between building footprints and parcel boundaries.
3. **Road Corridor & Land-Use Analytics**: Integrates 2,933 OSM road line segments and 98 land-use polygons to evaluate property accessibility and urban land patterns.
4. **Surveyor Review & Field Verification Queue**: WebGIS QA queue for geometry editing, topology validation, GNSS field observations, and reviewer approvals with append-only audit logging.
5. **Grounded Geospatial AI Assistant**: Natural language interface backed by 13 read-only GIS tools with deterministic fallback engines and provenance tracking.
6. **Authentication & Data Governance**: Token-based authentication, PBKDF2 password hashing, RBAC permissions (`PUBLIC`, `SURVEYOR`, `REVIEWER`, `ADMIN`), and Pan-India regional scoping (`India` &rarr; `State` &rarr; `City` &rarr; `Region`).
7. **GIS-Ready Export Center**: Generates standardized OGC GeoPackage (`.gpkg`), GeoJSON (`.geojson`), Evidence Packages (`.zip`), and dynamic intelligence dossiers (`.pdf`/`.json`).

---

## 👥 SIH Evaluator Demo Accounts

Pre-configured test accounts for evaluation:

| Role | Email | Password | Access Jurisdiction |
| :--- | :--- | :--- | :--- |
| **`PUBLIC`** | `demo-public@drishtigis.in` | `Public123!` | Public map layers & reports |
| **`SURVEYOR`** | `demo-surveyor@drishtigis.in` | `Surveyor123!` | `bhopal_mp` (Bhopal, MP) |
| **`REVIEWER`** | `demo-reviewer@drishtigis.in` | `Reviewer123!` | `bhopal_mp` (Bhopal, MP) |
| **`ADMIN`** | `demo-admin@drishtigis.in` | `Admin123!` | Global Jurisdiction (`*`) |

---

## 🎬 Recommended 3-5 Minute SIH Evaluator Walkthrough

1. **Landing & Access**: Open [`http://localhost:3000`](http://localhost:3000) and click **Get Started** or **Sign In**.
2. **City & Region Scope**: Select **Bhopal** (Primary Demonstration Region) or query any Indian city via **Location Search**.
3. **WebGIS Exploration**: Toggle `Buildings (AI)`, `Parcels (Demo)`, `Roads`, `Land Use`, and `Discrepancies` in the **Layers Panel**.
4. **Property Context**: Click any parcel or building footprint to view calculated spatial relationships, road accessibility, and confidence metrics in the **Context Sidebar**.
5. **Surveyor Review Queue**: Navigate to `/app/review` to inspect discrepancy boundaries, edit geometry with real-time topology validation, and record GNSS field observations.
6. **Grounded AI Assistant**: Navigate to `/app/assistant` or ask: *"What is the road access for parcel DRS-BPL-00101?"* to view tool execution logs and provenance.
7. **GIS Export Center**: Navigate to `/app/exports` to download GeoPackage and Evidence Package ZIP archives with preserved disclaimers.

---

## 🛡️ Data Provenance & Classifications

Every feature rendered in the WebGIS canvas or exported via API carries explicit provenance metadata:

- **`AI_DERIVED_UAVPAL`**: 834 AI building footprints extracted from 30 UAV GeoTIFF aerial tiles.
- **`SYNTHETIC_DEMO`**: 35 demonstration cadastral parcels carrying disclaimer *"Synthetic prototype data — not an official land record."*
- **`REFERENCE_GIS`**: 2,933 road segments and 98 land-use polygons from OpenStreetMap.
- **`REVIEWED_AI_GEOMETRY`**: Geometry modified during surveyor QA review.
- **`FIELD_VERIFIED`**: Ground-truthing GNSS observation records.

---

## 🛠️ Local Development & Deployment

### Backend Setup (FastAPI)
```bash
# Activate virtual environment
scripts\.ml-env\Scripts\activate

# Set PYTHONPATH to locate both backend and root app modules
# PowerShell:
$env:PYTHONPATH=".;backend"

# Run backend API server
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend Setup (Next.js 16)
```bash
# Navigate to frontend directory
cd drishtigis

# Run development server
npm run dev
```

### Run Test Suite
```bash
# Run 376+ automated backend unit & integration tests
scripts\.ml-env\Scripts\python.exe -m pytest backend/tests/
```

### Run Production Build
```bash
cd drishtigis
npm run build
```

---

## 📊 Feature Classification Status

### Implemented Capabilities (`IMPLEMENTED`)
- UAV Aerial Raster Tile Pipeline & COG Tiling
- U-Net + ResNet18 AI Building Segmentation
- Vector Polygon Topology Validation & Relationship Recomputation
- Surveyor Review Queue & Ground-Truthing Field Observations
- Grounded AI Assistant with 13 GIS Tool Execution Engine
- RBAC, JWT Authentication, and Security Audit Logging
- GeoJSON & GeoPackage Export Engine
- Next.js 16 WebGIS Workspace

### Future Enhancements (`PLANNED / FUTURE`)
- Integration with live State Land Records API gateways (e.g. Bhulekh APIs)
- Real multi-epoch drone imagery acquisition for temporal change detection
- Direct bluetooth GNSS hardware integration for field survey tablets
