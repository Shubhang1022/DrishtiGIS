"""
Segmentation metrics for DrishtiGIS UAVPal evaluation.

Metrics computed:
  - Pixel accuracy (global)
  - Per-class IoU
  - Mean IoU
  - Building IoU (class 4)
  - Building precision, recall, F1

NOTE: Do NOT report these numbers until actual model training has occurred.
      Phase 2 only prepares the metric infrastructure.
"""
from __future__ import annotations
from typing import Dict, Optional
import torch
import numpy as np

from backend.ai.uavpal.classes import NUM_CLASSES, BUILDING_CLASS_ID, CLASS_BY_ID


class SegmentationMetrics:
    """
    Accumulates predictions over a dataset and computes segmentation metrics.

    Usage:
        metrics = SegmentationMetrics(num_classes=6)
        for pred, target in dataloader:
            metrics.update(pred, target)
        result = metrics.compute()
    """

    def __init__(self, num_classes: int = NUM_CLASSES) -> None:
        self.num_classes = num_classes
        # Confusion matrix: rows = true, cols = pred
        self._confusion = np.zeros((num_classes, num_classes), dtype=np.int64)

    def reset(self) -> None:
        self._confusion[:] = 0

    def update(
        self,
        predictions: torch.Tensor,   # (B, H, W) int64 — argmax of logits
        targets: torch.Tensor,        # (B, H, W) int64 — ground-truth labels
        ignore_index: Optional[int] = None,
    ) -> None:
        """Accumulate predictions into confusion matrix."""
        pred = predictions.detach().cpu().numpy().flatten()
        tgt  = targets.detach().cpu().numpy().flatten()

        if ignore_index is not None:
            mask = tgt != ignore_index
            pred = pred[mask]
            tgt  = tgt[mask]

        # Clamp to valid range to avoid index errors from bad inputs
        pred = np.clip(pred, 0, self.num_classes - 1)
        tgt  = np.clip(tgt,  0, self.num_classes - 1)

        for t, p in zip(tgt, pred):
            self._confusion[t, p] += 1

    def compute(self) -> Dict[str, float]:
        """Compute all metrics from accumulated confusion matrix."""
        cm = self._confusion.astype(np.float64)

        # Pixel accuracy
        total   = cm.sum()
        correct = np.diag(cm).sum()
        pixel_accuracy = float(correct / total) if total > 0 else 0.0

        # Per-class IoU
        iou_per_class: Dict[str, float] = {}
        for c in range(self.num_classes):
            tp  = cm[c, c]
            fp  = cm[:, c].sum() - tp
            fn  = cm[c, :].sum() - tp
            denom = tp + fp + fn
            iou   = float(tp / denom) if denom > 0 else 0.0
            class_name = CLASS_BY_ID[c].name if c in CLASS_BY_ID else str(c)
            iou_per_class[class_name] = round(iou, 6)

        mean_iou = float(np.mean(list(iou_per_class.values())))

        # Building-specific (class 4)
        c = BUILDING_CLASS_ID
        bld_tp  = cm[c, c]
        bld_fp  = cm[:, c].sum() - bld_tp
        bld_fn  = cm[c, :].sum() - bld_tp

        bld_precision = float(bld_tp / (bld_tp + bld_fp)) if (bld_tp + bld_fp) > 0 else 0.0
        bld_recall    = float(bld_tp / (bld_tp + bld_fn)) if (bld_tp + bld_fn) > 0 else 0.0
        bld_f1 = (
            2 * bld_precision * bld_recall / (bld_precision + bld_recall)
            if (bld_precision + bld_recall) > 0 else 0.0
        )
        bld_iou = iou_per_class.get("Building", 0.0)

        return {
            "pixel_accuracy":       round(pixel_accuracy, 6),
            "mean_iou":             round(mean_iou, 6),
            "iou_per_class":        iou_per_class,
            "building_iou":         round(bld_iou, 6),
            "building_precision":   round(bld_precision, 6),
            "building_recall":      round(bld_recall, 6),
            "building_f1":          round(bld_f1, 6),
        }
