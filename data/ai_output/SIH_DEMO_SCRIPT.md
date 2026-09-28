# DRISHTIGIS — SIH FINAL DEMONSTRATION SCRIPT
## 3-to-5 Minute Presentation & Live Demo Script for Evaluators

**Target Problem**: SIH26012 — AI-Based Automated Urban Parcel Mapping and Cadastral Feature Extraction System using Drone Imagery.  
**Product Positioning**: *"DrishtiGIS is a Pan-India AI-powered urban parcel mapping and cadastral intelligence platform, currently validated using a Bhopal demonstration region."*

---

### Timed Presentation Breakdown

```
00:00 ─── 00:30 │ PROBLEM & CONTEXT
00:30 ─── 01:00 │ DRISHTIGIS SOLUTION & ARCHITECTURE
01:00 ─── 02:00 │ LIVE MAP DEMO: AI FEATURE EXTRACTION & GIS PARCELS
02:00 ─── 02:45 │ DISCREPANCY DETECTION & HUMAN-IN-THE-LOOP REVIEW
02:45 ─── 03:30 │ GROUNDED GEOSPATIAL AI ASSISTANT & PROVENANCE
03:30 ─── 04:00 │ GOVERNANCE, AUDIT TRAIL & GIS EXPORTS
04:00 ─── 05:00 │ NATIONWIDE SCALABILITY, IMPACT & FUTURE INTEGRATIONS
```

---

### Step-by-Step Script & Visual Walkthrough

#### 00:00 – 00:30 | Problem Statement
> **Presenter Speaking Script:**  
> "Respected judges, urban land governance across India faces a critical challenge: traditional manual land surveying cannot keep pace with rapid urban development. High-resolution drone imagery provides massive spatial clarity, but manually extracting building footprints, verifying parcel boundaries, and detecting spatial discrepancies takes months. DrishtiGIS solves this by combining deep-learning computer vision, GIS polygonization, human-in-the-loop review workflows, and grounded geospatial AI assistant intelligence."

**Screen View:** Landing page (`/`) showing the 4 core pillars: AI Feature Extraction, GIS Spatial Reasoning, Human Review, and Governed Security.

---

#### 00:30 – 01:00 | Solution & Architecture Overview
> **Presenter Speaking Script:**  
> "DrishtiGIS is built as a Pan-India scalable platform. Our architecture ingests georeferenced orthomosaics, runs U-Net with ResNet18 deep learning segmentation for building extraction, converts raster predictions into valid OGC vector polygons, performs spatial overlay against cadastral parcel boundaries, and flags physical discrepancies for surveyor review. Today, our working pipeline is validated using 30 high-resolution UAV drone tiles and synthetic prototype cadastral data over a Bhopal demonstration region."

**Screen View:** Landing page pipeline visual (`Aerial Imagery → AI Segmentation → Feature Vectorization → Parcel Association → Discrepancy Analysis → Human Review → Field Verification → GIS Export`).

---

#### 01:00 – 02:00 | Live Map Demo: AI Feature Extraction & Vector Layers
> **Presenter Speaking Script:**  
> "Let's enter the Geospatial Workspace. On the map, we can view 834 AI-derived building footprints extracted automatically at 0.02-meter resolution, layered over 35 synthetic demonstration parcels. Notice our generic search bar — we can search by Property ID, Plot Number, Survey Number, or House Number. When I click on parcel `DRS-BPL-DEMO-014`, the Property Panel displays recorded vs detected building area, observed land use, nearest road access, and clear dataset provenance. Note our explicit disclaimer: *Synthetic prototype data — not an official land record.*"

**Screen View:** `/app/map` view with UAV imagery base, cyan building vector overlays, property panel open for `DRS-BPL-DEMO-014`.

---

#### 02:00 – 02:45 | Discrepancy Detection & Human-in-the-Loop Review
> **Presenter Speaking Script:**  
> "AI alone should never make legal determinations. In parcel `DRS-BPL-DEMO-014`, our spatial engine detects a `CROSSES_BOUNDARY` discrepancy — an AI building footprint extending past the synthetic parcel polygon. Rather than declaring an illegality, DrishtiGIS flags it as *'Boundary relationship requires review'*. In the Review Queue (`/app/review`), a certified surveyor can inspect the original immutable AI geometry, draw a corrected boundary, attach field verification evidence (such as RTK/CORS or field photos), and submit it for reviewer approval with a complete append-only audit log."

**Screen View:** `/app/map` discrepancy highlight and `/app/review` queue interface showing surveyor review & field verification options.

---

#### 02:45 – 03:30 | Grounded Geospatial AI Assistant & Provenance
> **Presenter Speaking Script:**  
> "For non-GIS specialists, DrishtiGIS includes a Grounded AI Assistant (`/app/assistant`). When asked: *'Why is parcel DRS-BPL-DEMO-014 under review?'*, the assistant does not guess. It calls our backend GIS tool registry, retrieves exact spatial metrics, and responds with strict provenance detailing the source dataset (`UAVPal`), region (`Bhopal, Madhya Pradesh`), and feature ID. It strictly adheres to safety policies, avoiding legal hallucinations."

**Screen View:** `/app/assistant` interface executing `get_discrepancy_details` tool call and rendering structured response with provenance cards.

---

#### 03:30 – 04:00 | Governance, Audit Trail & GIS Exports
> **Presenter Speaking Script:**  
> "DrishtiGIS enforces multi-tenant Role-Based Access Control (Public, Surveyor, Reviewer, Admin) with region-scoped dataset visibility and security audit logging. Once verified, spatial data can be exported directly into GIS-ready formats including GeoJSON, GeoPackage, PDF reports, and complete Evidence ZIP Packages containing complete spatial metadata."

**Screen View:** `/app/exports` page demonstrating GeoJSON / GeoPackage / Evidence ZIP package generation.

---

#### 04:00 – 05:00 | Scalability, Impact & Future Integration
> **Presenter Speaking Script:**  
> "DrishtiGIS provides municipal bodies and state survey departments with an automated, auditable, and scalable AI mapping engine. Thank you, and we welcome your questions."

---

### Summary of Implementation Scope

| Feature Area | Status in DrishtiGIS | Notes |
| :--- | :--- | :--- |
| **30 UAV Drone Tiles & DSM Ingestion** | `IMPLEMENTED` | Real 0.02m UAVPal dataset for Bhopal |
| **U-Net + ResNet18 AI Building Footprints** | `IMPLEMENTED` | 834 vectorized building footprints |
| **35 Synthetic Cadastral Parcels** | `IMPLEMENTED` | Prototype demonstration cadastral layer |
| **Spatial Discrepancy Engine** | `IMPLEMENTED` | Detects `CROSSES_BOUNDARY`, area mismatch |
| **Surveyor Review & Field Verification** | `IMPLEMENTED` | Immutable original AI geom + surveyor edit + GNSS/RTK notes |
| **Grounded AI Assistant with Tool Calling** | `IMPLEMENTED` | Function calling on read-only GIS tool registry |
| **Role-Based Access Control & Audit Log** | `IMPLEMENTED` | JWT, PBKDF2 hashing, 4 roles, append-only logs |
| **GeoJSON / GeoPackage / Evidence Package Export** | `IMPLEMENTED` | Production GIS exports with metadata |
| **Real State SWAMITVA API Ingestion** | `FUTURE` | Planned production integration |
| **Real Second-Epoch UAV Raster Comparison** | `FUTURE` | Framework implemented with test fixtures |
