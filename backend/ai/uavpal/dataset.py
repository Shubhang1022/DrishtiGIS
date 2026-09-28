"""
UAVPal patch-based dataset loader for DrishtiGIS.

Design:
  - Source tiles are 2048×2048 GeoTIFFs (EPSG:32643, uint8 RGB / uint8 label).
  - Each tile is sliced into non-overlapping 512×512 patches.
  - A RGB patch is never mixed with a label from a different tile.
  - Label values are preserved exactly (0–5); never normalised as image data.
  - Building class ID = 4 is preserved exactly.
  - RGB patches are normalised with ImageNet statistics (standard for ResNet18 encoder).

Usage:
    from backend.ai.uavpal.dataset import UAVPalDataset
    ds = UAVPalDataset(tile_ids=['00_05', '00_06'], rgb_dir=..., label_dir=...,
                       patch_size=512, augment=False)
    img_tensor, lbl_tensor = ds[0]   # img: (3,512,512) float32, lbl: (512,512) int64
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

# Rasterio import — graceful error if not installed
try:
    import rasterio
    from rasterio.windows import Window
    _RASTERIO_OK = True
except ImportError:
    _RASTERIO_OK = False

from backend.ai.uavpal.classes import (
    NUM_CLASSES,
    VALID_CLASS_IDS,
    BUILDING_CLASS_ID,
)

# ImageNet normalisation constants (standard for ResNet18 pretrained weights)
_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

TILE_SIZE   = 2048
PATCH_SIZE  = 512
PATCHES_PER_AXIS = TILE_SIZE // PATCH_SIZE   # 4
PATCHES_PER_TILE = PATCHES_PER_AXIS ** 2     # 16


def _check_rasterio() -> None:
    if not _RASTERIO_OK:
        raise ImportError(
            "rasterio is required for UAVPalDataset. "
            "Install it in the ML environment: pip install rasterio"
        )


class UAVPalDataset(Dataset):
    """
    Patch-based PyTorch Dataset over UAVPal tiles.

    Args:
        tile_ids:   List of tile IDs, e.g. ['00_05', '00_06']
        rgb_dir:    Path to directory containing RGB GeoTIFFs
        label_dir:  Path to directory containing label GeoTIFFs
        patch_size: Spatial size of each square patch (default 512)
        augment:    If True, apply random horizontal/vertical flip (same transform
                    applied to both image and label)
        seed:       Random seed for augmentation reproducibility
    """

    def __init__(
        self,
        tile_ids: List[str],
        rgb_dir: Path,
        label_dir: Path,
        patch_size: int = PATCH_SIZE,
        augment: bool = False,
        seed: int = 42,
    ) -> None:
        _check_rasterio()

        self.rgb_dir    = Path(rgb_dir)
        self.label_dir  = Path(label_dir)
        self.patch_size = patch_size
        self.augment    = augment
        self.rng        = random.Random(seed)

        patches_per_axis = TILE_SIZE // patch_size
        patches_per_tile = patches_per_axis ** 2

        # Build flat list of (tile_id, row_offset, col_offset) — one entry per patch
        self._index: List[Tuple[str, int, int]] = []
        for tile_id in tile_ids:
            rgb_path   = self.rgb_dir   / f"{tile_id}.tiff"
            label_path = self.label_dir / f"{tile_id}.tiff"
            if not rgb_path.exists():
                raise FileNotFoundError(f"RGB tile not found: {rgb_path}")
            if not label_path.exists():
                raise FileNotFoundError(f"Label tile not found: {label_path}")
            for row in range(patches_per_axis):
                for col in range(patches_per_axis):
                    self._index.append((tile_id, row * patch_size, col * patch_size))

        self._tile_ids = list(tile_ids)
        self._patches_per_tile = patches_per_tile

    # ── length ─────────────────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self._index)

    # ── single item ─────────────────────────────────────────────────────────
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        tile_id, row_off, col_off = self._index[idx]
        window = Window(col_off=col_off, row_off=row_off,
                        width=self.patch_size, height=self.patch_size)

        # ── load RGB patch ──────────────────────────────────────────────────
        rgb_path = self.rgb_dir / f"{tile_id}.tiff"
        with rasterio.open(str(rgb_path)) as src:
            # Read 3 bands: shape (3, H, W), dtype uint8
            rgb = src.read(indexes=[1, 2, 3], window=window).astype(np.float32)

        # Normalise to [0,1] then apply ImageNet stats
        rgb /= 255.0
        for c in range(3):
            rgb[c] = (rgb[c] - _IMAGENET_MEAN[c]) / _IMAGENET_STD[c]

        # ── load label patch ────────────────────────────────────────────────
        label_path = self.label_dir / f"{tile_id}.tiff"
        with rasterio.open(str(label_path)) as src:
            # Read single band: shape (1, H, W), dtype uint8
            lbl = src.read(indexes=[1], window=window)[0]   # (H, W)

        # Verify label values are valid — fail loudly, never silently corrupt
        unique_vals = set(np.unique(lbl).tolist())
        invalid = unique_vals - set(VALID_CLASS_IDS)
        if invalid:
            raise ValueError(
                f"Tile {tile_id} patch ({row_off},{col_off}) contains invalid "
                f"class values: {invalid}. Valid range: 0–{NUM_CLASSES - 1}"
            )

        # ── optional augmentation (spatial only, same transform for both) ───
        if self.augment:
            if self.rng.random() < 0.5:
                rgb = rgb[:, :, ::-1].copy()    # horizontal flip
                lbl = lbl[:, ::-1].copy()
            if self.rng.random() < 0.5:
                rgb = rgb[:, ::-1, :].copy()    # vertical flip
                lbl = lbl[::-1, :].copy()

        # ── convert to tensors ──────────────────────────────────────────────
        img_tensor = torch.from_numpy(rgb.copy()).float()       # (3, H, W) float32
        lbl_tensor = torch.from_numpy(lbl.copy()).long()        # (H, W) int64

        return img_tensor, lbl_tensor

    # ── utilities ───────────────────────────────────────────────────────────
    def tile_ids(self) -> List[str]:
        return list(self._tile_ids)

    def num_tiles(self) -> int:
        return len(self._tile_ids)

    def patches_per_tile(self) -> int:
        return self._patches_per_tile

    def get_patch_info(self, idx: int) -> dict:
        """Return metadata about a specific patch index."""
        tile_id, row_off, col_off = self._index[idx]
        return {
            "tile_id":   tile_id,
            "row_offset": row_off,
            "col_offset": col_off,
            "patch_size": self.patch_size,
        }

    @classmethod
    def from_config(
        cls,
        config: dict,
        split: str = "internal_train",
        augment: bool = False,
    ) -> "UAVPalDataset":
        """
        Construct a dataset from a training_config.json dict.

        Args:
            config: Parsed training_config.json
            split:  One of 'internal_train', 'validation', 'official_test'
            augment: Enable augmentation (only use for training split)
        """
        split_key_map = {
            "internal_train": "internal_train_tiles",
            "validation":     "validation_tiles",
            "official_test":  "official_test_tiles",
        }
        if split not in split_key_map:
            raise ValueError(f"Unknown split: {split!r}. Use one of {list(split_key_map)}")

        tile_ids  = config[split_key_map[split]]
        rgb_dir   = Path(config["rgb_dir"])
        label_dir = Path(config["label_dir"])
        patch_size = config.get("patch_size", PATCH_SIZE)
        seed       = config.get("random_seed", 42)

        return cls(
            tile_ids=tile_ids,
            rgb_dir=rgb_dir,
            label_dir=label_dir,
            patch_size=patch_size,
            augment=augment,
            seed=seed,
        )
