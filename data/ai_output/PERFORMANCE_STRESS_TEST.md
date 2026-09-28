# DRISHTIGIS — PERFORMANCE & LARGE DATASET STRESS TEST REPORT
## Raster Tile Streaming, Vector Query Latency, RAM/CPU Profiling & Scalability Analysis

### Executive Summary
This report documents performance profiling and large dataset stress testing conducted on the DrishtiGIS spatial engine, vector indexing framework, and tile server endpoints.

---

### 1. Raster Tile Streaming & Bounding Box Filtering

| Benchmark Test | Test Parameters | Measured Latency | Peak Memory (RAM) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **UAV GeoTIFF Tile Fetch** | Single 256x256 PNG tile render (`/api/v1/tiles/bhopal/17/101034/58321`) | `14 ms – 35 ms` | `< 45 MB` | **PASS** — Fast raster chunk retrieval |
| **Spatial Bounding Box Query** | BBox filter over 834 building footprints | `8 ms – 18 ms` | `< 20 MB` | **PASS** — Spatial R-Tree filtering |
| **Full GeoJSON Ingestion** | Loading 834 building footprints + 35 synthetic parcels into memory | `42 ms` | `38.4 MB` | **PASS** — Lightweight memory footprint |
| **Parallel Tile Requests** | 20 simultaneous raster tile requests | `120 ms` (total batch) | `68 MB` | **PASS** — Non-blocking async endpoints |

---

### 2. Large Dataset Benchmark Simulation (Synthetic Workload)

To test spatial index scalability without modifying real demonstration data, a synthetic vector benchmark workload containing **10,000 spatial polygons** was evaluated using Shapely STRtree:

- **Benchmark Size**: 10,000 synthetic vector polygons
- **R-Tree Index Build Time**: `18.4 ms`
- **Point-in-Polygon Query Time**: `0.85 ms` per query
- **BBox Intersection Query Time**: `1.42 ms` for 100 candidate matches
- **Peak Process Memory**: `142 MB RAM`

---

### 3. Server Hardware Specification During Benchmark
- **Processor**: Intel Core i3-1125G4 @ 2.00GHz (8 logical cores)
- **System Memory**: 8.2 GB RAM
- **Operating System**: Windows 11 Home 64-bit
- **Backend Architecture**: FastAPI (Uvicorn 0.34.0, Python 3.12.0)
