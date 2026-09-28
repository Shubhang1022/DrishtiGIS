"""
U-Net with ResNet18 encoder for DrishtiGIS building segmentation.

Architecture:
  Encoder: ResNet18 (torchvision) — 4 feature levels
  Decoder: symmetric U-Net decoder with skip connections
  Output:  (B, num_classes, H, W) — dense per-pixel class logits

Input:  (B, 3, H, W) float32 — normalised RGB
Output: (B, 6, H, W) float32 — raw logits for 6 UAVPal classes

Final building mask: argmax(output, dim=1) == 4

Requires: torch, torchvision
Does NOT require: segmentation-models-pytorch, timm, or any other external library.
"""
from __future__ import annotations
from typing import List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from torchvision.models import resnet18, ResNet18_Weights
    _TORCHVISION_OK = True
except ImportError:
    _TORCHVISION_OK = False


# ── Decoder building blocks ──────────────────────────────────────────────────

class DoubleConv(nn.Module):
    """Two sequential (Conv → BN → ReLU) blocks — standard U-Net decoder unit."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class DecoderBlock(nn.Module):
    """
    U-Net decoder block: bilinear upsample → concatenate skip → DoubleConv.

    Uses bilinear upsampling instead of transposed convolution to avoid
    checkerboard artefacts and reduce parameter count.
    """

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up   = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        self.conv = DoubleConv(in_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        # Crop skip if spatial dims differ (handles odd-sized inputs gracefully)
        if x.shape != skip.shape:
            skip = skip[:, :, : x.shape[2], : x.shape[3]]
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


# ── Main model ───────────────────────────────────────────────────────────────

class UNetResNet18(nn.Module):
    """
    U-Net with ResNet18 encoder for 6-class UAVPal semantic segmentation.

    Encoder feature channels (ResNet18):
      layer0 (stem)  : 64   @ H/2  × W/2
      layer1         : 64   @ H/4  × W/4
      layer2         : 128  @ H/8  × W/8
      layer3         : 256  @ H/16 × W/16
      layer4 (bridge): 512  @ H/32 × W/32

    Decoder output channels: 256 → 128 → 64 → 32
    Segmentation head: Conv 1×1 → num_classes
    """

    def __init__(
        self,
        num_classes: int = 6,
        pretrained: bool = False,
    ) -> None:
        super().__init__()

        if not _TORCHVISION_OK:
            raise ImportError("torchvision is required. Install: pip install torchvision")

        self.num_classes = num_classes

        # ── Encoder (ResNet18 backbone) ─────────────────────────────────────
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        backbone = resnet18(weights=weights)

        # Split backbone into feature-extraction stages
        self.enc0 = nn.Sequential(
            backbone.conv1,     # (B, 64, H/2, W/2)
            backbone.bn1,
            backbone.relu,
        )
        self.pool  = backbone.maxpool  # (B, 64, H/4, W/4)
        self.enc1  = backbone.layer1   # (B,  64, H/4,  W/4)
        self.enc2  = backbone.layer2   # (B, 128, H/8,  W/8)
        self.enc3  = backbone.layer3   # (B, 256, H/16, W/16)
        self.enc4  = backbone.layer4   # (B, 512, H/32, W/32)  ← bottleneck

        # ── Decoder ─────────────────────────────────────────────────────────
        # dec4: upsample from H/32 → H/16, concat with enc3 (256)
        self.dec4 = DecoderBlock(in_channels=512, skip_channels=256, out_channels=256)
        # dec3: upsample from H/16 → H/8,  concat with enc2 (128)
        self.dec3 = DecoderBlock(in_channels=256, skip_channels=128, out_channels=128)
        # dec2: upsample from H/8  → H/4,  concat with enc1 (64)
        self.dec2 = DecoderBlock(in_channels=128, skip_channels=64,  out_channels=64)
        # dec1: upsample from H/4  → H/2,  concat with enc0 (64)
        self.dec1 = DecoderBlock(in_channels=64,  skip_channels=64,  out_channels=32)
        # dec0: upsample from H/2  → H    (no skip, just upsample + conv)
        self.dec0 = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True),
            DoubleConv(32, 32),
        )

        # ── Segmentation head ────────────────────────────────────────────────
        self.head = nn.Conv2d(32, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, 3, H, W) — normalised RGB input

        Returns:
            logits: (B, num_classes, H, W) — raw per-class logits
        """
        # Encoder path
        s0 = self.enc0(x)          # (B, 64,  H/2,  W/2)
        s1 = self.enc1(self.pool(s0))  # (B, 64,  H/4,  W/4)
        s2 = self.enc2(s1)         # (B, 128, H/8,  W/8)
        s3 = self.enc3(s2)         # (B, 256, H/16, W/16)
        s4 = self.enc4(s3)         # (B, 512, H/32, W/32) ← bottleneck

        # Decoder path (with skip connections)
        d4 = self.dec4(s4, s3)     # (B, 256, H/16, W/16)
        d3 = self.dec3(d4, s2)     # (B, 128, H/8,  W/8)
        d2 = self.dec2(d3, s1)     # (B,  64, H/4,  W/4)
        d1 = self.dec1(d2, s0)     # (B,  32, H/2,  W/2)
        d0 = self.dec0(d1)         # (B,  32, H,    W)

        return self.head(d0)       # (B, num_classes, H, W)

    def predict_mask(self, x: torch.Tensor) -> torch.Tensor:
        """
        Run inference and return the argmax class mask.

        Returns:
            mask: (B, H, W) int64 — per-pixel class index
        """
        with torch.no_grad():
            logits = self.forward(x)
        return torch.argmax(logits, dim=1)

    def predict_building_mask(self, x: torch.Tensor) -> torch.Tensor:
        """
        Return a binary mask where True = Building (class 4).

        Returns:
            mask: (B, H, W) bool
        """
        from backend.ai.uavpal.classes import BUILDING_CLASS_ID
        return self.predict_mask(x) == BUILDING_CLASS_ID

    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def trainable_parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def build_model(num_classes: int = 6, pretrained: bool = False) -> UNetResNet18:
    """Convenience factory that matches the approved architecture."""
    return UNetResNet18(num_classes=num_classes, pretrained=pretrained)
