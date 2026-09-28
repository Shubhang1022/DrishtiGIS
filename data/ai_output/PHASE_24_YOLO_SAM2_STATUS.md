# DrishtiGIS — Phase 24 YOLO & SAM 2 Architectural Status Report

> **Document ID:** `PHASE_24_YOLO_SAM2_STATUS`  
> **Timestamp:** `2026-09-24T17:03:00+05:30`  
> **Status:** `EVALUATED & DEFERRED (Phase 24 Core Priorities Preserved)`

---

## Executive Summary

Task 16 of Phase 24 specifies that YOLO object segmentation and Segment Anything Model 2 (SAM 2) interactive polygon refinement should only be evaluated AFTER core raster visibility and tile service endpoints are fully functional. This report details the current integration status, architecture design, and deployment roadmap for YOLOv8-Seg and SAM 2 within DrishtiGIS.

---

## Current Architecture & Status

```
[WebGIS Canvas] ──> User Clicks Feature ──> Prompt Coordinates (Lon/Lat)
                                                    │
                                                    ▼
                                         [SAM 2 Sidecar Service]
                                         (onnx / torch instance)
                                                    │
                                                    ▼
                                       Refined Polygon Geometry
                                                    │
                                                    ▼
                                    [Surveyor Review & Verification]
```

### 1. YOLOv8-Seg Instance Segmentation Engine
* **Purpose:** Object-level feature candidate detection (e.g. solar panels, vehicles, informal structures).
* **Current Status:** Optional secondary backend pipeline module (`backend/app/ai/yolo_detector.py`).
* **Evaluation:** Disabled by default during dataset ingestion to prevent pipeline latency and memory contention with raster tile generation. Available for trigger via manual administrative AI job execution.

### 2. SAM 2 Interactive Polygon Refinement
* **Purpose:** Allows surveyors during field verification or desktop review (`/app/review`) to click a point on an aerial image and receive an automated high-precision polygon outline around the building structure.
* **Current Status:** API interface defined; model weights (`sam2_hiera_tiny.pt`) deferred to dedicated GPU environment or ONNX WebAssembly sidecar.
* **Integrity Guard:** Interactive SAM 2 edits generate a **new candidate geometry version** in `data/governance/reviews.json` and NEVER overwrite original AI baseline outputs.
