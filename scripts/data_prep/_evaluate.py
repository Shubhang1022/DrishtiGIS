"""
DrishtiGIS Phase 3 — Evaluate best checkpoint on 12 official test tiles.
Generates:
  data/ai_output/evaluation/metrics.json
  data/ai_output/evaluation/test_report.md
  data/ai_output/evaluation/<tile>/  (RGB, GT mask, pred mask, overlays)

Must be run AFTER training is complete and best_model.pth is saved.
"""
import sys, os, json, time, warnings
warnings.filterwarnings('ignore', category=UserWarning)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)
os.chdir(root)

import numpy as np
import torch
from pathlib import Path

import rasterio
from rasterio.windows import Window

from backend.ai.segmentation.model import build_model
from backend.ai.segmentation.validation import SegmentationMetrics
from backend.ai.segmentation.masks import logits_to_mask, colour_mask, stitch_patches
from backend.ai.uavpal.classes import NUM_CLASSES, BUILDING_CLASS_ID, CLASS_BY_ID, COLOUR_PALETTE

# ── Config ────────────────────────────────────────────────────────────────────
CKPT_PATH    = Path("data/ai_models/uavpal/best_model.pth")
CONFIG_PATH  = "data/uavpal/training_config.json"
EVAL_DIR     = Path("data/ai_output/evaluation")
EVAL_DIR.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, encoding="utf-8") as f:
    cfg = json.load(f)

RGB_DIR   = Path(cfg["rgb_dir"])
LABEL_DIR = Path(cfg["label_dir"])
TEST_TILES = cfg["official_test_tiles"]   # 12 tiles — NEVER used in training/val
PATCH_SIZE  = cfg["patch_size"]           # 512
TILE_SIZE   = 2048
PATCHES_PER_AXIS = TILE_SIZE // PATCH_SIZE  # 4

# ImageNet normalisation (must match training)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

CLASS_NAMES = {c.id: c.name for c in CLASS_BY_ID.values()}

print(f"Evaluating {len(TEST_TILES)} official test tiles")
print(f"Checkpoint: {CKPT_PATH}")
print()

# ── Load model ────────────────────────────────────────────────────────────────
if not CKPT_PATH.exists():
    print(f"ERROR: checkpoint not found: {CKPT_PATH}")
    print("Run training first.")
    sys.exit(1)

model = build_model(num_classes=NUM_CLASSES, pretrained=False)
state = torch.load(str(CKPT_PATH), map_location="cpu", weights_only=True)
model.load_state_dict(state)
model.eval()
print(f"Model loaded: {model.parameter_count():,} parameters")
print()

# ── Per-tile inference + metric accumulation ─────────────────────────────────
global_metrics = SegmentationMetrics(num_classes=NUM_CLASSES)
per_tile_results = []
VIS_TILES = TEST_TILES[:6]   # generate visuals for first 6 test tiles

def load_rgb_patch(rgb_path, row_off, col_off):
    window = Window(col_off=col_off, row_off=row_off, width=PATCH_SIZE, height=PATCH_SIZE)
    with rasterio.open(str(rgb_path)) as src:
        rgb_raw = src.read(indexes=[1, 2, 3], window=window)  # (3,H,W) uint8
        rgb     = rgb_raw.astype(np.float32) / 255.0
        for c in range(3):
            rgb[c] = (rgb[c] - _MEAN[c]) / _STD[c]
    return torch.from_numpy(rgb).float(), rgb_raw   # normalised, and raw uint8

def load_label_patch(lbl_path, row_off, col_off):
    window = Window(col_off=col_off, row_off=row_off, width=PATCH_SIZE, height=PATCH_SIZE)
    with rasterio.open(str(lbl_path)) as src:
        return src.read(indexes=[1], window=window)[0]   # (H,W) uint8

for tile_id in TEST_TILES:
    t0       = time.time()
    rgb_path  = RGB_DIR   / f"{tile_id}.tiff"
    lbl_path  = LABEL_DIR / f"{tile_id}.tiff"

    # Collect patches for full-tile stitching (visuals)
    pred_patches_np = []
    gt_patches_np   = []
    rgb_patches_raw = []   # for visualization

    tile_metrics = SegmentationMetrics(num_classes=NUM_CLASSES)

    with torch.no_grad():
        for row in range(PATCHES_PER_AXIS):
            for col in range(PATCHES_PER_AXIS):
                row_off = row * PATCH_SIZE
                col_off = col * PATCH_SIZE

                img_tensor, rgb_raw = load_rgb_patch(rgb_path, row_off, col_off)
                lbl_arr = load_label_patch(lbl_path, row_off, col_off)

                img_batch = img_tensor.unsqueeze(0)   # (1,3,H,W)
                logits    = model(img_batch)           # (1,6,H,W)
                pred      = logits_to_mask(logits)[0]  # (H,W) int64

                lbl_tensor = torch.from_numpy(lbl_arr.copy()).long()

                tile_metrics.update(pred.unsqueeze(0), lbl_tensor.unsqueeze(0))
                global_metrics.update(pred.unsqueeze(0), lbl_tensor.unsqueeze(0))

                pred_patches_np.append(pred.numpy().astype(np.uint8))
                gt_patches_np.append(lbl_arr)
                rgb_patches_raw.append(rgb_raw)

    elapsed = time.time() - t0
    tile_result = tile_metrics.compute()

    print(f"  {tile_id}: bld_iou={tile_result['building_iou']:.4f}  "
          f"bld_f1={tile_result['building_f1']:.4f}  "
          f"miou={tile_result['mean_iou']:.4f}  "
          f"time={elapsed:.1f}s")

    per_tile_results.append({
        "tile_id": tile_id,
        "metrics": tile_result,
        "inference_time_s": round(elapsed, 2),
    })

    # ── Visuals ───────────────────────────────────────────────────────────────
    if tile_id in VIS_TILES:
        tile_vis_dir = EVAL_DIR / tile_id
        tile_vis_dir.mkdir(exist_ok=True)

        # Stitch full-tile masks
        pred_full = stitch_patches(pred_patches_np, TILE_SIZE, PATCH_SIZE)
        gt_full   = stitch_patches(gt_patches_np,   TILE_SIZE, PATCH_SIZE)

        # Stitch RGB (raw uint8 in CHW format — need to reassemble)
        rgb_rows = []
        for row_i in range(PATCHES_PER_AXIS):
            row_patches = rgb_patches_raw[row_i * PATCHES_PER_AXIS:(row_i + 1) * PATCHES_PER_AXIS]
            # Each patch is (3,512,512) uint8 — concatenate along W then H
            row_img = np.concatenate([p for p in row_patches], axis=2)  # (3,512,2048)
            rgb_rows.append(row_img)
        rgb_full = np.concatenate(rgb_rows, axis=1)  # (3,2048,2048)

        # Convert to HWC for PIL
        rgb_hwc = np.transpose(rgb_full, (1, 2, 0))   # (2048,2048,3)

        # Colour masks
        pred_colour = colour_mask(pred_full, COLOUR_PALETTE)
        gt_colour   = colour_mask(gt_full,   COLOUR_PALETTE)

        # Building-only binary masks
        pred_bld = (pred_full == BUILDING_CLASS_ID).astype(np.uint8) * 255
        gt_bld   = (gt_full   == BUILDING_CLASS_ID).astype(np.uint8) * 255

        # Overlay: building prediction on RGB
        overlay = rgb_hwc.copy()
        bld_mask_bool = pred_full == BUILDING_CLASS_ID
        overlay[bld_mask_bool] = (
            overlay[bld_mask_bool] * 0.4 +
            np.array([255, 100, 0], dtype=np.float32) * 0.6
        ).astype(np.uint8)

        # Save with PIL
        from PIL import Image
        # Save downsampled (512x512) versions for readability
        scale = 512
        def save_img(arr, path):
            img = Image.fromarray(arr)
            img = img.resize((scale, scale), Image.NEAREST)
            img.save(str(path))

        save_img(rgb_hwc,      tile_vis_dir / "rgb.png")
        save_img(pred_colour,  tile_vis_dir / "pred_mask.png")
        save_img(gt_colour,    tile_vis_dir / "gt_mask.png")
        save_img(np.stack([pred_bld]*3, axis=-1), tile_vis_dir / "pred_building.png")
        save_img(np.stack([gt_bld]*3,   axis=-1), tile_vis_dir / "gt_building.png")
        save_img(overlay,      tile_vis_dir / "overlay.png")
        print(f"    Visuals saved: {tile_vis_dir}")

# ── Global metrics ────────────────────────────────────────────────────────────
print()
global_result = global_metrics.compute()
print("=" * 60)
print("FINAL TEST RESULTS (12 official test tiles)")
print("=" * 60)
print(f"  Pixel accuracy  : {global_result['pixel_accuracy']:.4f}")
print(f"  Mean IoU        : {global_result['mean_iou']:.4f}")
print(f"  Building IoU    : {global_result['building_iou']:.4f}")
print(f"  Building Prec.  : {global_result['building_precision']:.4f}")
print(f"  Building Recall : {global_result['building_recall']:.4f}")
print(f"  Building F1     : {global_result['building_f1']:.4f}")
print()
print("  Per-class IoU:")
for name, iou in global_result["iou_per_class"].items():
    print(f"    {name:12s}: {iou:.4f}")

# ── Write metrics.json ────────────────────────────────────────────────────────
metrics_out = {
    "_meta": {
        "phase": "Phase 3 — Test Evaluation",
        "checkpoint": str(CKPT_PATH),
        "test_tiles": TEST_TILES,
        "n_test_tiles": len(TEST_TILES),
        "note": "These are FINAL TEST RESULTS — test tiles were never used during training or validation.",
    },
    "global_metrics": global_result,
    "per_tile_results": per_tile_results,
}
metrics_path = EVAL_DIR / "metrics.json"
with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics_out, f, indent=2, ensure_ascii=False)
print(f"\nMetrics saved: {metrics_path}")

# ── Write test_report.md ──────────────────────────────────────────────────────
report_lines = [
    "# DrishtiGIS Phase 3 — Final Test Evaluation Report",
    "",
    f"Checkpoint: `{CKPT_PATH}`  ",
    f"Test tiles: {len(TEST_TILES)} official UAVPal test tiles  ",
    "**These tiles were NEVER used for training or validation.**",
    "",
    "---",
    "",
    "## Global Test Metrics",
    "",
    "| Metric | Value |",
    "|---|---|",
    f"| Pixel Accuracy | {global_result['pixel_accuracy']:.4f} |",
    f"| Mean IoU | {global_result['mean_iou']:.4f} |",
    f"| **Building IoU** | **{global_result['building_iou']:.4f}** |",
    f"| Building Precision | {global_result['building_precision']:.4f} |",
    f"| Building Recall | {global_result['building_recall']:.4f} |",
    f"| Building F1 | {global_result['building_f1']:.4f} |",
    "",
    "## Per-Class IoU",
    "",
    "| Class | IoU |",
    "|---|---|",
]
for name, iou in global_result["iou_per_class"].items():
    report_lines.append(f"| {name} | {iou:.4f} |")

report_lines += [
    "",
    "---",
    "",
    "## Per-Tile Results",
    "",
    "| Tile | Bld IoU | Bld F1 | mIoU | Time (s) |",
    "|---|---|---|---|---|",
]
for tr in per_tile_results:
    m = tr["metrics"]
    report_lines.append(
        f"| {tr['tile_id']} | {m['building_iou']:.4f} | {m['building_f1']:.4f} | "
        f"{m['mean_iou']:.4f} | {tr['inference_time_s']:.1f} |"
    )

report_lines += [
    "",
    "---",
    "",
    "## Important Notes",
    "",
    "- This is a CPU-trained model (Intel i3-1125G4, no CUDA, no GPU acceleration).",
    "- Training used only 14 tiles (7,168 × 7,168 px total source data).",
    "- Building class ID = 4 (from UAVPal Annotation.gpkg — verified).",
    "- These metrics reflect semantic segmentation quality on the UAVPal test set.",
    "- The model has NOT been used to produce production GeoJSON yet.",
    "- Demo AI polygons (`bhopal-ai-features.geojson`) remain DEMO-labelled.",
]

report_path = EVAL_DIR / "test_report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print(f"Report saved: {report_path}")
print("\nEvaluation complete.")
