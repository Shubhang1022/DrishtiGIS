"""
DrishtiGIS Phase 2 — AI pipeline unit tests.

Covers:
  - Class mapping correctness (class IDs, names, building ID = 4)
  - RGB/label file pairing (filename must match)
  - Tile dimensions (2048×2048 required)
  - Label value integrity (only 0–5 allowed)
  - Train/validation/test separation (no leakage between splits)
  - Building class ID = 4 throughout the pipeline
  - Patch extraction (correct shape, no cross-tile mixing)
  - Model output shape (B, 6, H, W)
  - Training config consistency
  - Validation split integrity

Runs with pytest. Uses the ML venv's Python if torch is not available in the
pytest process — gracefully skips model tests rather than hard-failing.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.parent.parent
CONF_PATH    = ROOT / "data/uavpal/training_config.json"
SPLIT_PATH   = ROOT / "data/uavpal/validation_split.json"
RGB_DIR      = ROOT / "Dataset/geospatial-data/BHOPAL"
LABEL_DIR    = ROOT / "data/uavpal/annotations/Label/Tiles"
MANIFEST_PATH = ROOT / "data/uavpal/annotations/annotation_manifest.json"

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def config():
    assert CONF_PATH.exists(), f"training_config.json not found: {CONF_PATH}"
    with open(CONF_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def split():
    assert SPLIT_PATH.exists(), f"validation_split.json not found: {SPLIT_PATH}"
    with open(SPLIT_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def manifest():
    assert MANIFEST_PATH.exists(), f"annotation_manifest.json not found: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── 1. Class mapping ──────────────────────────────────────────────────────────

class TestClassMapping:
    def test_import(self):
        from backend.ai.uavpal.classes import CLASSES, NUM_CLASSES, BUILDING_CLASS_ID
        assert NUM_CLASSES == 6
        assert BUILDING_CLASS_ID == 4

    def test_class_ids_sequential(self):
        from backend.ai.uavpal.classes import CLASSES
        ids = [c.id for c in CLASSES]
        assert ids == list(range(6)), f"Expected [0,1,2,3,4,5], got {ids}"

    def test_building_is_class_4(self):
        from backend.ai.uavpal.classes import CLASS_BY_ID, BUILDING_CLASS_ID
        assert BUILDING_CLASS_ID == 4
        assert CLASS_BY_ID[4].name == "Building"

    def test_all_class_names(self):
        from backend.ai.uavpal.classes import CLASS_BY_NAME
        expected = {"Background", "Water", "Road", "Car", "Building", "Tree"}
        assert set(CLASS_BY_NAME.keys()) == expected

    def test_valid_class_ids(self):
        from backend.ai.uavpal.classes import VALID_CLASS_IDS
        assert set(VALID_CLASS_IDS) == {0, 1, 2, 3, 4, 5}

    def test_validate_class_id(self):
        from backend.ai.uavpal.classes import validate_class_id
        for i in range(6):
            assert validate_class_id(i)
        assert not validate_class_id(6)
        assert not validate_class_id(-1)
        assert not validate_class_id(255)

    def test_is_building(self):
        from backend.ai.uavpal.classes import is_building
        assert is_building(4)
        for i in [0, 1, 2, 3, 5]:
            assert not is_building(i)

    def test_class_name_helper(self):
        from backend.ai.uavpal.classes import class_name
        assert class_name(4) == "Building"
        assert class_name(0) == "Background"
        assert class_name(99) == "Unknown"


# ── 2. RGB / label file pairing ───────────────────────────────────────────────

class TestFilePairing:
    def test_rgb_files_exist(self):
        assert RGB_DIR.exists(), f"RGB dir not found: {RGB_DIR}"
        tiffs = [f for f in RGB_DIR.glob("*.tiff") if "(" not in f.name]
        assert len(tiffs) >= 30, f"Expected at least 30 RGB TIFFs, found {len(tiffs)}"

    def test_label_files_exist(self):
        assert LABEL_DIR.exists(), f"Label dir not found: {LABEL_DIR}"
        tiffs = [f for f in LABEL_DIR.glob("*.tiff") if "(" not in f.name]
        assert len(tiffs) >= 30, f"Expected at least 30 label TIFFs, found {len(tiffs)}"

    def test_filenames_match(self):
        """Every label filename must have a corresponding RGB counterpart."""
        rgb_names   = {f.name for f in RGB_DIR.glob("*.tiff") if "(" not in f.name}
        label_names = {f.name for f in LABEL_DIR.glob("*.tiff") if "(" not in f.name}
        assert label_names.issubset(rgb_names), (
            f"Filename mismatch.\n"
            f"  Label without RGB: {label_names - rgb_names}"
        )

    def test_rgb_not_modified(self):
        """Spot-check known byte sizes from Phase 0 baseline."""
        expected = {"00_00.tiff": 7358913, "01_06.tiff": 7259880}
        for name, size in expected.items():
            p = RGB_DIR / name
            assert p.stat().st_size == size, (
                f"{name} size changed: {p.stat().st_size} != {size}"
            )


# ── 3. Tile dimensions ────────────────────────────────────────────────────────

class TestTileDimensions:
    def test_label_dimensions_from_manifest(self, manifest):
        """All 30 label tiles must be exactly 2048×2048 (from Phase 1 manifest)."""
        for entry in manifest["tiles"]:
            assert entry["width"]  == 2048, f"{entry['tile']}: width={entry['width']}"
            assert entry["height"] == 2048, f"{entry['tile']}: height={entry['height']}"

    def test_label_crs_from_manifest(self, manifest):
        for entry in manifest["tiles"]:
            assert entry["crs"] == "EPSG:32643", f"{entry['tile']}: crs={entry['crs']}"

    def test_label_dtype_from_manifest(self, manifest):
        for entry in manifest["tiles"]:
            assert entry["dtype"] == "uint8", f"{entry['tile']}: dtype={entry['dtype']}"


# ── 4. Label value integrity ──────────────────────────────────────────────────

class TestLabelValues:
    def test_all_class_values_valid(self, manifest):
        """Every tile's manifest entry must report only values 0–5."""
        for entry in manifest["tiles"]:
            vals = entry["validation"]["unique_class_values"]
            bad = [v for v in vals if v not in range(6)]
            assert not bad, f"{entry['tile']}: invalid class values {bad}"

    def test_building_class_id_in_manifest(self, manifest):
        for entry in manifest["tiles"]:
            assert entry["building_class_id"] == 4

    def test_all_tiles_have_building_pixels(self, manifest):
        """Phase 1 verified all 30 tiles have building pixels."""
        for entry in manifest["tiles"]:
            assert entry["has_building_pixels"], (
                f"{entry['tile']}: no building pixels (class 4)"
            )


# ── 5. Train / validation / test separation ───────────────────────────────────

class TestSplitIntegrity:
    def test_no_leakage_train_val(self, split):
        train = set(split["internal_train"])
        val   = set(split["validation"])
        assert not (train & val), f"Train/val overlap: {train & val}"

    def test_no_leakage_train_test(self, split):
        train = set(split["internal_train"])
        test  = set(split["official_test"])
        assert not (train & test), f"Train/test overlap: {train & test}"

    def test_no_leakage_val_test(self, split):
        val  = set(split["validation"])
        test = set(split["official_test"])
        assert not (val & test), f"Val/test overlap: {val & test}"

    def test_all_tiles_accounted_for(self, split, manifest):
        all_split = (set(split["internal_train"]) | set(split["validation"]) | set(split["official_test"]))
        all_manifest = {Path(e["tile"]).stem for e in manifest["tiles"]}
        assert all_split == all_manifest, (
            f"Split tiles != manifest tiles.\n"
            f"  Missing from split: {all_manifest - all_split}\n"
            f"  Extra in split:     {all_split - all_manifest}"
        )

    def test_counts(self, split):
        assert len(split["internal_train"]) == 14
        assert len(split["validation"])     == 4
        assert len(split["official_test"])  == 12

    def test_validation_tiles_from_official_train(self, config, split):
        """Validation tiles must be a subset of the official training tiles."""
        official_train = set(config["internal_train_tiles"] + config["validation_tiles"])
        val = set(split["validation"])
        assert val.issubset(official_train), (
            f"Validation tiles not from official train: {val - official_train}"
        )

    def test_official_test_unchanged(self, config, split):
        expected_test = {
            "00_01", "00_02", "00_04", "00_07", "00_10", "00_13",
            "00_14", "00_19", "01_00", "01_03", "01_04", "01_05",
        }
        assert set(split["official_test"]) == expected_test


# ── 6. Training config ────────────────────────────────────────────────────────

class TestTrainingConfig:
    def test_building_class_id(self, config):
        assert config["building_class_id"] == 4

    def test_num_classes(self, config):
        assert config["num_classes"] == 6

    def test_patch_size(self, config):
        assert config["patch_size"] == 512

    def test_architecture(self, config):
        assert config["architecture"] == "UNet"
        assert config["encoder"] == "resnet18"

    def test_input_channels(self, config):
        assert config["input_channels"] == 3

    def test_output_classes(self, config):
        assert config["output_classes"] == 6

    def test_seed(self, config):
        assert config["random_seed"] == 42


# ── 7. Patch extraction ───────────────────────────────────────────────────────

_torch_available = False
try:
    import torch
    _torch_available = True
except ImportError:
    pass

_rasterio_available = False
try:
    # pyrefly: ignore [missing-import]
    import rasterio
    _rasterio_available = True
except ImportError:
    pass

skip_ml = pytest.mark.skipif(
    not (_torch_available and _rasterio_available),
    reason="torch and rasterio required for ML tests"
)


@skip_ml
class TestPatchExtraction:
    def test_dataset_creates(self, config):
        from backend.ai.uavpal.dataset import UAVPalDataset
        tile = config["internal_train_tiles"][0]
        ds = UAVPalDataset(
            tile_ids=[tile],
            rgb_dir=Path(config["rgb_dir"]),
            label_dir=Path(config["label_dir"]),
            patch_size=config["patch_size"],
            augment=False,
        )
        assert len(ds) == 16   # 2048/512 = 4 → 4×4 = 16 patches

    def test_patch_image_shape(self, config):
        from backend.ai.uavpal.dataset import UAVPalDataset
        tile = config["internal_train_tiles"][0]
        ds = UAVPalDataset(
            tile_ids=[tile],
            rgb_dir=Path(config["rgb_dir"]),
            label_dir=Path(config["label_dir"]),
            patch_size=config["patch_size"],
        )
        img, lbl = ds[0]
        assert tuple(img.shape) == (3, 512, 512)
        assert tuple(lbl.shape) == (512, 512)

    def test_patch_label_dtype(self, config):
        from backend.ai.uavpal.dataset import UAVPalDataset
        import torch
        tile = config["internal_train_tiles"][0]
        ds = UAVPalDataset(
            tile_ids=[tile],
            rgb_dir=Path(config["rgb_dir"]),
            label_dir=Path(config["label_dir"]),
            patch_size=config["patch_size"],
        )
        _, lbl = ds[0]
        assert lbl.dtype == torch.int64, f"Expected int64, got {lbl.dtype}"

    def test_patch_image_dtype(self, config):
        from backend.ai.uavpal.dataset import UAVPalDataset
        import torch
        tile = config["internal_train_tiles"][0]
        ds = UAVPalDataset(
            tile_ids=[tile],
            rgb_dir=Path(config["rgb_dir"]),
            label_dir=Path(config["label_dir"]),
            patch_size=config["patch_size"],
        )
        img, _ = ds[0]
        assert img.dtype == torch.float32

    def test_patch_label_values(self, config):
        """Label values in extracted patches must be 0–5 only."""
        from backend.ai.uavpal.dataset import UAVPalDataset
        tile = config["internal_train_tiles"][0]
        ds = UAVPalDataset(
            tile_ids=[tile],
            rgb_dir=Path(config["rgb_dir"]),
            label_dir=Path(config["label_dir"]),
            patch_size=config["patch_size"],
        )
        for i in range(min(4, len(ds))):   # check first 4 patches
            _, lbl = ds[i]
            vals = lbl.unique().tolist()
            bad = [v for v in vals if not (0 <= v <= 5)]
            assert not bad, f"Patch {i}: invalid label values {bad}"

    def test_no_cross_tile_mixing(self, config):
        """Each patch's tile_id must match its source tile."""
        from backend.ai.uavpal.dataset import UAVPalDataset
        tiles = config["internal_train_tiles"][:2]
        ds = UAVPalDataset(
            tile_ids=tiles,
            rgb_dir=Path(config["rgb_dir"]),
            label_dir=Path(config["label_dir"]),
            patch_size=config["patch_size"],
        )
        for i in range(len(ds)):
            info = ds.get_patch_info(i)
            assert info["tile_id"] in tiles

    def test_from_config_factory(self, config):
        from backend.ai.uavpal.dataset import UAVPalDataset
        ds = UAVPalDataset.from_config(config, split="internal_train", augment=False)
        assert ds.num_tiles() == len(config["internal_train_tiles"])
        assert len(ds) == ds.num_tiles() * 16


# ── 8. Model output shape ─────────────────────────────────────────────────────

@skip_ml
class TestModelOutputShape:
    def test_model_creates(self):
        from backend.ai.segmentation.model import build_model
        model = build_model(num_classes=6, pretrained=False)
        assert model is not None

    def test_output_channels(self):
        import torch
        from backend.ai.segmentation.model import build_model
        model = build_model(num_classes=6, pretrained=False)
        model.eval()
        x = torch.zeros(1, 3, 512, 512)
        with torch.no_grad():
            out = model(x)
        assert out.shape[1] == 6, f"Expected 6 output channels, got {out.shape[1]}"

    def test_output_spatial_matches_input(self):
        import torch
        from backend.ai.segmentation.model import build_model
        model = build_model(num_classes=6, pretrained=False)
        model.eval()
        x = torch.zeros(1, 3, 512, 512)
        with torch.no_grad():
            out = model(x)
        assert out.shape[2] == 512
        assert out.shape[3] == 512

    def test_output_shape_full(self):
        import torch
        from backend.ai.segmentation.model import build_model
        model = build_model(num_classes=6, pretrained=False)
        model.eval()
        x = torch.zeros(2, 3, 512, 512)   # batch_size=2
        with torch.no_grad():
            out = model(x)
        assert tuple(out.shape) == (2, 6, 512, 512)

    def test_building_mask_from_model(self):
        import torch
        from backend.ai.segmentation.model import build_model
        from backend.ai.uavpal.classes import BUILDING_CLASS_ID
        model = build_model(num_classes=6, pretrained=False)
        x = torch.zeros(1, 3, 512, 512)
        mask = model.predict_building_mask(x)
        assert mask.dtype == torch.bool
        assert tuple(mask.shape) == (1, 512, 512)

    def test_parameter_count_reasonable(self):
        from backend.ai.segmentation.model import build_model
        model = build_model(num_classes=6, pretrained=False)
        n = model.parameter_count()
        # ResNet18 U-Net should be ~15M–20M parameters
        assert 10_000_000 < n < 30_000_000, f"Unexpected param count: {n:,}"

    def test_num_classes_attribute(self):
        from backend.ai.segmentation.model import build_model
        model = build_model(num_classes=6)
        assert model.num_classes == 6
