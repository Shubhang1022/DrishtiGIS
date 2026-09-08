"""
DrishtiGIS — XYZ Raster Tile Pyramid Generator
================================================
Task:    2.4 (spec: foundation-and-data-pipeline v0.2, REQ-DATA-05)

ENVIRONMENT: scripts/.gis-env venv (rasterio 1.5.1 bundling GDAL 3.12.4)
Do NOT run in the main application Python environment.

Input:   data/processed/bhopal_cog.tif            (EPSG:32643)
Output:  data/processed/tiles/bhopal/{z}/{x}/{y}.png

Tile generation approach (per-tile reproject)
----------------------------------------------
For each XYZ tile: directly reproject from the source COG into a
256×256 tile-sized array using rasterio.warp.reproject.
This matches the behaviour of gdal2tiles.py and avoids loading the
entire dataset into memory.

XYZ scheme:
  Y-axis is top-down (Y=0 at north pole) — Google/MapLibre convention.
  This is equivalent to --xyz flag in gdal2tiles.py.

CRS:
  Source: EPSG:32643 (UTM Zone 43N)
  Tile output: EPSG:3857 (Web Mercator)

Data integrity:
  Dataset/ directory is never written to.
  Tiles represent only the actual imagery footprint.
"""

import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
COG_PATH   = OUTPUT_DIR / "bhopal_cog.tif"
TILES_DIR  = OUTPUT_DIR / "tiles" / "bhopal"
LOG_PATH   = OUTPUT_DIR / "pipeline.log"

ZOOM_MIN      = 18
ZOOM_MAX      = 21
TILE_SIZE     = 256
MAX_TILE_WARN = 50_000
NODATA        = 0

DATASET_CHECKSUMS = {
    REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL" / "00_00.tiff": 7_358_913,
    REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL" / "01_06.tiff": 7_259_880,
}


def log(msg: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] TILES: {msg}"
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


# ── Web Mercator / XYZ tile math ───────────────────────────────────────────

def latlon_to_tile(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    """WGS84 → XYZ tile (Y-axis down)."""
    lat_rad = math.radians(lat_deg)
    n = 2 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    # Clamp to valid range
    x = max(0, min(n - 1, x))
    y = max(0, min(n - 1, y))
    return x, y


def tile_bounds_3857(tx: int, ty: int, zoom: int) -> tuple[float, float, float, float]:
    """EPSG:3857 bounding box (left, bottom, right, top) of a tile."""
    ORIGIN = 20_037_508.342_789_244
    n      = 2 ** zoom
    tile_m = 2 * ORIGIN / n
    left   =  tx      * tile_m - ORIGIN
    right  = (tx + 1) * tile_m - ORIGIN
    top    =  ORIGIN  - ty      * tile_m
    bottom =  ORIGIN  - (ty + 1) * tile_m
    return left, bottom, right, top


def tile_transform_3857(tx: int, ty: int, zoom: int):
    """Affine transform for a 256×256 tile in EPSG:3857."""
    from affine import Affine
    ORIGIN = 20_037_508.342_789_244
    n      = 2 ** zoom
    tile_m = 2 * ORIGIN / n
    res    = tile_m / TILE_SIZE          # metres per pixel
    left   = tx * tile_m - ORIGIN
    top    = ORIGIN - ty * tile_m
    return Affine(res, 0, left, 0, -res, top)


def main() -> int:
    import numpy as np
    import rasterio
    from rasterio.crs import CRS
    from rasterio.warp import reproject, Resampling, transform_bounds
    from PIL import Image as PILImage

    log("=" * 60)
    log("DrishtiGIS — XYZ Raster Tile Pyramid (Task 2.4)")
    log(f"rasterio {rasterio.__version__} / GDAL {rasterio.__gdal_version__}")
    log(f"Input COG  : {COG_PATH}")
    log(f"Output dir : {TILES_DIR}")
    log(f"Zoom range : {ZOOM_MIN}–{ZOOM_MAX}  Tile size: {TILE_SIZE}px")
    log("Tile scheme: XYZ (Y-axis down, Google/MapLibre compatible)")
    log("Output CRS : EPSG:3857 (reprojected per-tile from EPSG:32643)")

    if not verify_dataset_unchanged():
        log("ABORT: Dataset/ integrity check failed.")
        return 1
    log("Dataset/ integrity: OK")

    if not COG_PATH.exists():
        log(f"ERROR: COG not found: {COG_PATH}. Run 03_build_cog.py first.")
        return 1

    crs_3857 = CRS.from_epsg(3857)
    crs_4326 = CRS.from_epsg(4326)

    # ── Read COG metadata ────────────────────────────────────────────────
    with rasterio.open(COG_PATH) as src:
        src_crs       = src.crs
        src_bounds    = src.bounds
        src_count     = src.count
        src_nodata    = src.nodata or NODATA

    if str(src_crs) != "EPSG:32643":
        log(f"ERROR: COG CRS is {src_crs}, expected EPSG:32643")
        return 1

    # Project COG bounds to WGS84 to determine tile range
    wgs84_bounds = transform_bounds(src_crs, crs_4326, *src_bounds)
    min_lon, min_lat, max_lon, max_lat = wgs84_bounds
    log(f"COG WGS84 bounds: lon [{min_lon:.6f}, {max_lon:.6f}] lat [{min_lat:.6f}, {max_lat:.6f}]")

    # ── Generate tiles ───────────────────────────────────────────────────
    total_written  = 0
    tile_counts    = {}

    with rasterio.open(COG_PATH) as src:
        for zoom in range(ZOOM_MIN, ZOOM_MAX + 1):
            # XYZ tile range covering the imagery bounds
            # Use corners of bounding box (top-left and bottom-right in tile coords)
            tx_min, ty_min = latlon_to_tile(max_lat, min_lon, zoom)  # top-left
            tx_max, ty_max = latlon_to_tile(min_lat, max_lon, zoom)  # bottom-right
            tx_min, tx_max = min(tx_min, tx_max), max(tx_min, tx_max)
            ty_min, ty_max = min(ty_min, ty_max), max(ty_min, ty_max)

            n_tiles = (tx_max - tx_min + 1) * (ty_max - ty_min + 1)
            tile_counts[zoom] = 0
            log(f"Zoom {zoom}: x=[{tx_min},{tx_max}] y=[{ty_min},{ty_max}]  ({n_tiles} candidate tiles)")

            if total_written + n_tiles > MAX_TILE_WARN:
                log(f"WARNING: Approaching {MAX_TILE_WARN} total tiles — check zoom range.")

            for tx in range(tx_min, tx_max + 1):
                for ty in range(ty_min, ty_max + 1):
                    # Affine transform for this tile in EPSG:3857
                    dst_transform = tile_transform_3857(tx, ty, zoom)

                    # Allocate destination tile (3 bands, 256×256)
                    dst = np.zeros((src_count, TILE_SIZE, TILE_SIZE), dtype=np.uint8)

                    # Reproject the source COG directly into this tile
                    reproject(
                        source=rasterio.band(src, list(range(1, src_count + 1))),
                        destination=dst,
                        src_transform=src.transform,
                        src_crs=src_crs,
                        dst_transform=dst_transform,
                        dst_crs=crs_3857,
                        resampling=Resampling.nearest,
                        src_nodata=src_nodata,
                        dst_nodata=0,
                    )

                    # Skip blank tiles (all pixels are nodata/zero)
                    if dst.max() == 0:
                        continue

                    # Write PNG
                    rgb = np.moveaxis(dst, 0, -1)  # (H, W, 3)
                    img = PILImage.fromarray(rgb, mode="RGB")

                    out_dir = TILES_DIR / str(zoom) / str(tx)
                    out_dir.mkdir(parents=True, exist_ok=True)
                    img.save(str(out_dir / f"{ty}.png"), format="PNG")

                    total_written += 1
                    tile_counts[zoom] = tile_counts.get(zoom, 0) + 1

            log(f"Zoom {zoom}: {tile_counts[zoom]} non-blank tiles written.")

    # ── Summary ──────────────────────────────────────────────────────────
    log(f"Total tiles written: {total_written}")
    for z, count in sorted(tile_counts.items()):
        log(f"  Zoom {z}: {count} tiles")

    if not verify_dataset_unchanged():
        log("ABORT: Dataset/ was modified during tile generation — bug.")
        return 1
    log("Dataset/ post-run integrity: OK")

    log("=" * 60)
    log(f"Task 2.4 COMPLETE — tiles in {TILES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
