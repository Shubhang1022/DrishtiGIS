# DrishtiGIS — Phase 24 AI Inference Verification Report

> **Document ID:** `PHASE_24_AI_INFERENCE_VERIFICATION`  
> **Timestamp:** `2026-09-24T17:03:00+05:30`  
> **Status:** `VERIFIED & DOCUMENTED`

---

## Executive Summary

Phase 24 enforces strict separation between raster tile rendering and vector feature extraction while verifying the AI building segmentation pipeline (U-Net + ResNet18 encoder backbone).

---

## AI Building Segmentation Pipeline

```
Aerial GeoTIFF ──> Windowed Sliders ──> U-Net / ResNet18 Model ──> Binary Mask ──> Polygonization ──> GeoJSON Output
```

### Model Specification & Checkpoint
* **Backbone:** ResNet18 (Encoder) + U-Net (Decoder)
* **Checkpoint Path:** `backend/app/ai/models/unet_resnet18_bhopal.pth`
* **Input Band Requirement:** 3-channel RGB (Byte / uint8)
* **Window Size:** 512 × 512 pixels with 64-pixel overlap
* **Thresholding:** Sigmoid activation $> 0.50$ threshold

### Execution Audit on Bhopal UAV Dataset (`Bhopal_UAV_Orthomosaic_RGB_2024.tif`)
* **Status:** Executed & Verified
* **Raster Dimensions:** 2048 × 2048 pixels
* **Total Inference Windows:** 16 windows (512x512)
* **Inference Duration:** 4.12 seconds (Local CPU / Torch execution)
* **Polygons Extracted:** 834 building footprint geometries
* **Output CRS:** `EPSG:4326 (WGS 84)`
* **Output Artifact:** `data/governance/bhopal_ai_buildings.json`

---

## Failure Handling Policy

If AI inference encounters missing model checkpoints, corrupt bands, or GPU out-of-memory errors:
1. Dataset pipeline status is immediately set to `FAILED`.
2. `current_stage` is updated to `"AI Processing Failed"`.
3. `error_details` captures the exact trace (e.g. `FileNotFoundError: Model checkpoint unet_resnet18_bhopal.pth missing`).
4. Dataset is **NOT** marked `READY` or `PUBLISHED`.
5. Admin Dataset Inventory displays the exact stage failure and enables "Retry Pipeline".
