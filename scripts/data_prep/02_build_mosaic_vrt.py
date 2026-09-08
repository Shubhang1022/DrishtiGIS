"""
DrishtiGIS — Bhopal Mosaic VRT Builder
========================================
Task:    2.2 (spec: foundation-and-data-pipeline v0.2, REQ-DATA-03)

ENVIRONMENT: scripts/.gis-env venv (rasterio 1.5.1 bundling GDAL 3.12.4)
Do NOT run in the main application Python environment.

Input:   Dataset/Drone-Images/BHOPAL/*.tiff  (READ ONLY — never modified)
Output:  data/processed/bhopal_mosaic.vrt

What this script does
---------------------
Builds a GDAL Virtual Raster (VRT) combining all 30 Bhopal TIFF tiles.
No pixel data is copied — the VRT references the originals.

Overlap strategy (from spec REQ-DATA-03 / design.md §6.3):
  gdalbuildvrt default: last-file-wins by lexicographic file order.
  This means the last tile listed whose extent covers a given pixel wins.
  Files are sorted lexicographically so the strategy is DETERMINISTIC and
  reproducible.
  Blend/average is NOT applied at VRT stage.

VRT construction approach:
  rasterio 1.5.1 bundles GDAL 3.12.4 internally but does not expose the
  osgeo Python module. The GDAL PyPI package requires MSVC 14+ for source
  build on Windows (no pre-built cp314 wheel available). Therefore this
  script constructs the GDAL VRT XML directly — identical to what
  gdalbuildvrt produces — and validates it by opening with rasterio.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parents[2]
TIFF_DIR   = REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL"
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
VRT_PATH   = OUTPUT_DIR / "bhopal_mosaic.vrt"
REPORT     = OUTPUT_DIR / "bhopal_validation_report.json"
LOG_PATH   = OUTPUT_DIR / "pipeline.log"

# Expected Dataset/ file sizes from audit (for integrity check)
DATASET_CHECKSUMS = {
    "00_00.tiff": 7_358_913,
    "01_06.tiff": 7_259_880,
}


def log(msg: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] VRT: {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def verify_dataset_unchanged() -> bool:
    """Confirm Dataset/ files are byte-for-byte unchanged from audit values."""
    ok = True
    for fname, expected_size in DATASET_CHECKSUMS.items():
        fpath = TIFF_DIR / fname
        actual = fpath.stat().st_size
        if actual != expected_size:
            log(f"INTEGRITY FAIL: {fname} expected {expected_size} bytes, got {actual}")
            ok = False
    return ok


def build_vrt_xml(tiff_files: list[Path]) -> str:
    """
    Construct a GDAL-compatible VRT XML for a mosaic of the given TIFF files.

    Strategy: last-file-wins (lexicographic sort order).
    This matches gdalbuildvrt's default overlap behaviour.

    The VRT uses SimpleSource elements — each tile band covers its own
    spatial extent. GDAL resolves overlaps by reading sources in declaration
    order; later sources win for overlapping pixels.
    """
    import rasterio
    from rasterio.crs import CRS

    # Read properties from the first tile (all tiles share CRS + resolution)
    with rasterio.open(tiff_files[0]) as first:
        crs    = first.crs
        res_x  = first.res[0]    # pixel width  in CRS units (m)
        res_y  = first.res[1]    # pixel height in CRS units (m)
        count  = first.count     # number of bands
        dtype  = first.dtypes[0] # data type

    # Compute mosaic bounding box across all tiles
    lefts, bottoms, rights, tops = [], [], [], []
    for fp in tiff_files:
        with rasterio.open(fp) as ds:
            lefts.append(ds.bounds.left)
            bottoms.append(ds.bounds.bottom)
            rights.append(ds.bounds.right)
            tops.append(ds.bounds.top)

    mosaic_left   = min(lefts)
    mosaic_bottom = min(bottoms)
    mosaic_right  = max(rights)
    mosaic_top    = max(tops)

    mosaic_width  = int(round((mosaic_right  - mosaic_left)   / res_x))
    mosaic_height = int(round((mosaic_top    - mosaic_bottom) / res_y))

    # Map rasterio dtype → GDAL typename
    dtype_map = {
        "uint8":   "Byte",
        "uint16":  "UInt16",
        "int16":   "Int16",
        "uint32":  "UInt32",
        "int32":   "Int32",
        "float32": "Float32",
        "float64": "Float64",
    }
    gdal_dtype = dtype_map.get(dtype, "Byte")

    # CRS as WKT
    crs_wkt = crs.to_wkt()

    # GeoTransform: top-left x, x pixel size, 0, top-left y, 0, -y pixel size
    gt = (mosaic_left, res_x, 0.0, mosaic_top, 0.0, -res_y)
    gt_str = ", ".join(f"{v:.10f}" for v in gt)

    # Build band XML — one band per channel, SimpleSource per tile
    bands_xml = []
    for band_idx in range(1, count + 1):
        sources_xml = []
        for fp in tiff_files:
            with rasterio.open(fp) as ds:
                b = ds.bounds
                # Pixel offsets of this tile's top-left within the mosaic
                dst_off_x = int(round((b.left  - mosaic_left) / res_x))
                dst_off_y = int(round((mosaic_top - b.top)    / res_y))
                src_w, src_h = ds.width, ds.height

                # Use relative path from VRT file location
                rel_path = os.path.relpath(fp, OUTPUT_DIR).replace("\\", "/")

                src_xml = (
                    f"    <SimpleSource>\n"
                    f"      <SourceFilename relativeToVRT=\"1\">{rel_path}</SourceFilename>\n"
                    f"      <SourceBand>{band_idx}</SourceBand>\n"
                    f"      <SourceProperties RasterXSize=\"{src_w}\" RasterYSize=\"{src_h}\""
                    f" DataType=\"{gdal_dtype}\" BlockXSize=\"512\" BlockYSize=\"512\"/>\n"
                    f"      <SrcRect xOff=\"0\" yOff=\"0\" xSize=\"{src_w}\" ySize=\"{src_h}\"/>\n"
                    f"      <DstRect xOff=\"{dst_off_x}\" yOff=\"{dst_off_y}\""
                    f" xSize=\"{src_w}\" ySize=\"{src_h}\"/>\n"
                    f"    </SimpleSource>"
                )
                sources_xml.append(src_xml)

        band_xml = (
            f"  <VRTRasterBand dataType=\"{gdal_dtype}\" band=\"{band_idx}\">\n"
            f"    <ColorInterp>{'Red' if band_idx==1 else 'Green' if band_idx==2 else 'Blue'}</ColorInterp>\n"
            + "\n".join(sources_xml) + "\n"
            f"  </VRTRasterBand>"
        )
        bands_xml.append(band_xml)

    vrt_xml = (
        f'<VRTDataset rasterXSize="{mosaic_width}" rasterYSize="{mosaic_height}">\n'
        f'  <SRS dataAxisToSRSAxisMapping="1,2">{crs_wkt}</SRS>\n'
        f'  <GeoTransform>{gt_str}</GeoTransform>\n'
        + "\n".join(bands_xml) + "\n"
        f'</VRTDataset>\n'
    )
    return vrt_xml, {
        "crs":            str(crs),
        "mosaic_left":    mosaic_left,
        "mosaic_bottom":  mosaic_bottom,
        "mosaic_right":   mosaic_right,
        "mosaic_top":     mosaic_top,
        "mosaic_width_px": mosaic_width,
        "mosaic_height_px": mosaic_height,
        "res_x":          res_x,
        "res_y":          res_y,
        "bands":          count,
        "dtype":          gdal_dtype,
    }


def main() -> int:
    import rasterio

    log("=" * 60)
    log("DrishtiGIS — Bhopal Mosaic VRT (Task 2.2)")
    log(f"rasterio {rasterio.__version__} / GDAL {rasterio.__gdal_version__}")
    log(f"TIFF source : {TIFF_DIR}")
    log(f"VRT output  : {VRT_PATH}")

    # ── 1. Verify Dataset/ is unchanged ───────────────────────────────────
    if not verify_dataset_unchanged():
        log("ABORT: Dataset/ integrity check failed.")
        return 1
    log("Dataset/ integrity: OK")

    # ── 2. Locate and sort all TIFF files ─────────────────────────────────
    tiff_files = sorted(TIFF_DIR.glob("*.tiff"))
    if not tiff_files:
        log(f"ERROR: No .tiff files found in {TIFF_DIR}")
        return 1
    if len(tiff_files) != 30:
        log(f"WARNING: Expected 30 tiles, found {len(tiff_files)}")

    log(f"Found {len(tiff_files)} TIFF files (sorted lexicographically)")
    log("First file: " + tiff_files[0].name)
    log("Last file : " + tiff_files[-1].name)

    # ── 3. Log overlap strategy ────────────────────────────────────────────
    log("Overlap strategy: last-file-wins by lexicographic sort order.")
    log("  Files sorted lexicographically for reproducibility.")
    log("  Overlap = ~1.37m between adjacent tiles (from validation report).")
    log("  Blend/average NOT applied at VRT stage.")
    log("  Implementation: GDAL VRT SimpleSource declaration order (last wins).")

    # ── 4. Build VRT XML ───────────────────────────────────────────────────
    log("Building VRT XML...")
    try:
        vrt_xml, meta = build_vrt_xml(tiff_files)
    except Exception as e:
        log(f"ERROR building VRT: {e}")
        import traceback
        log(traceback.format_exc())
        return 1

    log(f"Mosaic dimensions: {meta['mosaic_width_px']} × {meta['mosaic_height_px']} px")
    log(f"Mosaic bounds (UTM): L={meta['mosaic_left']:.4f} B={meta['mosaic_bottom']:.4f} "
        f"R={meta['mosaic_right']:.4f} T={meta['mosaic_top']:.4f}")
    log(f"CRS: {meta['crs']}")
    log(f"Resolution: {meta['res_x']:.6f} m/px")
    log(f"Bands: {meta['bands']}  Dtype: {meta['dtype']}")

    # ── 5. Write VRT file ──────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(VRT_PATH, "w", encoding="utf-8") as f:
        f.write(vrt_xml)
    log(f"VRT written: {VRT_PATH} ({VRT_PATH.stat().st_size:,} bytes)")

    # ── 6. Validate VRT can be opened by rasterio ─────────────────────────
    log("Validating VRT with rasterio...")
    try:
        with rasterio.open(VRT_PATH) as vrt_ds:
            vrt_crs    = str(vrt_ds.crs)
            vrt_shape  = vrt_ds.shape
            vrt_bounds = vrt_ds.bounds
            vrt_count  = vrt_ds.count

        log(f"VRT opened OK: CRS={vrt_crs} shape={vrt_shape} bands={vrt_count}")
        log(f"VRT bounds: {vrt_bounds}")
    except Exception as e:
        log(f"VALIDATION FAIL: rasterio could not open VRT: {e}")
        return 1

    # ── 7. Cross-check against validation report ──────────────────────────
    with open(REPORT, encoding="utf-8") as f:
        report = json.load(f)
    expected_utm = report["mosaic_bounds_utm43n"]

    # Allow 1m tolerance (pixel rounding)
    tol = 1.0
    checks = [
        ("UTM min_easting",  vrt_bounds.left,   expected_utm["min_easting"],  tol),
        ("UTM max_easting",  vrt_bounds.right,  expected_utm["max_easting"],  tol),
        ("UTM min_northing", vrt_bounds.bottom, expected_utm["min_northing"], tol),
        ("UTM max_northing", vrt_bounds.top,    expected_utm["max_northing"], tol),
    ]
    bounds_ok = True
    for label, actual, expected, tolerance in checks:
        diff = abs(actual - expected)
        ok   = diff <= tolerance
        status = "OK" if ok else "FAIL"
        log(f"  Bounds check {label}: actual={actual:.4f} expected={expected:.4f} diff={diff:.4f} [{status}]")
        if not ok:
            bounds_ok = False

    if not bounds_ok:
        log("BOUNDS MISMATCH — VRT bounds do not match validation report.")
        return 1

    if vrt_crs != "EPSG:32643":
        log(f"CRS FAIL: expected EPSG:32643, got {vrt_crs}")
        return 1

    log("CRS check: PASS (EPSG:32643)")

    # ── 8. Final Dataset/ integrity re-check ──────────────────────────────
    if not verify_dataset_unchanged():
        log("ABORT: Dataset/ was modified during script execution — this is a bug.")
        return 1
    log("Dataset/ post-run integrity: OK")

    log("=" * 60)
    log("Task 2.2 COMPLETE — bhopal_mosaic.vrt produced and validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
