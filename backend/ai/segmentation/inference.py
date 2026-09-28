"""
Inference utilities for DrishtiGIS building segmentation.

Runs a trained U-Net over a full 2048×2048 tile using patch-based sliding window.
Does NOT run until a trained model checkpoint exists (Phase 3+).

NOTE: Do NOT use these to produce AI polygons until Phase 3 training is complete
      and the model has been evaluated. The demo polygons in
      drishtigis/lib/demo-data/bhopal-ai-features.geojson must remain clearly
      labelled as DEMO until replaced by real model output.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Union

import numpy as np
import torch

from backend.ai.segmentation.model import UNetResNet18, build_model
from backend.ai.segmentation.masks import logits_to_mask, stitch_patches, mask_to_numpy
from backend.ai.uavpal.classes import NUM_CLASSES, BUILDING_CLASS_ID

# ImageNet normalisation — must match training
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

TILE_SIZE  = 2048
PATCH_SIZE = 512


def _load_rgb_patch(rgb_path: Path, row_off: int, col_off: int, patch_size: int) -> torch.Tensor:
    """Load and normalise a single RGB patch from a GeoTIFF."""
    try:
        import rasterio
        from rasterio.windows import Window
    except ImportError:
        raise ImportError("rasterio is required for inference: pip install rasterio")

    window = Window(col_off=col_off, row_off=row_off, width=patch_size, height=patch_size)
    with rasterio.open(str(rgb_path)) as src:
        rgb = src.read(indexes=[1, 2, 3], window=window).astype(np.float32)
    rgb /= 255.0
    for c in range(3):
        rgb[c] = (rgb[c] - _MEAN[c]) / _STD[c]
    return torch.from_numpy(rgb).float()   # (3, H, W)


def run_tile_inference(
    model: UNetResNet18,
    rgb_path: Union[str, Path],
    patch_size: int = PATCH_SIZE,
    device: Optional[torch.device] = None,
    confidence_threshold: Optional[float] = None,
) -> np.ndarray:
    """
    Run inference over a full tile using patch-based sliding window.

    Args:
        model:                Trained UNetResNet18 (must be in eval mode)
        rgb_path:             Path to a 2048×2048 RGB GeoTIFF
        patch_size:           Patch size (must match training)
        device:               torch device (defaults to CPU)
        confidence_threshold: If set, threshold P(Building) instead of argmax

    Returns:
        mask: (TILE_SIZE, TILE_SIZE) uint8 — per-pixel class index
              (or binary uint8 if confidence_threshold is set)
    """
    rgb_path = Path(rgb_path)
    if not rgb_path.exists():
        raise FileNotFoundError(f"RGB tile not found: {rgb_path}")

    if device is None:
        device = torch.device("cpu")

    model = model.to(device)
    model.eval()

    n = TILE_SIZE // patch_size
    patches_out = []

    with torch.no_grad():
        for row in range(n):
            for col in range(n):
                row_off = row * patch_size
                col_off = col * patch_size
                img = _load_rgb_patch(rgb_path, row_off, col_off, patch_size)
                img = img.unsqueeze(0).to(device)          # (1, 3, H, W)
                logits = model(img)                         # (1, C, H, W)

                if confidence_threshold is not None:
                    from backend.ai.segmentation.masks import apply_confidence_threshold
                    patch_mask = apply_confidence_threshold(logits, confidence_threshold)
                    patch_np = patch_mask[0].cpu().numpy().astype(np.uint8)
                else:
                    patch_mask = logits_to_mask(logits)    # (1, H, W)
                    patch_np = mask_to_numpy(patch_mask[0])

                patches_out.append(patch_np)

    return stitch_patches(patches_out, tile_size=TILE_SIZE, patch_size=patch_size)


def load_checkpoint(checkpoint_path: Union[str, Path], num_classes: int = NUM_CLASSES) -> UNetResNet18:
    """
    Load a trained model from a checkpoint file.

    Args:
        checkpoint_path: Path to .pt or .pth checkpoint
        num_classes:     Number of output classes (must match training)

    Returns:
        model: UNetResNet18 in eval mode
    """
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path}\n"
            "No model has been trained yet (Phase 3 not started)."
        )
    model = build_model(num_classes=num_classes, pretrained=False)
    state = torch.load(str(checkpoint_path), map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model
