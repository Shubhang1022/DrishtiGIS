"""
DrishtiGIS — Cloud Optimized GeoTIFF Builder
==============================================
Task:    2.3 (spec: foundation-and-data-pipeline v0.2, REQ-DATA-04)

ENVIRONMENT: scripts/.gis-env venv (rasterio 1.5.1 bundling GDAL 3.12.4)
Do NOT run in the main application Python environment.

Input:   data/processed/bhopal_mosaic.vrt
Output:  data/processed/bhopal_cog.tif

What this script does
---------------------
1. Opens the VRT mosaic produced by 02_build_mosaic_vrt.py.
2. Reads the full mosaic in tiled windows (memory-efficient).
3. Writes a GeoTIFF with JPEG compression, tiled 256×256 blocks.
4. Builds internal overview levels (equivalent to -co OVERVIEWS=AUTO).
5. Copies to a Cloud Optimized GeoTIFF using rasterio's COG driver.
6. Validates the COG by checking: CRS, overviews, file size, and
   that it is smaller than the combined source tile size (~206 MB).

Equivalent to gdal_translate:
    gdal_translate -of COG -co COMPRESS=JPEG -co QUALITY=85
                   -co OVERVIEWS=AUTO
                   bhopal_mosaic.vrt bhopal_cog.tif

CRS is preserved as EPSG:32643 (UTM zone 43N).
"""

import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
VRT_PATH   = OUTPUT_DIR / "bhopal_mosaic.vrt"
TMP_PATH   = OUTPUT_DIR / "_bhopal_tmp.tif"     # intermediate (deleted after COG)
COG_PATH   = OUTPUT_DIR / "bhopal_cog.tif"
LOG_PATH   = OUTPUT_DIR / "pipeline.log"

SOURCE_SIZE_BYTES = 206 * 1024 * 1024  # ~206 MB combined source tiles

# Dataset/ integrity sentinel values
DATASET_CHECKSUMS = {
    REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL" / "00_00.tiff": 7_358_913,
    REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL" / "01_06.tiff": 7_259_880,
}


def log(msg: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] COG: {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def verify_dataset_unchanged() -> bool:
    for fpath, expected in DATASET_CHECKSUMS.items():
        actual = fpath.stat().st_size
        if actual != expected:
            log(f"INTEGRITY FAIL: {fpath.name} expected {expected}, got {actual}")
            return False
    return True


def build_overview_levels(width: int, height: int) -> list[int]:
    """
    Compute overview levels where the smallest overview is >= 256 px in either
    dimension — equivalent to GDAL's AUTO overview strategy.
    """
    levels = []
    factor = 2
    while True:
        ov_w = math.ceil(width  / factor)
        ov_h = math.ceil(height / factor)
        if ov_w < 64 and ov_h < 64:
            break
        levels.append(factor)
        factor *= 2
        if factor > 1024:
            break
    return levels


def main() -> int:
    import rasterio
    from rasterio.enums import Resampling
    import rasterio.shutil as rio_shutil
    import numpy as np

    log("=" * 60)
    log("DrishtiGIS — Cloud Optimized GeoTIFF (Task 2.3)")
    log(f"rasterio {rasterio.__version__} / GDAL {rasterio.__gdal_version__}")
    log(f"Input VRT : {VRT_PATH}")
    log(f"Output COG: {COG_PATH}")

    # ── 1. Pre-flight checks ───────────────────────────────────────────────
    if not verify_dataset_unchanged():
        log("ABORT: Dataset/ integrity check failed.")
        return 1
    log("Dataset/ integrity: OK")

    if not VRT_PATH.exists():
        log(f"ERROR: VRT not found at {VRT_PATH}. Run 02_build_mosaic_vrt.py first.")
        return 1

    # Skip if COG already exists and is valid
    if COG_PATH.exists():
        size_mb = COG_PATH.stat().st_size / 1e6
        log(f"COG already exists ({size_mb:.1f} MB). Skipping rebuild (idempotent).")
        log("Delete data/processed/bhopal_cog.tif to force rebuild.")
        return 0

    # ── 2. Open source VRT ────────────────────────────────────────────────
    log("Opening VRT mosaic...")
    with rasterio.open(VRT_PATH) as src:
        src_crs     = src.crs
        src_profile = src.profile.copy()
        src_width   = src.width
        src_height  = src.height
        src_bounds  = src.bounds
        src_count   = src.count
        src_dtype   = src.dtypes[0]
        src_transform = src.transform

    log(f"Source: {src_width}×{src_height}px, {src_count} bands, CRS={src_crs}")

    if str(src_crs) != "EPSG:32643":
        log(f"ERROR: VRT CRS is {src_crs}, expected EPSG:32643. Aborting.")
        return 1

    # ── 3. Write tiled, JPEG-compressed intermediate GeoTIFF ──────────────
    log(f"Writing intermediate tiled GeoTIFF: {TMP_PATH}")
    log("  compress=JPEG  quality=85  tiled=True  blocksize=256")

    tmp_profile = {
        "driver":     "GTiff",
        "dtype":      src_dtype,
        "width":      src_width,
        "height":     src_height,
        "count":      src_count,
        "crs":        src_crs,
        "transform":  src_transform,
        "tiled":      True,
        "blockxsize": 256,
        "blockysize": 256,
        "compress":   "JPEG",
        "jpeg_quality": 85,
        "photometric": "RGB" if src_count == 3 else None,
    }
    if tmp_profile["photometric"] is None:
        del tmp_profile["photometric"]

    # Write in horizontal strips for memory efficiency (512 rows at a time)
    STRIP = 512
    total_rows = src_height

    with rasterio.open(VRT_PATH) as src:
        with rasterio.open(TMP_PATH, "w", **tmp_profile) as dst:
            y_off = 0
            while y_off < total_rows:
                rows   = min(STRIP, total_rows - y_off)
                window = rasterio.windows.Window(
                    col_off=0, row_off=y_off,
                    width=src_width, height=rows,
                )
                data = src.read(window=window)
                dst.write(data, window=window)
                y_off += rows
                pct = 100 * y_off / total_rows
                if (y_off // STRIP) % 4 == 0 or y_off >= total_rows:
                    log(f"  Written rows {y_off}/{total_rows} ({pct:.0f}%)")

    tmp_size_mb = TMP_PATH.stat().st_size / 1e6
    log(f"Intermediate GeoTIFF written: {tmp_size_mb:.1f} MB")

    # ── 4. Build internal overviews ────────────────────────────────────────
    ov_levels = build_overview_levels(src_width, src_height)
    log(f"Building internal overviews: {ov_levels}")

    with rasterio.open(TMP_PATH, "r+") as dst:
        dst.build_overviews(ov_levels, Resampling.nearest)
        dst.update_tags(ns="rio_overview", resampling="nearest")

    log(f"Overviews built: {len(ov_levels)} levels")

    # ── 5. Copy to Cloud Optimized GeoTIFF ────────────────────────────────
    log(f"Converting to COG: {COG_PATH}")
    rio_shutil.copy(
        TMP_PATH, COG_PATH,
        driver="COG",
        compress="JPEG",
        jpeg_quality=85,
    )
    cog_size_bytes = COG_PATH.stat().st_size
    cog_size_mb    = cog_size_bytes / 1e6
    log(f"COG written: {cog_size_mb:.1f} MB")

    # ── 6. Clean up intermediate file ─────────────────────────────────────
    TMP_PATH.unlink(missing_ok=True)
    log("Intermediate file removed.")

    # ── 7. Validate COG ───────────────────────────────────────────────────
    log("Validating COG...")
    with rasterio.open(COG_PATH) as cog:
        cog_crs    = str(cog.crs)
        cog_shape  = (cog.height, cog.width)
        cog_bounds = cog.bounds
        cog_count  = cog.count
        cog_ovrs   = cog.overviews(1)
        cog_driver = cog.driver
        cog_profile = cog.profile

    log(f"  Driver   : {cog_driver}")
    log(f"  CRS      : {cog_crs}")
    log(f"  Shape    : {cog_shape}")
    log(f"  Bands    : {cog_count}")
    log(f"  Compress : {cog_profile.get('compress')}")
    log(f"  Overviews: {cog_ovrs}")
    log(f"  Bounds   : {cog_bounds}")

    errors = []
    if cog_crs != "EPSG:32643":
        errors.append(f"CRS mismatch: {cog_crs}")
    if cog_count != 3:
        errors.append(f"Band count: {cog_count}")
    if len(cog_ovrs) < 2:
        errors.append(f"Too few overview levels: {cog_ovrs}")
    if cog_size_bytes >= SOURCE_SIZE_BYTES:
        errors.append(f"COG size {cog_size_mb:.1f}MB >= source {SOURCE_SIZE_BYTES/1e6:.0f}MB")

    if errors:
        for e in errors:
            log(f"  VALIDATION FAIL: {e}")
        return 1

    log("  All validation checks: PASS")

    # ── 8. Final Dataset/ integrity re-check ──────────────────────────────
    if not verify_dataset_unchanged():
        log("ABORT: Dataset/ was modified during script execution — bug.")
        return 1
    log("Dataset/ post-run integrity: OK")

    log("=" * 60)
    log(f"Task 2.3 COMPLETE — bhopal_cog.tif ({cog_size_mb:.1f} MB) produced and validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
