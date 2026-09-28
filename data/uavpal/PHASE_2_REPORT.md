# DrishtiGIS Phase 2 — Segmentation Pipeline Preparation Report

Generated: 2026-09-08  
Status: **COMPLETE — Smoke test PASS, no training performed**

---

## 1. Environment

| Item | Value |
|---|---|
| ML Python | 3.12.0 (`C:\Python312\python.exe`) |
| ML venv | `scripts/.ml-env/` (Python 3.12, isolated) |
| GIS venv | `scripts/.gis-env/` (Python 3.14, rasterio only — unchanged) |
| OS | Windows (win32) |
| CPU | Intel Core i3-1125G4 @ 2.00 GHz, 8 logical cores |
| RAM | 7.7 GB total |
| GPU | Intel UHD Graphics (integrated — no CUDA) |
| Disk free | 13.8 GB |
| CUDA | Not available — CPU-only training |

---

## 2. Installed Packages (scripts/.ml-env)

| Package | Version |
|---|---|
| torch | 2.5.1+cpu |
| torchvision | 0.20.1+cpu |
| rasterio | 1.3.10 |
| numpy | 2.4.6 |
| pillow | 12.3.0 |
| scipy | 1.15.3 |
| scikit-image | 0.25.2 |
| shapely | 2.1.1 |
| geopandas | 1.0.1 |
| pyproj | 3.7.1 |
| segmentation-models-pytorch | 0.3.4 |
| pytest | 8.3.5 |

PyTorch installed as CPU-only wheel (`+cpu`) — correct for this machine (no NVIDIA GPU).  
CUDA packages were **not** installed.

---

## 3. Python / PyTorch / torchvision Versions

```
Python      : 3.12.0
torch       : 2.5.1+cpu
torchvision : 0.20.1+cpu
CUDA        : Not available (CPU only)
```

---

## 4. CPU / GPU Information

- CPU: Intel i3-1125G4, 8 logical cores, ~2 GHz
- RAM: 7.7 GB total
- GPU: Intel UHD (integrated graphics) — no CUDA support
- PyTorch device: `cpu`
- Estimated training time for Phase 3 (CPU, 224 patches/epoch): slow but feasible for smoke test; full training will require GPU or cloud

---

## 5. Validation Split

Deterministic, spatially distributed. No random shuffling.

| Split | Tiles | Count |
|---|---|---|
| Internal train | 00_05, 00_06, 00_08, 00_09, 00_11, 00_12, 00_15, 00_16, 00_17, 00_18, 00_20, 01_01, 01_02, 01_06 | 14 |
| Validation | 00_00, 00_03, 00_21, 00_22 | 4 |
| Official test (untouched) | 00_01, 00_02, 00_04, 00_07, 00_10, 00_13, 00_14, 00_19, 01_00, 01_03, 01_04, 01_05 | 12 |

**Strategy:** Validation tiles taken from the western (cols 00, 03) and eastern (cols 21, 22) ends of row 00.  
This provides geographic spread and avoids placing spatially adjacent tiles in both train and validation.  
Seed: 42. No leakage between any split pair (verified by test suite).

---

## 6. Patch Size

| Parameter | Value | Rationale |
|---|---|---|
| Source tile | 2048 x 2048 px | UAVPal standard |
| Patch size | 512 x 512 px | 16 non-overlapping patches per tile |
| Patch stride | 512 px | Non-overlapping for val; reducible for train augmentation |
| Patches per tile | 16 (4x4 grid) | (2048/512)^2 |
| Ground coverage | ~10.24 m x 10.24 m per patch | @ ~2 cm/px resolution |
| Approx train patches | 224 | 14 tiles x 16 |
| Approx val patches | 64 | 4 tiles x 16 |

512 px was chosen over 256 px (too small for building context) and 1024 px (too large for 7.7 GB RAM on CPU).

---

## 7. Batch Size

**batch_size = 2** for Phase 3 training.  
Rationale: 2 x (3 x 512 x 512) float32 image patches = ~6 MB per batch, well within RAM budget.  
Smoke test used batch_size = 1.

---

## 8. Model Architecture

```
Architecture : U-Net
Encoder      : ResNet18 (torchvision)
Encoder weights : None (random init for Phase 2 smoke test)
Input        : (B, 3, 512, 512) float32 — normalised RGB
Output       : (B, 6, 512, 512) float32 — per-pixel class logits
Parameters   : 14,339,846 total (~14.3M)
```

Encoder feature map stages:
| Stage | Channels | Spatial (for 512 input) |
|---|---|---|
| enc0 (stem) | 64 | 256 x 256 |
| enc1 (layer1) | 64 | 128 x 128 |
| enc2 (layer2) | 128 | 64 x 64 |
| enc3 (layer3) | 256 | 32 x 32 |
| enc4 (layer4, bottleneck) | 512 | 16 x 16 |

Decoder: bilinear upsample + skip concatenation + DoubleConv at each level.  
Final building mask: `argmax(output, dim=1) == 4`

Implementation: pure `torch` + `torchvision`. Does NOT require segmentation-models-pytorch at runtime.

---

## 9. Smoke Test Results

**Tile:** `00_05` (internal train)  
**Device:** CPU  
**All 12 checks: PASS**

| Check | Result | Detail |
|---|---|---|
| [1] Pair loaded | PASS | load_time=0.179s |
| [2] Image shape | PASS | (3, 512, 512) float32 |
| [3] Label shape | PASS | (512, 512) int64 |
| [4] Output 6 channels | PASS | output=(1, 6, 512, 512) |
| [5] Label values 0-5 only | PASS | unique=[0, 2, 4] |
| [6] Output spatial dims | PASS | 512x512 == 512x512 |
| [7] Forward pass | PASS | 0.914s |
| [8] Loss computed | PASS | CrossEntropyDice=1.382328 |
| [9a] Backward pass | PASS | grad_norm=2.3338 |
| [9b] Optimizer step | PASS | Adam step complete |
| [10a] No NaN/Inf in output | PASS | clean |
| [10b] No NaN/Inf in loss | PASS | clean |

Result JSON saved to: `data/uavpal/smoke_test_result.json`

---

## 10. Tensor Dimensions

| Tensor | Shape | dtype |
|---|---|---|
| Input image patch | (1, 3, 512, 512) | float32 |
| Label patch | (1, 512, 512) | int64 |
| Model output (logits) | (1, 6, 512, 512) | float32 |
| Building binary mask | (1, 512, 512) | bool |
| Loss scalar | () | float32 |

---

## 11. Loss Calculation Result

```
Loss function : CrossEntropyDiceLoss
  CE weight   : 0.5
  Dice weight : 0.5
Loss value    : 1.382328
```

Expected range at random init with 6 classes: ~ln(6) ≈ 1.79 for pure CE.  
Combined CE+Dice at ~1.38 is consistent with random weights — no indication of numerical issues.

---

## 12. Memory Usage

Approximate peak memory during smoke test (CPU, batch_size=1, 512x512):

| Component | Approx size |
|---|---|
| Input image tensor | ~3 MB |
| Model parameters (float32) | ~55 MB |
| Activations (forward pass) | ~200-400 MB estimated |
| Gradients (backward) | ~55 MB |
| **Total peak** | **~350-500 MB** |

7.7 GB RAM is more than sufficient for batch_size=2 during training.

---

## 13. Test Results

### AI pipeline tests (scripts/.ml-env Python 3.12)

```
46 passed, 0 failed
```

| Group | Tests | Result |
|---|---|---|
| TestClassMapping | 8 | PASS |
| TestFilePairing | 4 | PASS |
| TestTileDimensions | 3 | PASS |
| TestLabelValues | 3 | PASS |
| TestSplitIntegrity | 7 | PASS |
| TestTrainingConfig | 7 | PASS |
| TestPatchExtraction | 7 | PASS |
| TestModelOutputShape | 7 | PASS |

### Backend WebGIS tests (system Python 3.14)

```
90 passed, 1 failed (pre-existing)
FAILED: test_ai_feature_filter_by_parcel — assert 2 == 1
```

Pre-existing data drift from uncommitted `bhopal-ai-features.geojson` modification.  
Not introduced by Phase 2. Not modified.

### Dataset integrity

```
30 RGB TIFFs: byte-exact (unchanged)
PBF: 1,706,252,573 bytes (unchanged)
```

---

## 14. Problems Encountered

| Problem | Resolution |
|---|---|
| GIS venv uses Python 3.14 — PyTorch not available for 3.14 | Created separate `scripts/.ml-env` with Python 3.12.0 |
| Windows console `UnicodeEncodeError` for `\u2286` in print | Replaced with ASCII equivalent `in [0-5]` in train.py |
| Tee-Object caching stale output in reused terminal | Stopped and restarted terminal process; used script file with `sys.stdout.reconfigure(encoding='utf-8')` |

---

## Files Created This Phase

| File | Description |
|---|---|
| `scripts/.ml-env/` | Python 3.12 ML virtual environment |
| `data/uavpal/validation_split.json` | Deterministic 14/4/12 tile split |
| `data/uavpal/training_config.json` | Full training configuration |
| `data/uavpal/smoke_test_result.json` | Smoke test JSON output |
| `backend/ai/__init__.py` | Package init |
| `backend/ai/uavpal/__init__.py` | Package init |
| `backend/ai/uavpal/classes.py` | Authoritative class definitions |
| `backend/ai/uavpal/dataset.py` | Patch-based dataset loader |
| `backend/ai/segmentation/__init__.py` | Package init |
| `backend/ai/segmentation/model.py` | U-Net ResNet18 (pure torch) |
| `backend/ai/segmentation/train.py` | Loss function + smoke test runner |
| `backend/ai/segmentation/inference.py` | Tile inference utilities |
| `backend/ai/segmentation/masks.py` | Mask post-processing |
| `backend/ai/segmentation/validation.py` | Segmentation metrics |
| `backend/tests/test_ai_pipeline.py` | 46 AI pipeline unit tests |

---

## STOP — Phase 2 Complete

No full training was performed.  
No model weights were downloaded.  
No AI polygons were generated.  
Demo polygons in `bhopal-ai-features.geojson` remain labelled as `DEMO — not from real inference`.

**Waiting for explicit approval to begin Phase 3 (full training).**
