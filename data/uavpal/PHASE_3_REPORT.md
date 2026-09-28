# DrishtiGIS Phase 3 — Training and Evaluation Report

Generated: 2026-09-12  
Status: **COMPLETE — Training done, test evaluation done, STOP**

---

## 1. Hardware

| Item | Value |
|---|---|
| CPU | Intel Core i3-1125G4 @ 2.00 GHz, 8 logical cores |
| RAM | 8.2 GB total, ~1.6 GB available during training |
| GPU | Intel UHD (integrated) — no CUDA, no GPU acceleration |
| PyTorch | 2.5.1+cpu |
| Training device | `cpu` |

---

## 2. Training Duration

| Phase | Epochs | Total Time |
|---|---|---|
| Pilot (10 epochs) | 10 | 6,658s (~111 min, ~11.1 min/epoch) |
| Full continuation (20 epochs) | 20 | 15,262s (~254 min, ~12.7 min/epoch) |
| **Total** | **30** | **21,920s (~6.1 hours)** |

Peak RAM during training: 0.26 GB RSS (model + activations) — well within safe limit.

---

## 3. Epoch Timings (full 20-epoch continuation)

| Ep (cont.) | Ep (overall) | T-Loss | V-Loss | V-BldIoU | V-mIoU | Time (s) | LR |
|---|---|---|---|---|---|---|---|
| 1  | 11 | 1.0702 | 1.0735 | 0.4590 | 0.1740 | 923.6 | 1e-4 |
| 2  | 12 | 1.0274 | 1.0979 | 0.4591 | 0.1694 | 923.3 | 1e-4 |
| 3  | 13 | 1.0077 | 1.0243 | 0.5213 | 0.2048 | 729.8 | 1e-4 |
| 4  | 14 | 1.0046 | 1.0497 | 0.4429 | 0.1901 | 679.1 | 1e-4 |
| 5  | 15 | 0.9749 | 1.0203 | 0.5214 | 0.2069 | 688.5 | 1e-4 |
| 6  | 16 | 0.9801 | 1.0057 | 0.5701 | 0.2209 | 715.4 | 1e-4 |
| 7  | 17 | 0.9595 | 1.0941 | 0.2892 | 0.1467 | 701.1 | 1e-4 |
| 8  | 18 | 0.9504 | 1.0584 | 0.4205 | 0.1728 | 949.1 | 1e-4 |
| 9  | 19 | 0.9187 | 1.0654 | 0.3187 | 0.1955 | 719.8 | 1e-4 |
| 10 | 20 | 0.9215 | 0.9904 | 0.5154 | 0.2207 | 683.0 | 1e-4 |
| 11 | 21 | 0.9250 | 1.0795 | 0.3665 | 0.1839 | 711.7 | 1e-4 |
| 12 | 22 | 0.9435 | 0.9705 | 0.5519 | 0.1973 | 724.0 | **5e-5** |
| 13 | 23 | 0.8858 | 0.9790 | 0.4948 | 0.2416 | 716.9 | 5e-5 |
| 14 | 24 | 0.8798 | 0.9953 | 0.4886 | 0.2013 | 705.3 | 5e-5 |
| **15** | **25** | **0.8961** | **0.9312** | **0.5867** | **0.2504** | **689.3** | **5e-5** |
| 16 | 26 | 0.8524 | 1.0025 | 0.3867 | 0.1912 | 812.1 | 5e-5 |
| 17 | 27 | 0.8703 | 0.9708 | 0.4572 | 0.2346 | 822.8 | 5e-5 |
| 18 | 28 | 0.8722 | 0.9191 | 0.5649 | 0.2462 | 845.6 | 5e-5 |
| 19 | 29 | 0.8802 | 1.0265 | 0.3696 | 0.1775 | 731.3 | 5e-5 |
| 20 | 30 | 0.8641 | 0.9772 | 0.4677 | 0.1972 | 786.1 | 5e-5 |

Best checkpoint: **epoch 25 (continuation epoch 15)**, Building IoU = 0.5867.  
Early stopping did not trigger (patience=10 not exceeded within budget).

---

## 4. RAM Usage

Peak RSS during training: **~0.26 GB** per process.  
System total: 8.2 GB. Safe limit: 6.6 GB. Training well within limits.  
`batch_size=2`, `gradient_accumulation_steps=4` (effective batch = 8).

---

## 5. Training Configuration

| Parameter | Value |
|---|---|
| Architecture | U-Net |
| Encoder | ResNet18 (random init — no pretrained weights) |
| Input | (B, 3, 512, 512) float32, ImageNet-normalised |
| Output | (B, 6, 512, 512) float32 logits |
| Parameters | 14,339,846 |
| Patch size | 512 × 512 |
| Batch size | 2 |
| Grad accum steps | 4 (effective batch = 8) |
| LR (initial) | 1e-4 |
| LR (after plateau) | 5e-5 (reduced at epoch 22) |
| Weight decay | 1e-4 |
| Loss | CrossEntropyDice (CE weight=0.5, Dice weight=0.5) |
| Class weights | [Background:0.435, Water:0.0, Road:1.0, Car:10.0, Building:0.211, Tree:2.414] |
| Seed | 42 |
| Augmentation | Random H/V flip (applied identically to image and mask) |

---

## 6. Validation Results (best checkpoint, epoch 25)

| Metric | Value |
|---|---|
| Building IoU | **0.5867** |
| Building F1 | 0.7395 |
| Building Precision | 0.8831 |
| Building Recall | 0.6361 |
| Mean IoU | 0.2504 |
| Pixel Accuracy | 0.6024 |

---

## 7. Final Test Results (12 official test tiles — evaluated ONCE)

**These tiles were NEVER used for training or validation.**

| Metric | Value |
|---|---|
| Pixel Accuracy | 0.5852 |
| **Mean IoU** | **0.3123** |
| **Building IoU** | **0.5240** |
| Building Precision | 0.8518 |
| Building Recall | 0.5766 |
| Building F1 | 0.6877 |

---

## 8. Per-Class IoU (test set)

| Class ID | Class Name | IoU |
|---|---|---|
| 0 | Background | 0.3170 |
| 1 | Water | 0.0000 |
| 2 | Road | 0.2984 |
| 3 | Car | 0.0948 |
| **4** | **Building** | **0.5240** |
| 5 | Tree | 0.6394 |

---

## 9. Building IoU (per test tile)

| Tile | Building IoU | Building F1 | mIoU |
|---|---|---|---|
| 00_01 | 0.2052 | 0.3405 | 0.2799 |
| 00_02 | 0.5584 | 0.7167 | 0.2609 |
| 00_04 | 0.4779 | 0.6468 | 0.3087 |
| 00_07 | 0.4932 | 0.6606 | 0.2889 |
| 00_10 | **0.6950** | **0.8200** | 0.2748 |
| 00_13 | 0.4676 | 0.6373 | 0.2958 |
| 00_14 | 0.4694 | 0.6389 | 0.2674 |
| 00_19 | 0.5848 | 0.7380 | 0.2966 |
| 01_00 | 0.4616 | 0.6316 | 0.1710 |
| 01_03 | 0.5480 | 0.7081 | 0.2943 |
| 01_04 | **0.6645** | **0.7984** | 0.1938 |
| 01_05 | 0.5428 | 0.7036 | 0.2946 |

---

## 10–11. Building Precision / Recall / F1

See table in section 7.  
- Precision 0.852 — model is selective, low false positive rate
- Recall 0.577 — model misses ~42% of building pixels (expected for 30-epoch CPU model from scratch)
- F1 0.688 — solid baseline for a model trained on ~14 tiles, CPU only, no pretrained encoder

---

## 12. Mean IoU

**0.3123** across 12 test tiles, 6 classes.  
Best class: Tree (0.639), followed by Building (0.524).  
Water: 0.000 — absent in this region, model predicts 0 pixels as Water.  
Car: 0.095 — rare class, hard to learn with small patches.

---

## 13. Qualitative Observations

- Model precision is consistently high (0.85+) — building predictions are reliable where made.
- Main weakness is recall: model tends to under-segment buildings in dense urban clusters.
- Tree class achieves better IoU than Building (0.639 vs 0.524) due to more distinctive texture.
- 00_01 tile is an outlier (Building IoU = 0.205) — likely contains scene types poorly represented in train set (sparse buildings, edge effects, or different urban texture from validation distribution).
- Tile 00_10 and 01_04 are strong performers (IoU 0.695, 0.665).
- Val IoU oscillation during training is a known effect of the small validation set (4 tiles = 64 patches) — building up/down with patch sampling randomness.

---

## 14. Known Failure Cases

| Failure | Description |
|---|---|
| Dense building adjacency | Adjacent touching buildings are often merged into single prediction |
| Low-contrast rooftops | Dark/weathered rooftops misclassified as Road or Background |
| Water = 0 IoU | No water in training area — model cannot predict water class |
| Car = 0.095 IoU | Very few car pixels; not enough examples at 512×512 patches |
| 00_01 low performance | Scene characteristics differ from training distribution |

---

## 15. Visual Evaluation

6 test tiles have visual outputs in `data/ai_output/evaluation/<tile>/`:
- `rgb.png` — downsampled RGB source (512×512 preview)
- `gt_mask.png` — ground-truth semantic mask (colour-coded)
- `pred_mask.png` — model prediction semantic mask
- `gt_building.png` — ground-truth building binary mask
- `pred_building.png` — predicted building binary mask
- `overlay.png` — RGB with building prediction highlighted in orange

Tiles with visuals: 00_01, 00_02, 00_04, 00_07, 00_10, 00_13

---

## Data Integrity

- 30 RGB TIFFs: **byte-exact** (unchanged)
- 30 label TIFFs: **byte-exact** (unchanged)
- PBF: 1,706,252,573 bytes — unchanged
- Demo AI polygons: remain labelled `"model": "DEMO — not from real inference"`

---

## Test Baseline

```
Backend WebGIS tests: 90 PASS, 1 FAIL
FAILED: test_ai_feature_filter_by_parcel (pre-existing data drift, not modified)
```

---

## Files Created This Phase

| File | Description |
|---|---|
| `data/uavpal/class_distribution.json` | Per-class pixel counts and median-frequency weights |
| `data/uavpal/validation_split.json` | 14/4/12 deterministic tile split |
| `data/uavpal/training_config.json` | Full training configuration |
| `data/uavpal/ram_check_result.json` | RAM safety check results |
| `data/ai_models/uavpal/best_model.pth` | Best checkpoint (epoch 25, 54.8 MB) |
| `data/ai_models/uavpal/latest_model.pth` | Final checkpoint (epoch 30, 54.8 MB) |
| `data/ai_models/uavpal/model_metadata.json` | Full model provenance |
| `data/ai_models/uavpal/training_history.json` | Per-epoch metrics (20 epochs) |
| `data/ai_output/evaluation/metrics.json` | Test evaluation results |
| `data/ai_output/evaluation/test_report.md` | Test report |
| `data/ai_output/evaluation/<tile>/*.png` | Visual evaluation (6 tiles × 6 images = 36 PNGs) |

---

## STOP — Phase 3 Complete

No production GeoJSON was generated.  
No demo AI polygons were replaced.  
No WebGIS frontend was modified.  
No parcel geometry was modified.

**Waiting for explicit Phase 4 approval:**  
**Semantic mask → individual building polygons → georeferencing**
