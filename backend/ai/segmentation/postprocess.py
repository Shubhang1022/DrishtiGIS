"""
DrishtiGIS Phase 4 — Post-processing: semantic mask → building polygons (pixel space).

Pipeline per tile:
  1. Run model inference → 6-class logit map
  2. Extract Building mask (class 4) + probability map
  3. Morphological noise filtering
  4. Connected-component labelling
  5. Min-area filtering (sensitivity: 2 / 5 / 10 m²)
  6. Optional watershed separation of touching buildings
  7. Contour extraction → closed polygon (pixel coordinates)
  8. Return list of BuildingComponent dataclasses

Coordinate conversion is handled by georef.py.
Deduplication across tiles is handled by dedup.py.

Resolution: ~2.17 cm/pixel → 1 pixel ≈ 0.000471 m²
Minimum sensible structure: a small shed might be ~4 m² ≈ 8500 pixels
Noise floor: model artefacts are usually < 50 pixels contiguous
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import torch
    _TORCH_OK = True
except ImportError:
    _TORCH_OK = False

try:
    from scipy import ndimage as ndi
    from scipy.ndimage import label as cc_label
    _SCIPY_OK = True
except ImportError:
    _SCIPY_OK = False

# ── Constants ─────────────────────────────────────────────────────────────────
BUILDING_CLASS_ID = 4
NUM_CLASSES       = 6
PATCH_SIZE        = 512
TILE_SIZE         = 2048

# Pixel area at ~2.17 cm/px resolution
# Actual pixel size from raster metadata — use 0.02169 m/px (derived from Phase 1)
DEFAULT_PX_SIZE_M = 0.02169   # metres per pixel (square pixel assumed)
DEFAULT_PX_AREA_M2 = DEFAULT_PX_SIZE_M ** 2   # ≈ 4.7e-4 m² per pixel

# Min-area thresholds for sensitivity comparison
MIN_AREA_THRESHOLDS_M2 = [2.0, 5.0, 10.0]

# Morphological structuring element for noise removal
MORPH_OPEN_RADIUS = 2    # pixels — removes thin spurs and isolated noise
MORPH_CLOSE_RADIUS = 3   # pixels — closes small gaps inside buildings

# ImageNet normalisation (must match training)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class BuildingComponent:
    """A single connected building region extracted from one tile."""
    tile_id:         str
    component_id:    int                     # within-tile label index
    pixel_contour:   np.ndarray              # (N, 2) array of (col, row) pixel coords
    pixel_area:      float                   # pixels²
    area_m2:         float                   # approximate m²
    mean_confidence: float                   # mean softmax P(Building) over mask
    median_confidence: float                 # median softmax P(Building) over mask
    bbox_pixel:      Tuple[int,int,int,int]  # (col_min, row_min, col_max, row_max)
    has_hole:        bool = False            # whether interior holes were detected
    was_watershed:   bool = False            # split from larger component by watershed


@dataclass
class TileExtractionResult:
    """All building components extracted from one tile."""
    tile_id:            str
    raw_components:     int    # after cc_label, before any filtering
    filtered_components: int   # after min-area filter
    components:         List[BuildingComponent]
    mask_building_pixels: int  # total building pixels in raw mask
    watershed_splits:   int = 0
    min_area_m2:        float = 5.0


# ── Inference on one tile ─────────────────────────────────────────────────────

def run_inference_tile(
    model,
    rgb_path: Path,
    device,
    patch_size: int = PATCH_SIZE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run model over a full 2048×2048 tile patch-by-patch.

    Returns:
        pred_mask:    (H, W) uint8  — argmax class index
        prob_building: (H, W) float32 — softmax P(class=4) per pixel
    """
    if not _TORCH_OK:
        raise ImportError("torch required")

    import torch
    import torch.nn.functional as F
    import rasterio
    from rasterio.windows import Window

    n = TILE_SIZE // patch_size
    pred_patches   = []
    prob_patches   = []

    model.eval()
    with torch.no_grad():
        for row in range(n):
            for col in range(n):
                row_off = row * patch_size
                col_off = col * patch_size
                window  = Window(col_off=col_off, row_off=row_off,
                                 width=patch_size, height=patch_size)
                with rasterio.open(str(rgb_path)) as src:
                    rgb = src.read(indexes=[1, 2, 3], window=window).astype(np.float32)
                rgb /= 255.0
                for c in range(3):
                    rgb[c] = (rgb[c] - _MEAN[c]) / _STD[c]
                img = torch.from_numpy(rgb).float().unsqueeze(0).to(device)

                logits = model(img)                          # (1, 6, H, W)
                probs  = torch.softmax(logits, dim=1)        # (1, 6, H, W)
                pred   = torch.argmax(logits, dim=1)[0]      # (H, W)
                prob_b = probs[0, BUILDING_CLASS_ID, :, :]   # (H, W)

                pred_patches.append(pred.cpu().numpy().astype(np.uint8))
                prob_patches.append(prob_b.cpu().numpy().astype(np.float32))

    # Stitch patches
    rows_pred = []
    rows_prob = []
    for r in range(n):
        row_p = np.concatenate(pred_patches[r*n:(r+1)*n], axis=1)
        row_b = np.concatenate(prob_patches[r*n:(r+1)*n], axis=1)
        rows_pred.append(row_p)
        rows_prob.append(row_b)
    pred_mask    = np.concatenate(rows_pred, axis=0)   # (2048,2048) uint8
    prob_building = np.concatenate(rows_prob, axis=0)  # (2048,2048) float32
    return pred_mask, prob_building


# ── Mask → components ─────────────────────────────────────────────────────────

def _disk(radius: int) -> np.ndarray:
    """Create a circular structuring element of given radius."""
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    return (x**2 + y**2 <= radius**2).astype(np.uint8)


def extract_building_components(
    tile_id: str,
    pred_mask: np.ndarray,
    prob_building: np.ndarray,
    min_area_m2: float = 5.0,
    px_size_m: float = DEFAULT_PX_SIZE_M,
    use_watershed: bool = True,
    simplify_px: float = 1.5,
) -> TileExtractionResult:
    """
    Extract individual building components from a segmentation mask.

    Args:
        tile_id:       Source tile identifier
        pred_mask:     (H, W) uint8 — argmax class prediction
        prob_building: (H, W) float32 — softmax P(Building)
        min_area_m2:   Minimum building area in m² (default 5.0)
        px_size_m:     Pixel size in metres
        use_watershed: Whether to attempt watershed separation
        simplify_px:   Polygon simplification tolerance in pixels

    Returns:
        TileExtractionResult
    """
    if not _SCIPY_OK:
        raise ImportError("scipy required: pip install scipy")

    px_area = px_size_m ** 2
    min_px  = max(1, int(min_area_m2 / px_area))   # min pixels per component

    # 1. Binary building mask
    bld_mask = (pred_mask == BUILDING_CLASS_ID).astype(np.uint8)
    total_bld_px = int(bld_mask.sum())

    # 2. Morphological cleaning
    se_open  = _disk(MORPH_OPEN_RADIUS)
    se_close = _disk(MORPH_CLOSE_RADIUS)
    bld_mask = ndi.binary_opening(bld_mask,  structure=se_open).astype(np.uint8)
    bld_mask = ndi.binary_closing(bld_mask, structure=se_close).astype(np.uint8)

    # 3. Connected-component labelling (8-connectivity)
    struct = np.ones((3, 3), dtype=np.int32)
    labeled, n_components = cc_label(bld_mask, structure=struct)
    raw_components = n_components

    # 4. Optional watershed separation of touching buildings
    watershed_splits = 0
    if use_watershed and n_components > 0:
        labeled, watershed_splits = _watershed_separation(bld_mask, labeled, n_components)
        n_components = labeled.max()

    # 5. Extract per-component polygons
    components: List[BuildingComponent] = []
    comp_idx = 0

    for label_val in range(1, n_components + 1):
        comp_mask = (labeled == label_val)
        px_count  = int(comp_mask.sum())
        if px_count < min_px:
            continue

        area_m2 = px_count * px_area

        # Mean/median confidence from probability map
        probs_in_comp  = prob_building[comp_mask]
        mean_conf      = float(np.mean(probs_in_comp))
        median_conf    = float(np.median(probs_in_comp))

        # Bounding box
        rows, cols = np.where(comp_mask)
        r_min, r_max = int(rows.min()), int(rows.max())
        c_min, c_max = int(cols.min()), int(cols.max())

        # Contour extraction using marching squares / border tracing
        contour = _extract_contour(comp_mask, simplify_px=simplify_px)
        if contour is None or len(contour) < 4:
            continue

        components.append(BuildingComponent(
            tile_id=tile_id,
            component_id=comp_idx,
            pixel_contour=contour,
            pixel_area=float(px_count),
            area_m2=area_m2,
            mean_confidence=mean_conf,
            median_confidence=median_conf,
            bbox_pixel=(c_min, r_min, c_max, r_max),
            was_watershed=(label_val > raw_components),
        ))
        comp_idx += 1

    return TileExtractionResult(
        tile_id=tile_id,
        raw_components=raw_components,
        filtered_components=len(components),
        components=components,
        mask_building_pixels=total_bld_px,
        watershed_splits=watershed_splits,
        min_area_m2=min_area_m2,
    )


def _watershed_separation(
    bld_mask: np.ndarray,
    labeled: np.ndarray,
    n_components: int,
) -> Tuple[np.ndarray, int]:
    """
    Apply distance-transform watershed to separate touching buildings.
    Only applied to components larger than 5000 px (>2.3 m²) that may be merges.
    Returns updated labeled array and count of new splits.
    """
    try:
        from scipy.ndimage import distance_transform_edt
        from skimage.segmentation import watershed
        from skimage.feature import peak_local_max
    except ImportError:
        return labeled, 0

    splits = 0
    new_labeled = labeled.copy()
    next_label  = n_components + 1

    for lv in range(1, n_components + 1):
        comp = (labeled == lv)
        px   = int(comp.sum())
        # Only attempt watershed on large components (>10000 px ≈ 4.7 m²)
        if px < 10000:
            continue

        # Distance transform within component
        dist = distance_transform_edt(comp)
        # Find local maxima — each peak is a candidate building centre
        coords = peak_local_max(
            dist,
            min_distance=20,      # ~0.43 m apart — one roof apart
            labels=comp,
            exclude_border=False,
        )
        if len(coords) <= 1:
            continue   # single building or can't separate

        # Create markers
        markers = np.zeros_like(labeled)
        for idx, (r, c) in enumerate(coords, start=1):
            markers[r, c] = idx

        # Watershed segmentation within the component mask
        ws = watershed(-dist, markers, mask=comp)

        # Replace original label with watershed sub-labels
        sub_labels = np.unique(ws[ws > 0])
        if len(sub_labels) <= 1:
            continue

        for sl in sub_labels:
            if sl == 1:
                new_labeled[ws == sl] = lv     # reuse original label for first segment
            else:
                new_labeled[ws == sl] = next_label
                next_label += 1
                splits += 1

    return new_labeled, splits


def _extract_contour(
    comp_mask: np.ndarray,
    simplify_px: float = 1.5,
) -> Optional[np.ndarray]:
    """
    Extract outer contour of a binary mask component.
    Returns (N, 2) array of (col, row) pixel coords, or None if extraction fails.

    Uses skimage.measure.find_contours (marching squares).
    Falls back to bounding-box if unavailable.
    """
    try:
        from skimage.measure import find_contours, approximate_polygon
    except ImportError:
        # Fallback: use bounding box as polygon
        rows, cols = np.where(comp_mask)
        if len(rows) == 0:
            return None
        r0, r1 = rows.min(), rows.max()
        c0, c1 = cols.min(), cols.max()
        return np.array([[c0,r0],[c1,r0],[c1,r1],[c0,r1],[c0,r0]])

    # Pad by 1 pixel so contours on edges are found
    padded = np.pad(comp_mask, 1, constant_values=0)
    contours = find_contours(padded.astype(float), level=0.5)
    if not contours:
        return None

    # Use the longest contour (outer boundary)
    contour = max(contours, key=len)

    # Subtract the padding offset: contour is (row, col) in padded coords
    # → subtract 1 and swap to (col, row) for consistency
    contour = contour - 1                       # remove pad offset, still (row, col)

    # Simplify
    if simplify_px > 0 and len(contour) > 6:
        contour = approximate_polygon(contour, tolerance=simplify_px)

    # Convert to (col, row) = (x, y) order
    contour_xy = contour[:, ::-1].copy()        # now (col, row)

    # Ensure the polygon is closed
    if not np.allclose(contour_xy[0], contour_xy[-1]):
        contour_xy = np.vstack([contour_xy, contour_xy[0]])

    return contour_xy


# ── Min-area sensitivity analysis ────────────────────────────────────────────

def min_area_sensitivity(
    tile_id: str,
    pred_mask: np.ndarray,
    prob_building: np.ndarray,
    px_size_m: float = DEFAULT_PX_SIZE_M,
) -> dict:
    """
    Run extraction at three min-area thresholds and report component counts.
    Used to document the chosen threshold decision.
    """
    results = {}
    for threshold in MIN_AREA_THRESHOLDS_M2:
        res = extract_building_components(
            tile_id=tile_id,
            pred_mask=pred_mask,
            prob_building=prob_building,
            min_area_m2=threshold,
            px_size_m=px_size_m,
            use_watershed=False,   # speed — no watershed for sensitivity test
            simplify_px=1.5,
        )
        results[f"{threshold}m2"] = res.filtered_components
    return results
