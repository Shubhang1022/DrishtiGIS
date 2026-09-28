# DrishtiGIS Phase 3 — Final Test Evaluation Report

Checkpoint: `data\ai_models\uavpal\best_model.pth`  
Test tiles: 12 official UAVPal test tiles  
**These tiles were NEVER used for training or validation.**

---

## Global Test Metrics

| Metric | Value |
|---|---|
| Pixel Accuracy | 0.5852 |
| Mean IoU | 0.3123 |
| **Building IoU** | **0.5240** |
| Building Precision | 0.8518 |
| Building Recall | 0.5766 |
| Building F1 | 0.6877 |

## Per-Class IoU

| Class | IoU |
|---|---|
| Background | 0.3170 |
| Water | 0.0000 |
| Road | 0.2984 |
| Car | 0.0948 |
| Building | 0.5240 |
| Tree | 0.6394 |

---

## Per-Tile Results

| Tile | Bld IoU | Bld F1 | mIoU | Time (s) |
|---|---|---|---|---|
| 00_01 | 0.2052 | 0.3405 | 0.2799 | 11.5 |
| 00_02 | 0.5584 | 0.7167 | 0.2609 | 11.2 |
| 00_04 | 0.4779 | 0.6468 | 0.3087 | 11.1 |
| 00_07 | 0.4932 | 0.6606 | 0.2889 | 11.5 |
| 00_10 | 0.6950 | 0.8200 | 0.2748 | 11.1 |
| 00_13 | 0.4676 | 0.6373 | 0.2958 | 10.9 |
| 00_14 | 0.4694 | 0.6389 | 0.2674 | 11.1 |
| 00_19 | 0.5848 | 0.7380 | 0.2966 | 11.6 |
| 01_00 | 0.4616 | 0.6316 | 0.1710 | 11.4 |
| 01_03 | 0.5480 | 0.7081 | 0.2943 | 11.2 |
| 01_04 | 0.6645 | 0.7984 | 0.1938 | 11.4 |
| 01_05 | 0.5428 | 0.7036 | 0.2946 | 11.1 |

---

## Important Notes

- This is a CPU-trained model (Intel i3-1125G4, no CUDA, no GPU acceleration).
- Training used only 14 tiles (7,168 × 7,168 px total source data).
- Building class ID = 4 (from UAVPal Annotation.gpkg — verified).
- These metrics reflect semantic segmentation quality on the UAVPal test set.
- The model has NOT been used to produce production GeoJSON yet.
- Demo AI polygons (`bhopal-ai-features.geojson`) remain DEMO-labelled.