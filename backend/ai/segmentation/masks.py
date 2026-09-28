"""
Mask post-processing utilities for DrishtiGIS building segmentation.

Converts dense U-Net output into usable building masks.
Does NOT fabricate or guess — every polygon comes from real model output.

NOTE: Real inference output does not exist yet (Phase 2).
      These utilities are prepared for Phase 3 inference.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

from backend.ai.uavpal.classes import BUILDING_CLASS_ID, NUM_CLASSES


def logits_to_mask(logits: torch.Tensor) -> torch.Tensor:
    """
    Convert raw model output to per-pixel class indices.

    Args:
        logits: (B, C, H, W) or (C, H, W) float32

    Returns:
        mask: (B, H, W) or (H, W) int64
    """
    return torch.argmax(logits, dim=-3)   # works for both batched and single


def logits_to_building_binary(logits: torch.Tensor) -> torch.Tensor:
    """
    Convert raw logits to a binary building mask.

    Args:
        logits: (B, C, H, W) float32

    Returns:
        binary: (B, H, W) bool — True where predicted class == Building (4)
    """
    mask = logits_to_mask(logits)
    return mask == BUILDING_CLASS_ID


def building_confidence(logits: torch.Tensor) -> torch.Tensor:
    """
    Return per-pixel probability of the Building class (softmax score).

    Args:
        logits: (B, C, H, W) float32

    Returns:
        confidence: (B, H, W) float32 in [0, 1]
    """
    probs = torch.softmax(logits, dim=1)   # (B, C, H, W)
    return probs[:, BUILDING_CLASS_ID, :, :]   # (B, H, W)


def mask_to_numpy(mask: torch.Tensor) -> np.ndarray:
    """Convert a class mask tensor to a uint8 numpy array."""
    return mask.detach().cpu().numpy().astype(np.uint8)


def apply_confidence_threshold(
    logits: torch.Tensor,
    threshold: float = 0.5,
) -> torch.Tensor:
    """
    Return binary building mask using a confidence threshold on softmax probability.

    Pixels where P(Building) >= threshold are marked True.

    Args:
        logits:    (B, C, H, W) float32
        threshold: confidence threshold in [0, 1]

    Returns:
        mask: (B, H, W) bool
    """
    return building_confidence(logits) >= threshold


def colour_mask(class_mask: np.ndarray, palette: Optional[Dict[int, Tuple[int, int, int]]] = None) -> np.ndarray:
    """
    Convert a (H, W) class index array to an (H, W, 3) RGB colour image.

    Args:
        class_mask: (H, W) uint8
        palette:    dict mapping class_id → (R, G, B); defaults to UAVPal palette

    Returns:
        rgb: (H, W, 3) uint8
    """
    if palette is None:
        from backend.ai.uavpal.classes import COLOUR_PALETTE
        palette = COLOUR_PALETTE

    h, w = class_mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_id, colour in palette.items():
        rgb[class_mask == class_id] = colour
    return rgb


def stitch_patches(
    patches: List[np.ndarray],
    tile_size: int = 2048,
    patch_size: int = 512,
) -> np.ndarray:
    """
    Reassemble non-overlapping patches back into a full-tile mask.

    Args:
        patches:    List of (patch_size, patch_size) uint8 arrays, in row-major order
        tile_size:  Output tile size (default 2048)
        patch_size: Patch size (default 512)

    Returns:
        tile: (tile_size, tile_size) uint8
    """
    n = tile_size // patch_size
    assert len(patches) == n * n, f"Expected {n*n} patches, got {len(patches)}"
    rows = []
    for r in range(n):
        row = np.concatenate(patches[r * n: (r + 1) * n], axis=1)
        rows.append(row)
    return np.concatenate(rows, axis=0)
