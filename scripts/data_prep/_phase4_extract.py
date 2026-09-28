"""
DrishtiGIS Phase 4 — Full extraction pipeline.

Runs all 30 Bhopal UAV tiles through:
  1. Model inference (best_model.pth)
  2. Building mask extraction + morphological cleaning
  3. Min-area sensitivity analysis (2/5/10 m²)
  4. Connected-component analysis
  5. Watershed separation of touching buildings
  6. Contour → pixel polygon
  7. Pixel → EPSG:32643 → EPSG:4326 via GeoTIFF affine
  8. Geometry validation + repair (make_valid)
  9. Cross-tile deduplication (centroid 5m + IoU 0.15)
  10. Write bhopal-buildings-ai.geojson
  11. Write bhopal-building-inference-report.json
  12. Write per-tile visual QA
"""
import sys, os, json, time, datetime, warnings, math
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)
os.chdir(root)

os.makedirs("data/ai_output", exist_ok=True)
LOG_PATH = "data/ai_output/phase4_log.txt"
log_fh   = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
sys.stdout = log_fh
sys.stderr = log_fh

import numpy as np
import torch
from pathlib import Path

from backend.ai.segmentation.model       import build_model
from backend.ai.segmentation.postprocess import (
    extract_building_components, run_inference_tile,
    min_area_sensitivity, DEFAULT_PX_SIZE_M, TileExtractionResult,
)
from backend.ai.segmentation.georef  import tile_components_to_features, GeometryRepairStats
from backend.ai.segmentation.dedup   import deduplicate_features, ADJACENT_PAIRS
from backend.ai.uavpal.classes       import NUM_CLASSES, BUILDING_CLASS_ID

# ── Config ────────────────────────────────────────────────────────────────────
CKPT_PATH   = Path("data/ai_models/uavpal/best_model.pth")
CONFIG_PATH = "data/uavpal/training_config.json"
RGB_DIR     = Path("Dataset/geospatial-data/BHOPAL")
LABEL_DIR   = Path("data/uavpal/annotations/Label/Tiles")
OUT_DIR     = Path("data/ai_output")
VIS_DIR     = OUT_DIR / "phase4_qa"
VIS_DIR.mkdir(parents=True, exist_ok=True)

MIN_AREA_M2 = 5.0
PX_SIZE_M   = DEFAULT_PX_SIZE_M

with open(CONFIG_PATH, encoding="utf-8") as f:
    cfg = json.load(f)

ALL_TILES = sorted(f.stem for f in RGB_DIR.glob("*.tiff"))

VIS_TILES = {"00_10", "00_11", "01_04", "00_06", "00_19",
             "01_02", "00_00", "00_22"}


# ── Visual QA helper ──────────────────────────────────────────────────────────

def save_visual_qa(tile_id, pred_mask, result, feats, rgb_dir, vis_dir):
    """Save 5 QA images for a tile: RGB, raw mask, semantic mask, polygon overlay, final footprints."""
    try:
        import rasterio
        from PIL import Image, ImageDraw
        from backend.ai.segmentation.masks import colour_mask
        from backend.ai.uavpal.classes import COLOUR_PALETTE
        from shapely.geometry import shape as shp_shape
        from pyproj import Transformer

        tile_dir = vis_dir / tile_id
        tile_dir.mkdir(exist_ok=True)
        SCALE = 512
        sf    = SCALE / 2048.0

        # RGB
        with rasterio.open(str(rgb_dir / f"{tile_id}.tiff")) as src:
            rgb = src.read(indexes=[1, 2, 3])
            aff = src.transform
        rgb_hwc = np.transpose(rgb, (1, 2, 0))
        img_rgb = Image.fromarray(rgb_hwc).resize((SCALE, SCALE), Image.NEAREST)
        img_rgb.save(str(tile_dir / "rgb.png"))

        # Raw building mask
        bld_raw = (pred_mask == BUILDING_CLASS_ID).astype(np.uint8) * 255
        Image.fromarray(bld_raw).resize((SCALE, SCALE), Image.NEAREST).save(
            str(tile_dir / "mask_building_raw.png"))

        # Semantic colour mask
        sem = colour_mask(pred_mask, COLOUR_PALETTE)
        Image.fromarray(sem).resize((SCALE, SCALE), Image.NEAREST).save(
            str(tile_dir / "mask_semantic.png"))

        # Component polygon overlay (pixel space)
        ov1 = img_rgb.copy().convert("RGBA")
        d1  = ImageDraw.Draw(ov1, "RGBA")
        for comp in result.components:
            pts = [(c * sf, r * sf) for c, r in comp.pixel_contour]
            if len(pts) >= 3:
                d1.polygon(pts, fill=(255,100,0,80), outline=(255,60,0,220))
        ov1.save(str(tile_dir / "polygon_overlay.png"))

        # Final GeoJSON footprints back-projected to pixel space for display
        ov2   = img_rgb.copy().convert("RGBA")
        d2    = ImageDraw.Draw(ov2, "RGBA")
        inv   = ~aff
        t_inv = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
        for feat in feats:
            if feat["properties"]["source_tile"] != tile_id:
                continue
            try:
                geom = shp_shape(feat["geometry"])
                pts  = []
                for lon, lat in geom.exterior.coords:
                    e, n = t_inv.transform(lon, lat)
                    col, row = inv * (e, n)
                    pts.append((col * sf, row * sf))
                if len(pts) >= 3:
                    d2.polygon(pts, fill=(0,200,255,90), outline=(0,150,255,220))
            except Exception:
                pass
        ov2.save(str(tile_dir / "final_footprints.png"))

        print(f"  [QA] {tile_id}: saved to {tile_dir}", flush=True)
    except Exception as e:
        print(f"  [QA] {tile_id}: FAILED — {e}", flush=True)


# ── Main pipeline ─────────────────────────────────────────────────────────────

print(f"Phase 4 — Building footprint extraction")
print(f"Started : {datetime.datetime.now().isoformat()}")
print(f"Tiles   : {len(ALL_TILES)}")
print(f"Checkpoint: {CKPT_PATH}")
print(f"Min area  : {MIN_AREA_M2} m2")
print(f"Px size   : {PX_SIZE_M*100:.3f} cm/px")
print()

# Load model
if not CKPT_PATH.exists():
    print(f"ERROR: checkpoint not found: {CKPT_PATH}")
    sys.exit(1)

device = torch.device("cpu")
model  = build_model(num_classes=NUM_CLASSES, pretrained=False)
state  = torch.load(str(CKPT_PATH), map_location=device, weights_only=True)
model.load_state_dict(state)
model.eval()
print(f"Model loaded: {model.parameter_count():,} params\n")

all_features: list = []
repair_stats  = GeometryRepairStats()
per_tile_report: list = []
total_raw_cc  = 0
total_filtered = 0
total_ws_splits = 0
sensitivity_done    = False
sensitivity_results = {}

for tile_id in ALL_TILES:
    t0      = time.time()
    rgb_path = RGB_DIR / f"{tile_id}.tiff"
    print(f"[{tile_id}] inferring...", end=" ", flush=True)

    # Inference
    pred_mask, prob_bld = run_inference_tile(model, rgb_path, device)
    t_inf = time.time() - t0
    bld_px = int((pred_mask == BUILDING_CLASS_ID).sum())
    print(f"{t_inf:.0f}s bld_px={bld_px:,}", end="  ", flush=True)

    # Min-area sensitivity (first tile only)
    if not sensitivity_done:
        sensitivity_results = min_area_sensitivity(tile_id, pred_mask, prob_bld)
        print(f"sensitivity: 2m2={sensitivity_results.get('2.0m2','?')} "
              f"5m2={sensitivity_results.get('5.0m2','?')} "
              f"10m2={sensitivity_results.get('10.0m2','?')}",
              end="  ", flush=True)
        sensitivity_done = True

    # Extract components
    result: TileExtractionResult = extract_building_components(
        tile_id=tile_id, pred_mask=pred_mask, prob_building=prob_bld,
        min_area_m2=MIN_AREA_M2, px_size_m=PX_SIZE_M,
        use_watershed=True, simplify_px=1.5,
    )
    total_raw_cc    += result.raw_components
    total_filtered  += result.filtered_components
    total_ws_splits += result.watershed_splits
    print(f"cc={result.raw_components} filt={result.filtered_components} ws={result.watershed_splits}",
          end="  ", flush=True)

    # Georef → GeoJSON features
    feats = tile_components_to_features(result.components, RGB_DIR, repair_stats)
    all_features.extend(feats)
    t_tot = time.time() - t0
    print(f"feats={len(feats)} total={t_tot:.0f}s", flush=True)

    per_tile_report.append({
        "tile_id": tile_id, "raw_components": result.raw_components,
        "filtered_components": result.filtered_components,
        "watershed_splits": result.watershed_splits,
        "geojson_features": len(feats),
        "building_pixels": result.mask_building_pixels,
        "inference_time_s": round(t_inf, 2),
        "total_time_s": round(t_tot, 2),
    })

    # Visual QA
    if tile_id in VIS_TILES:
        save_visual_qa(tile_id, pred_mask, result, feats, RGB_DIR, VIS_DIR)

# ── Deduplication ─────────────────────────────────────────────────────────────
print()
print(f"Raw components  : {total_raw_cc:,}")
print(f"Filtered        : {total_filtered:,}")
print(f"WS splits       : {total_ws_splits:,}")
print(f"Raw features    : {len(all_features):,}")
print("Deduplicating...", flush=True)

final_features, n_removed, n_merged = deduplicate_features(all_features)
print(f"Removed: {n_removed}  Merged: {n_merged}  Final: {len(final_features):,}", flush=True)

# Stats
confs    = [f["properties"]["confidence"] for f in final_features]
areas    = [f["properties"]["area_m2"]    for f in final_features]
avg_conf = float(np.mean(confs)) if confs else 0.0
med_conf = float(np.median(confs)) if confs else 0.0
avg_area = float(np.mean(areas))  if areas else 0.0

# ── Write GeoJSON ─────────────────────────────────────────────────────────────
geojson_path = OUT_DIR / "bhopal-buildings-ai.geojson"
geojson_out  = {
    "type": "FeatureCollection",
    "metadata": {
        "_source":          "AI_DERIVED_UAVPAL",
        "_disclaimer":      (
            "AI-derived building footprints from UAVPal semantic segmentation. "
            "NOT cadastral boundaries. NOT legal property boundaries. "
            "For research and visualization purposes only."
        ),
        "model":            "UNet-ResNet18-UAVPal",
        "model_version":    "phase3-epoch25-bld_iou0.587",
        "source_dataset":   "UAVPal v1 (doi:10.17026/DANS-Z55-6GT4)",
        "source_class":     BUILDING_CLASS_ID,
        "source_class_name":"Building",
        "crs":              "EPSG:4326",
        "total_buildings":  len(final_features),
        "generated":        datetime.datetime.now().isoformat(),
    },
    "features": final_features,
}
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(geojson_out, f, separators=(",", ":"), ensure_ascii=False)
size_mb = os.path.getsize(geojson_path) / 1e6
print(f"\nGeoJSON written: {geojson_path}  ({size_mb:.2f} MB)", flush=True)

# ── Write report ──────────────────────────────────────────────────────────────
report = {
    "_meta": {"phase": "Phase 4", "generated": datetime.datetime.now().isoformat()},
    "model":                  "UNet-ResNet18-UAVPal",
    "model_checkpoint":       str(CKPT_PATH),
    "source_tiles":           ALL_TILES,
    "source_tile_count":      len(ALL_TILES),
    "min_area_threshold_m2":  MIN_AREA_M2,
    "min_area_rationale": (
        f"Pixel size {PX_SIZE_M*100:.3f} cm → 1px = {PX_SIZE_M**2:.6f} m². "
        f"5 m² ≈ {int(MIN_AREA_M2/PX_SIZE_M**2):,} px. "
        "Removes sub-4px noise while retaining small sheds and annexes."
    ),
    "min_area_sensitivity":   sensitivity_results,
    "total_raw_components":   total_raw_cc,
    "total_filtered_components": total_filtered,
    "total_watershed_splits": total_ws_splits,
    "total_raw_polygons":     len(all_features),
    "duplicates_removed":     n_removed,
    "duplicates_merged":      n_merged,
    "final_building_count":   len(final_features),
    "geometry_repair": {
        "total":          repair_stats.total,
        "invalid_before": repair_stats.invalid,
        "repaired":       repair_stats.repaired,
        "failed":         repair_stats.failed,
        "method":         repair_stats.method,
    },
    "confidence_methodology": "mean_softmax_p_building_over_component_pixels",
    "average_confidence":     round(avg_conf, 4),
    "median_confidence":      round(med_conf, 4),
    "average_area_m2":        round(avg_area, 2),
    "deduplication": {
        "method":         "centroid_proximity_5m + polygon_iou_0.15",
        "max_centroid_m": 5.0,
        "min_iou":        0.15,
        "adjacent_pairs": len(ADJACENT_PAIRS),
    },
    "crs_source":             "EPSG:32643",
    "crs_output":             "EPSG:4326",
    "output_geojson":         str(geojson_path),
    "per_tile":               per_tile_report,
}

report_path = OUT_DIR / "bhopal-building-inference-report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"Report written:  {report_path}", flush=True)
print()
print(f"PHASE 4 COMPLETE: {len(final_features):,} building footprints")
print(f"Finished: {datetime.datetime.now().isoformat()}")
log_fh.flush()
log_fh.close()
