"""
DrishtiGIS Phase 3 — Full UAVPal segmentation training loop.

Entry points:
  run_smoke_test(config_path)  — 1-batch sanity check (Phase 2)
  run_pilot(config_path, epochs=10) — short pilot run
  run_training(config_path)     — full training with early stopping

Checkpoints saved to: data/ai_models/uavpal/
  best_model.pth    — best validation Building IoU
  latest_model.pth  — most recent epoch

Class weights: median-frequency from data/uavpal/class_distribution.json
  Water (class 1) absent in training tiles → weight = 0
  Car   (class 3) rare                     → weight capped at 10
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# ── Force UTF-8 output ────────────────────────────────────────────────────────
if hasattr(sys.stdout, 'reconfigure') and callable(getattr(sys.stdout, 'reconfigure', None)):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure') and callable(getattr(sys.stderr, 'reconfigure', None)):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.ai.segmentation.model import build_model
from backend.ai.segmentation.validation import SegmentationMetrics
from backend.ai.uavpal.dataset import UAVPalDataset
from backend.ai.uavpal.classes import NUM_CLASSES, BUILDING_CLASS_ID, CLASS_BY_ID


# ── Loss ─────────────────────────────────────────────────────────────────────

class CrossEntropyDiceLoss(nn.Module):
    """
    Combined Cross-Entropy + Soft Dice loss.
    class_weights: tensor of shape (num_classes,) for CE; also used to zero
                   Dice contribution for absent classes.
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        class_weights: Optional[torch.Tensor] = None,
        ce_weight: float = 0.5,
        dice_weight: float = 0.5,
        smooth: float = 1.0,
    ) -> None:
        super().__init__()
        self.num_classes  = num_classes
        self.ce_weight    = ce_weight
        self.dice_weight  = dice_weight
        self.smooth       = smooth
        self.register_buffer('class_weights', class_weights)
        self.ce = nn.CrossEntropyLoss(
            weight=class_weights,
            ignore_index=-100,
        )

    def dice_loss(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs   = torch.softmax(logits, dim=1)            # (B, C, H, W)
        one_hot = torch.zeros_like(probs)
        one_hot.scatter_(1, targets.unsqueeze(1), 1.0)   # (B, C, H, W)

        # Per-class soft Dice summed over spatial + batch dims
        inter = (probs * one_hot).sum(dim=(0, 2, 3))     # (C,)
        union = (probs + one_hot).sum(dim=(0, 2, 3))     # (C,)
        dice  = 1.0 - (2.0 * inter + self.smooth) / (union + self.smooth)  # (C,)

        # Zero out absent classes (weight == 0) to avoid learning from them
        if self.class_weights is not None:
            w = self.class_weights.to(dice.device)
            mask = w > 0
            if mask.any():
                dice = dice[mask]
        return dice.mean()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_loss   = self.ce(logits, targets)
        dice_loss = self.dice_loss(logits, targets)
        return self.ce_weight * ce_loss + self.dice_weight * dice_loss


# ── RAM monitor ───────────────────────────────────────────────────────────────

def ram_used_gb() -> float:
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1e9
    except ImportError:
        return -1.0


# ── Epoch runner ─────────────────────────────────────────────────────────────

def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: Optional[torch.optim.Optimizer],
    device: torch.device,
    is_train: bool,
    grad_accum_steps: int = 1,
) -> Tuple[float, SegmentationMetrics]:
    """Run one full epoch. Returns (mean_loss, metrics_accumulator)."""
    model.train(is_train)
    metrics = SegmentationMetrics(num_classes=NUM_CLASSES)
    total_loss = 0.0
    n_batches  = 0

    ctx = torch.enable_grad() if is_train else torch.no_grad()
    with ctx:
        for step, (imgs, lbls) in enumerate(loader):
            imgs = imgs.to(device)
            lbls = lbls.to(device)

            logits = model(imgs)
            loss   = criterion(logits, lbls)

            if is_train:
                (loss / grad_accum_steps).backward()
                if (step + 1) % grad_accum_steps == 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    optimizer.zero_grad()

            total_loss += loss.item()
            n_batches  += 1

            preds = torch.argmax(logits, dim=1)
            metrics.update(preds, lbls)

    mean_loss = total_loss / max(n_batches, 1)
    return mean_loss, metrics


# ── Main training function ────────────────────────────────────────────────────

def run_training(
    config_path: str = "data/uavpal/training_config.json",
    max_epochs: Optional[int] = None,
    pilot_epochs: Optional[int] = None,   # if set, only run this many epochs
    checkpoint_dir: str = "data/ai_models/uavpal",
    resume_from: Optional[str] = None,    # path to checkpoint .pth to resume from
) -> dict:
    """
    Full training loop.

    Args:
        config_path:     Path to training_config.json
        max_epochs:      Override max_epochs from config (None = use config value)
        pilot_epochs:    If set, run only this many epochs (pilot mode)
        checkpoint_dir:  Directory to save model checkpoints

    Returns:
        dict with training history and best metrics
    """
    # ── Setup ─────────────────────────────────────────────────────────────────
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    SEED        = cfg["random_seed"]
    PATCH_SIZE  = cfg["patch_size"]
    BATCH_SIZE  = cfg["batch_size"]
    LR          = cfg["learning_rate"]
    WD          = cfg["weight_decay"]
    N_EPOCHS    = pilot_epochs if pilot_epochs else (max_epochs or cfg["max_epochs"])
    PATIENCE    = cfg["early_stopping_patience"]
    RGB_DIR     = Path(cfg["rgb_dir"])
    LABEL_DIR   = Path(cfg["label_dir"])
    CKPT_DIR    = Path(checkpoint_dir)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)

    device = torch.device("cpu")
    print(f"Device: {device}")
    print(f"Epochs: {N_EPOCHS}  BS: {BATCH_SIZE}  LR: {LR}  Patch: {PATCH_SIZE}")
    print(f"Train tiles: {len(cfg['internal_train_tiles'])}  "
          f"Val tiles: {len(cfg['validation_tiles'])}")

    # ── Class weights ─────────────────────────────────────────────────────────
    dist_path = "data/uavpal/class_distribution.json"
    if Path(dist_path).exists():
        with open(dist_path, encoding="utf-8") as f:
            dist = json.load(f)
        raw_w = [dist["per_class_weights"][str(c)] for c in range(NUM_CLASSES)]
        class_weights = torch.tensor(raw_w, dtype=torch.float32)
        print(f"Class weights: {[round(w,3) for w in raw_w]}")
    else:
        class_weights = None
        print("No class distribution file — training without class weights")

    # ── Datasets ──────────────────────────────────────────────────────────────
    train_ds = UAVPalDataset(
        tile_ids=cfg["internal_train_tiles"],
        rgb_dir=RGB_DIR, label_dir=LABEL_DIR,
        patch_size=PATCH_SIZE, augment=True, seed=SEED,
    )
    val_ds = UAVPalDataset(
        tile_ids=cfg["validation_tiles"],
        rgb_dir=RGB_DIR, label_dir=LABEL_DIR,
        patch_size=PATCH_SIZE, augment=False, seed=SEED,
    )
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=0, pin_memory=False)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=0, pin_memory=False)
    print(f"Train patches: {len(train_ds)}  Val patches: {len(val_ds)}")

    # ── Model ─────────────────────────────────────────────────────────────────
    model     = build_model(num_classes=NUM_CLASSES, pretrained=False).to(device)

    # Resume from checkpoint if specified
    if resume_from and Path(resume_from).exists():
        state = torch.load(str(resume_from), map_location=device, weights_only=True)
        model.load_state_dict(state)
        print(f"Resumed from checkpoint: {resume_from}")
    elif resume_from:
        print(f"WARNING: resume checkpoint not found: {resume_from} — starting fresh")

    criterion = CrossEntropyDiceLoss(
        num_classes=NUM_CLASSES,
        class_weights=class_weights.to(device) if class_weights is not None else None,
        ce_weight=cfg.get("ce_weight", 0.5),
        dice_weight=cfg.get("dice_weight", 0.5),
    )
    optimizer = torch.optim.Adam(
        model.parameters(), lr=LR, weight_decay=WD
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=5
    )

    # ── Training loop ─────────────────────────────────────────────────────────
    history: List[dict] = []
    best_bld_iou       = -1.0
    best_epoch         = -1
    epochs_no_improve  = 0
    start_ts = time.time()
    GRAD_ACCUM = 4   # effective batch = 2 * 4 = 8 — safe for 7.7 GB RAM

    print()
    print("=" * 70)
    print(f"{'Ep':>3}  {'T-Loss':>8}  {'V-Loss':>8}  "
          f"{'V-BldIoU':>9}  {'V-mIoU':>8}  {'RAM GB':>7}  {'Time s':>7}")
    print("=" * 70)

    optimizer.zero_grad()

    for epoch in range(1, N_EPOCHS + 1):
        ep_start = time.time()

        # Train
        train_loss, _ = run_epoch(
            model, train_loader, criterion, optimizer,
            device, is_train=True, grad_accum_steps=GRAD_ACCUM,
        )

        # Validate
        val_loss, val_metrics = run_epoch(
            model, val_loader, criterion, None,
            device, is_train=False,
        )
        val_result  = val_metrics.compute()
        bld_iou     = val_result["building_iou"]
        mean_iou    = val_result["mean_iou"]
        bld_f1      = val_result["building_f1"]
        ep_time     = time.time() - ep_start
        ram_gb      = ram_used_gb()

        scheduler.step(bld_iou)

        print(f"{epoch:>3}  {train_loss:>8.4f}  {val_loss:>8.4f}  "
              f"{bld_iou:>9.4f}  {mean_iou:>8.4f}  "
              f"{ram_gb:>7.2f}  {ep_time:>7.1f}")

        ep_record = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss":   round(val_loss,   6),
            "val_building_iou": round(bld_iou,  6),
            "val_mean_iou":     round(mean_iou, 6),
            "val_building_f1":  round(bld_f1,   6),
            "val_pixel_accuracy": round(val_result["pixel_accuracy"], 6),
            "val_building_precision": round(val_result["building_precision"], 6),
            "val_building_recall":    round(val_result["building_recall"],    6),
            "epoch_time_s": round(ep_time, 2),
            "ram_gb": round(ram_gb, 3),
            "lr": optimizer.param_groups[0]["lr"],
        }
        history.append(ep_record)

        # Checkpoint
        torch.save(model.state_dict(), str(CKPT_DIR / "latest_model.pth"))

        if bld_iou > best_bld_iou:
            best_bld_iou      = bld_iou
            best_epoch        = epoch
            epochs_no_improve = 0
            torch.save(model.state_dict(), str(CKPT_DIR / "best_model.pth"))
            print(f"    ** new best Building IoU={bld_iou:.4f} — checkpoint saved")
        else:
            epochs_no_improve += 1
            if not pilot_epochs and epochs_no_improve >= PATIENCE:
                print(f"\nEarly stopping at epoch {epoch} "
                      f"(no improvement for {PATIENCE} epochs)")
                break

    total_time = time.time() - start_ts
    print("=" * 70)
    print(f"Training complete: {len(history)} epochs in {total_time:.0f}s")
    print(f"Best Building IoU: {best_bld_iou:.4f} at epoch {best_epoch}")

    result = {
        "epochs_run":       len(history),
        "total_time_s":     round(total_time, 1),
        "best_epoch":       best_epoch,
        "best_building_iou": round(best_bld_iou, 6),
        "history":          history,
        "config_path":      config_path,
        "checkpoint_dir":   str(CKPT_DIR),
    }

    # Save training history
    hist_path = CKPT_DIR / "training_history.json"
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"History saved: {hist_path}")

    return result


# ── Pilot run ─────────────────────────────────────────────────────────────────

def run_pilot(
    config_path: str = "data/uavpal/training_config.json",
    epochs: int = 10,
) -> dict:
    """Run a short pilot to assess epoch time and learning dynamics."""
    print(f"\nPILOT RUN — {epochs} epochs")
    print("=" * 70)
    return run_training(config_path, pilot_epochs=epochs)


# ── Smoke test (Phase 2 compatibility) ───────────────────────────────────────

def run_smoke_test(config_path: str = "data/uavpal/training_config.json") -> dict:
    """1-batch CPU sanity check — all 12 checks must pass."""
    results: dict = {}
    print("=" * 60)
    print("DrishtiGIS Phase 2/3 -- CPU Smoke Test")
    print("=" * 60)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    seed       = config["random_seed"]
    patch_size = config["patch_size"]
    num_classes = config["num_classes"]
    lr          = config["learning_rate"]

    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    results["config_loaded"] = True

    first_tile = config["internal_train_tiles"][0]
    ds = UAVPalDataset(
        tile_ids=[first_tile],
        rgb_dir=Path(config["rgb_dir"]),
        label_dir=Path(config["label_dir"]),
        patch_size=patch_size,
        augment=False, seed=seed,
    )
    results["dataset_created"] = True
    results["dataset_length"]  = len(ds)

    t0 = time.time()
    img, lbl = ds[0]
    results["pair_load_time_s"] = round(time.time() - t0, 3)

    results["check_pair_loaded"] = isinstance(img, torch.Tensor) and isinstance(lbl, torch.Tensor)
    results["check_img_shape"]   = tuple(img.shape) == (3, patch_size, patch_size)
    results["check_lbl_shape"]   = tuple(lbl.shape) == (patch_size, patch_size)
    results["img_shape"]         = list(img.shape)
    results["lbl_shape"]         = list(lbl.shape)

    unique_vals = lbl.unique().tolist()
    results["label_unique_values"] = [int(v) for v in unique_vals]
    results["check_label_values"]  = all(0 <= v <= 5 for v in unique_vals)

    print(f"  [1] Pair loaded     : {results['check_pair_loaded']}")
    print(f"  [2] Image shape     : {results['check_img_shape']}  {list(img.shape)}")
    print(f"  [3] Label shape     : {results['check_lbl_shape']}  {list(lbl.shape)}")
    print(f"  [5] Label values    : {results['check_label_values']}  {[int(v) for v in unique_vals]}")

    model = build_model(num_classes=num_classes, pretrained=False)
    model.train()
    results["model_parameter_count"] = model.parameter_count()

    img_batch = img.unsqueeze(0)
    lbl_batch = lbl.unsqueeze(0)

    try:
        t0     = time.time()
        logits = model(img_batch)
        results["forward_time_s"]     = round(time.time() - t0, 3)
        results["check_forward_pass"] = True
        results["output_shape"]       = list(logits.shape)
    except Exception as e:
        results["check_forward_pass"] = False
        print(f"  [7] Forward FAIL: {e}")
        return results

    results["check_output_channels"] = logits.shape[1] == num_classes
    results["check_spatial_dims"]    = (logits.shape[2] == patch_size and logits.shape[3] == patch_size)
    results["check_no_nan_inf_output"] = (
        not torch.isnan(logits).any().item() and not torch.isinf(logits).any().item()
    )

    print(f"  [4] Output channels : {results['check_output_channels']}  shape={list(logits.shape)}")
    print(f"  [6] Spatial dims    : {results['check_spatial_dims']}")
    print(f"  [7] Forward pass    : {results['check_forward_pass']}  ({results['forward_time_s']}s)")

    criterion = CrossEntropyDiceLoss(num_classes=num_classes)
    try:
        loss = criterion(logits, lbl_batch)
        results["loss_value"]          = round(loss.item(), 6)
        results["check_loss_computed"] = True
        results["check_no_nan_inf_loss"] = (
            not torch.isnan(loss).item() and not torch.isinf(loss).item()
        )
        print(f"  [8] Loss            : {results['loss_value']:.6f}")
    except Exception as e:
        results["check_loss_computed"] = False
        print(f"  [8] Loss FAIL: {e}")
        return results

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    optimizer.zero_grad()
    try:
        loss.backward()
        grad_norm = sum(
            p.grad.data.norm(2).item() ** 2
            for p in model.parameters() if p.grad is not None
        ) ** 0.5
        results["check_backward"] = True
        results["grad_norm"]      = round(grad_norm, 6)
        optimizer.step()
        results["check_optimizer_step"] = True
        print(f"  [9] Backward+step   : OK  grad_norm={grad_norm:.4f}")
    except Exception as e:
        results["check_backward"] = False
        print(f"  [9] Backward FAIL: {e}")

    all_checks = [
        results.get("check_pair_loaded"), results.get("check_img_shape"),
        results.get("check_lbl_shape"),   results.get("check_output_channels"),
        results.get("check_label_values"), results.get("check_spatial_dims"),
        results.get("check_forward_pass"), results.get("check_loss_computed"),
        results.get("check_backward"),     results.get("check_optimizer_step"),
        results.get("check_no_nan_inf_output"), results.get("check_no_nan_inf_loss"),
    ]
    results["all_checks_pass"] = all(bool(c) for c in all_checks)
    print()
    print(f"Smoke test: {'PASS' if results['all_checks_pass'] else 'FAIL'}")
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DrishtiGIS UAVPal training")
    parser.add_argument("--config",  default="data/uavpal/training_config.json")
    parser.add_argument("--mode",    choices=["smoke", "pilot", "full"], default="pilot")
    parser.add_argument("--epochs",  type=int, default=10)
    parser.add_argument("--ckpt-dir", default="data/ai_models/uavpal")
    parser.add_argument("--resume",  default=None, help="Path to checkpoint .pth to resume from")
    args = parser.parse_args()

    if args.mode == "smoke":
        result = run_smoke_test(args.config)
    elif args.mode == "pilot":
        result = run_pilot(args.config, epochs=args.epochs)
    else:
        result = run_training(args.config, checkpoint_dir=args.ckpt_dir,
                              resume_from=args.resume)

    print("\n=== RESULT ===")
    print(json.dumps(
        {k: v for k, v in result.items() if k != "history"},
        indent=2, ensure_ascii=False
    ))
