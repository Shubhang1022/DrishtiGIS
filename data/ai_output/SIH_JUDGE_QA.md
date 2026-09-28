# DRISHTIGIS — SIH JUDGE EVALUATION Q&A
## 20 Technical Q&A Pairs Grounded in Actual Codebase Implementation

---

### Q1: What is innovative about DrishtiGIS?
**Answer:**  
DrishtiGIS bridges the gap between deep-learning computer vision and production WebGIS land governance. Instead of just displaying static rasters, it automatically extracts 834 vector building footprints using U-Net+ResNet18, computes topological spatial relationships against cadastral parcel boundaries, flags spatial discrepancies, provides an immutable human-in-the-loop review workflow, and enables natural language spatial queries via a tool-calling Grounded AI Assistant.

---

### Q2: Why is AI required for urban parcel mapping?
**Answer:**  
Manual digitization of building footprints and urban features from high-resolution drone imagery (0.02m spatial resolution) across entire municipalities requires thousands of human-hours. Deep learning semantic segmentation processes drone orthomosaics in minutes, generating preliminary building footprints that accelerate surveyor mapping by over 80%.

---

### Q3: How are parcel boundaries obtained in this system?
**Answer:**  
In the current validated demonstration, parcel boundaries are represented by 35 synthetic prototype cadastral polygons generated over the Bhopal UAV tile area for demonstration purposes. In production deployment, parcel boundaries are ingested from official state cadastral Shapefiles, GeoJSON, or WFS endpoints (such as SWAMITVA or state revenue databases).

---

### Q4: Can AI determine legal cadastral boundaries independently?
**Answer:**  
No. AI extracts physical spatial features (e.g., observed building footprints, road edges) from aerial imagery. Legal cadastral boundaries require official land record authority, ground-truthing, and statutory approval. DrishtiGIS uses AI to detect *physical spatial discrepancies* for human surveyor review; it strictly refrains from making autonomous legal determinations.

---

### Q5: What happens when the AI model makes a mistake?
**Answer:**  
DrishtiGIS implements an immutable human-in-the-loop review architecture (`/app/review`). If AI misclassifies a building boundary or generates inaccurate geometry, a surveyor can edit the vector vertices in WebGIS. The original AI-derived geometry remains permanently archived and unmodifiable, while the surveyor's corrected geometry is stored in a separate review layer with a complete append-only audit trail.

---

### Q6: How does human verification work?
**Answer:**  
When a spatial discrepancy (e.g., `CROSSES_BOUNDARY` or area mismatch) is flagged, it enters the Surveyor Review Queue. A surveyor inspects the overlay, optionally attaches Ground Truthing evidence (supported types: `ON_SITE`, `GNSS`, `RTK/CORS`, `SURVEY_RECORD`, `FIELD_PHOTO`, `AUTHORITY_RECORD`), updates the geometry status to `SURVEYOR_EDITED`, and submits it for Reviewer approval.

---

### Q7: What dataset was used to build and validate DrishtiGIS?
**Answer:**  
The system is validated using 30 high-resolution UAV RGB GeoTIFF tiles and 30 label masks from the UAVPal dataset (0.0217m spatial resolution, EPSG:32643 / EPSG:4326), along with 2,933 OSM reference road features, 98 OSM land-use polygons, and 35 synthetic demonstration cadastral parcels.

---

### Q8: Why is Bhopal being demonstrated?
**Answer:**  
Bhopal is the validated demonstration region because the high-resolution UAVPal drone imagery dataset and synthetic demonstration cadastral layer are located there. DrishtiGIS's underlying architecture is Pan-India ready and supports dynamic CRS transformations and region-scoped dataset governance.

---

### Q9: How does this scale across India?
**Answer:**  
DrishtiGIS is architected around region-aware datasets, dynamic EPSG projection handling (converting UTM zones EPSG:32643/32644 to WGS84 EPSG:4326), multi-tenant RBAC with region scoping (`bhopal_mp`, etc.), and modular GeoTIFF tile server endpoints. New cities can be onboarded via standard dataset ingestion pipelines without code modifications.

---

### Q10: How will official government cadastral data be integrated in the future?
**Answer:**  
State revenue departments can connect existing GeoServer WFS endpoints, PostGIS spatial databases, or REST APIs directly into DrishtiGIS's regional ingestion service. The system will map official Khasra/Plot attributes while preserving dataset governance rules.

---

### Q11: How does the system handle different Coordinate Reference Systems (CRS)?
**Answer:**  
Raw UAV drone imagery in UTM projections (e.g., EPSG:32643 - WGS 84 / UTM Zone 43N) is dynamically reprojected to EPSG:4326 (WGS84 lat/lon) during raster tile processing and vector polygonization using PyProj and GDAL/Rasterio, ensuring seamless WebGIS rendering in MapLibre GL.

---

### Q12: How does the system handle large datasets?
**Answer:**  
DrishtiGIS uses server-side spatial indexing (R-Tree / RTree via Shapely), MBTiles/GeoTIFF raster tiling, vector tile partitioning, and asynchronous API endpoints in FastAPI, maintaining sub-100ms response times for spatial queries over thousands of features.

---

### Q13: How is AI Assistant hallucination controlled?
**Answer:**  
The DrishtiGIS AI Assistant is strictly *grounded*. It does not generate spatial data from model weights. Instead, user queries trigger deterministic tool calls on a read-only backend GIS tool registry (`get_parcel_history`, `get_discrepancy_details`, `get_parcel_buildings`). Responses strictly include explicit source provenance and disclaimer tags.

---

### Q14: How is sensitive cadastral and spatial data protected?
**Answer:**  
DrishtiGIS enforces multi-tenant Role-Based Access Control (RBAC) with 4 roles (`PUBLIC`, `SURVEYOR`, `REVIEWER`, `ADMIN`), JWT session authentication, PBKDF2 password hashing, region-scoped dataset visibility permissions, and append-only security audit logs.

---

### Q15: What happens if an external LLM API is unavailable?
**Answer:**  
The AI Assistant includes a fallback rule-based geospatial tool executor. If external API keys or LLM services are offline, the system directly executes tool function calls and returns formatted JSON/markdown spatial intelligence data without service disruption.

---

### Q16: What features are currently implemented versus planned for the future?
**Answer:**  
- **IMPLEMENTED:** AI U-Net+ResNet18 segmentation, 834 building footprints, 35 synthetic parcels, spatial discrepancy engine, surveyor review queue, field verification workflow, Grounded AI Assistant, RBAC, GeoJSON/GeoPackage exports.
- **FUTURE:** Direct state SWAMITVA portal WFS integration, multi-temporal real UAV raster ingestion, mobile field survey app synchronization.

---

### Q17: How could a government department deploy DrishtiGIS?
**Answer:**  
DrishtiGIS is containerized and cloud-agnostic. A urban development or survey department can deploy the FastAPI backend and Next.js frontend on state data center infrastructure (NIC cloud / AWS / Azure), connect their PostgreSQL/PostGIS database, and configure region RBAC for municipal surveyors.

---

### Q18: How is DrishtiGIS different from a standard GIS viewer (e.g. QGIS / ArcGIS Web App)?
**Answer:**  
Standard GIS viewers are passive display tools. DrishtiGIS is an end-to-end intelligence engine that automatically extracts features using deep learning, detects topological discrepancies between physical structures and cadastral records, manages a structured multi-role human review workflow, and provides a grounded natural-language AI interface.

---

### Q19: What specific role does drone imagery play in the pipeline?
**Answer:**  
Drone imagery provides ultra-high spatial resolution (0.02m per pixel vs 0.5m-3m for satellite), capturing sharp building boundaries, narrow pathways, and structural overhangs essential for dense urban parcel mapping.

---

### Q20: What happens when second-epoch historical imagery is unavailable?
**Answer:**  
When second temporal UAV rasters are unavailable, the temporal comparison engine transparently displays a disclaimer tag: `TEST FIXTURE — Demonstration temporal analysis. Second temporal UAV raster unavailable.` This preserves system honesty while demonstrating temporal change detection readiness.
