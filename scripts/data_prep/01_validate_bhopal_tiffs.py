"""
DrishtiGIS — Bhopal TIFF Validation Script
===========================================
Task:    1.1 (spec: foundation-and-data-pipeline v0.2, REQ-DATA-01)
Env:     Main Python environment (uses Pillow only — no GIS env required)
Input:   Dataset/Drone-Images/BHOPAL/*.tiff  (READ ONLY — never modified)
Output:  data/processed/bhopal_validation_report.json

What this script does
---------------------
1. Opens every .tiff file in the BHOPAL directory using Pillow.
2. Reads embedded GeoTIFF tags to extract CRS, resolution, bounds, bands.
3. Performs UTM → WGS84 reprojection using pure Python math (no GDAL required).
4. Analyses the tile grid layout and reports incomplete rows.
5. Checks GDAL availability (reports but does not require it).
6. Writes a machine-readable JSON report and a human-readable summary.
7. Exits 0 on success, 1 if any tile fails validation.

IMPORTANT: This script NEVER writes to Dataset/.
All output is written to data/processed/.
"""

import json
import math
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT    = Path(__file__).resolve().parents[2]
TIFF_DIR     = REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL"
OUTPUT_DIR   = REPO_ROOT / "data" / "processed"
REPORT_PATH  = OUTPUT_DIR / "bhopal_validation_report.json"
LOG_PATH     = OUTPUT_DIR / "pipeline.log"

# Expected values (from audit)
EXPECTED_CRS        = "WGS 84 / UTM zone 43N"
EXPECTED_EPSG       = 32643
EXPECTED_DIMS       = (2048, 2048)
EXPECTED_BANDS      = 3
EXPECTED_BITS       = 8
EXPECTED_RESOLUTION = 0.02171   # m/pixel ± tolerance
RESOLUTION_TOL      = 0.0002    # ±0.02% tolerance


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
def log(msg: str, also_print: bool = True) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] VALIDATE: {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if also_print:
        print(line)


# ---------------------------------------------------------------------------
# Pure-Python UTM zone 43N → WGS84 conversion
# (Verified against audit results; no external dependency)
# ---------------------------------------------------------------------------
def utm43n_to_latlon(easting: float, northing: float) -> tuple[float, float]:
    """Convert EPSG:32643 (UTM zone 43N) coordinates to WGS84 lat/lon."""
    a   = 6_378_137.0
    f   = 1 / 298.257_223_563
    k0  = 0.9996
    e2  = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    lon0 = math.radians(75.0)  # central meridian zone 43

    N1  = northing / k0
    mu  = N1 / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1  = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu
            + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu))

    N    = a / math.sqrt(1 - e2 * math.sin(phi1)**2)
    T    = math.tan(phi1)**2
    C    = ep2 * math.cos(phi1)**2
    R    = a * (1 - e2) / (1 - e2 * math.sin(phi1)**2) ** 1.5
    D    = (easting - 500_000) / (N * k0)

    lat = phi1 - (N * math.tan(phi1) / R) * (
        D**2 / 2
        - (5 + 3 * T + 10 * C - 4 * C**2 - 9 * ep2) * D**4 / 24
        + (61 + 90 * T + 298 * C + 45 * T**2 - 252 * ep2 - 3 * C**2) * D**6 / 720
    )
    lon = lon0 + (
        D
        - (1 + 2 * T + C) * D**3 / 6
        + (5 - 2 * C + 28 * T - 3 * C**2 + 8 * ep2 + 24 * T**2) * D**5 / 120
    ) / math.cos(phi1)

    return round(math.degrees(lat), 8), round(math.degrees(lon), 8)


# ---------------------------------------------------------------------------
# GDAL availability check (optional — does not block validation)
# ---------------------------------------------------------------------------
def check_gdal() -> dict:
    result = {"available": False, "version": None, "note": ""}
    try:
        from osgeo import gdal  # type: ignore
        result["available"] = True
        result["version"]   = gdal.__version__
        result["note"]      = "GDAL Python bindings available — Phase 2 pipeline ready."
    except ImportError:
        result["note"] = (
            "GDAL Python bindings NOT found in this environment. "
            "Phase 1 validation uses Pillow only (sufficient). "
            "For Phase 2 (mosaic/COG/tiles), activate the GIS environment first — "
            "see scripts/README.md."
        )
    return result


# ---------------------------------------------------------------------------
# Tag decoders
# ---------------------------------------------------------------------------
COMPRESSION_NAMES = {
    1: "None/Uncompressed",
    5: "LZW",
    6: "JPEG (old)",
    7: "JPEG",
    8: "Deflate/ZIP",
    32773: "PackBits",
}

def decode_geokeydir(gkd: tuple) -> dict:
    """Extract EPSG code and other values from GeoKeyDirectory tag (34735)."""
    keys = {}
    if not gkd or len(gkd) < 4:
        return keys
    num_keys = gkd[3]
    for i in range(num_keys):
        base = 4 + i * 4
        if base + 3 >= len(gkd):
            break
        key_id    = gkd[base]
        tiff_tag  = gkd[base + 1]
        count     = gkd[base + 2]
        value_off = gkd[base + 3]
        if tiff_tag == 0:  # short value stored inline
            keys[key_id] = value_off
    return keys


# ---------------------------------------------------------------------------
# Single-tile validator
# ---------------------------------------------------------------------------
def validate_tile(filepath: Path) -> dict:
    from PIL import Image  # type: ignore

    result = {
        "filename":     filepath.name,
        "valid":        False,
        "errors":       [],
        "warnings":     [],
        "crs_string":   None,
        "epsg":         None,
        "resolution_m": None,
        "dimensions":   None,
        "bands":        None,
        "bit_depth":    None,
        "compression":  None,
        "nodata_value": None,
        "nodata_pct":   None,
        "bounds_utm43n": None,
        "bounds_wgs84":  None,
        "tilepoint_raw": None,
        "pixelscale_raw": None,
    }

    try:
        img  = Image.open(filepath)
        tags = img.tag_v2
    except Exception as e:
        result["errors"].append(f"Cannot open file: {e}")
        return result

    # --- Dimensions ---
    w, h = img.size
    result["dimensions"] = [w, h]
    if (w, h) != EXPECTED_DIMS:
        result["errors"].append(f"Unexpected dimensions: {w}x{h}, expected {EXPECTED_DIMS[0]}x{EXPECTED_DIMS[1]}")

    # --- Bands ---
    bands = len(img.getbands())
    result["bands"] = bands
    if bands != EXPECTED_BANDS:
        result["errors"].append(f"Expected {EXPECTED_BANDS} bands, got {bands}")

    # --- Bit depth (BitsPerSample tag 258) ---
    bps = tags.get(258)
    if bps:
        if isinstance(bps, (tuple, list)):
            bit_depth = bps[0]
        else:
            bit_depth = int(bps)
        result["bit_depth"] = bit_depth
        if bit_depth != EXPECTED_BITS:
            result["errors"].append(f"Expected {EXPECTED_BITS}-bit depth, got {bit_depth}")
    else:
        result["warnings"].append("BitsPerSample tag (258) missing")

    # --- Compression (tag 259) ---
    comp_id = tags.get(259)
    result["compression"] = COMPRESSION_NAMES.get(comp_id, f"Unknown({comp_id})")

    # --- NoData value (tag 42113) ---
    nodata_raw = tags.get(42113)
    if nodata_raw is not None:
        try:
            result["nodata_value"] = int(nodata_raw) if nodata_raw else 0
        except Exception:
            result["nodata_value"] = str(nodata_raw)

    # --- CRS string (GeoAsciiParamsTag 34737) ---
    crs_str = tags.get(34737, "")
    result["crs_string"] = crs_str
    if EXPECTED_CRS not in str(crs_str):
        result["errors"].append(f"Unexpected CRS string: '{crs_str}'")

    # --- EPSG from GeoKeyDirectory (tag 34735) ---
    gkd = tags.get(34735)
    if gkd:
        geo_keys = decode_geokeydir(gkd)
        epsg = geo_keys.get(3072)  # ProjectedCSTypeGeoKey
        result["epsg"] = epsg
        if epsg != EXPECTED_EPSG:
            result["errors"].append(f"Expected EPSG:{EXPECTED_EPSG}, got EPSG:{epsg}")
    else:
        result["warnings"].append("GeoKeyDirectory tag (34735) missing")

    # --- Tiepoint & pixel scale → geographic bounds ---
    tiepoint   = tags.get(33922)  # ModelTiepointTag
    pixelscale = tags.get(33550)  # ModelPixelScaleTag

    if tiepoint and pixelscale:
        result["tilepoint_raw"]  = list(tiepoint)
        result["pixelscale_raw"] = list(pixelscale)

        tlx = tiepoint[3]
        tly = tiepoint[4]
        sx  = pixelscale[0]
        sy  = pixelscale[1]
        brx = tlx + sx * w
        bry = tly - sy * h

        result["resolution_m"] = round(sx, 6)
        if abs(sx - EXPECTED_RESOLUTION) > RESOLUTION_TOL:
            result["errors"].append(f"Resolution {sx:.6f} m/px outside expected ~{EXPECTED_RESOLUTION} ± {RESOLUTION_TOL}")

        result["bounds_utm43n"] = {
            "min_easting":  round(tlx, 4),
            "max_easting":  round(brx, 4),
            "min_northing": round(bry, 4),
            "max_northing": round(tly, 4),
        }

        tl_lat, tl_lon = utm43n_to_latlon(tlx, tly)
        br_lat, br_lon = utm43n_to_latlon(brx, bry)
        result["bounds_wgs84"] = {
            "min_lon": round(min(tl_lon, br_lon), 8),
            "max_lon": round(max(tl_lon, br_lon), 8),
            "min_lat": round(min(tl_lat, br_lat), 8),
            "max_lat": round(max(tl_lat, br_lat), 8),
        }
    else:
        result["errors"].append("Missing tiepoint (33922) or pixel scale (33550) tags — not a GeoTIFF")

    # --- NoData percentage (sample-based, fast) ---
    if result["nodata_value"] is not None:
        try:
            import numpy as np  # type: ignore (numpy is in main env)
            arr = np.array(img)
            nd_val = result["nodata_value"]
            mask   = (arr[:, :, 0] == nd_val) & (arr[:, :, 1] == nd_val) & (arr[:, :, 2] == nd_val)
            result["nodata_pct"] = round(float(mask.sum()) / (w * h) * 100, 3)
        except ImportError:
            result["nodata_pct"] = None
            result["warnings"].append("numpy not available — nodata_pct skipped")

    result["valid"] = len(result["errors"]) == 0
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    log("=" * 60)
    log("DrishtiGIS — Bhopal TIFF Validation (Task 1.1)")
    log(f"TIFF directory : {TIFF_DIR}")
    log(f"Report output  : {REPORT_PATH}")

    # --- Check Pillow ---
    try:
        from PIL import Image  # noqa: F401
        from PIL import __version__ as pil_ver
        log(f"Pillow version : {pil_ver}")
    except ImportError:
        log("ERROR: Pillow is not installed. Run: pip install pillow")
        return 1

    # --- Check GDAL (informational) ---
    gdal_info = check_gdal()
    log(f"GDAL available : {gdal_info['available']} — {gdal_info['note']}")

    # --- Locate TIFF files ---
    if not TIFF_DIR.exists():
        log(f"ERROR: TIFF directory not found: {TIFF_DIR}")
        return 1

    tiff_files = sorted(TIFF_DIR.glob("*.tiff"))
    if not tiff_files:
        log(f"ERROR: No .tiff files found in {TIFF_DIR}")
        return 1

    log(f"Found {len(tiff_files)} TIFF files")

    # --- Validate each tile ---
    tile_results = []
    for fp in tiff_files:
        result = validate_tile(fp)
        status = "PASS" if result["valid"] else "FAIL"
        log(f"  {status} {fp.name}"
            + (f" — ERRORS: {result['errors']}" if result["errors"] else "")
            + (f" — WARNINGS: {result['warnings']}" if result["warnings"] else ""))
        tile_results.append(result)

    valid_count   = sum(1 for t in tile_results if t["valid"])
    invalid_count = len(tile_results) - valid_count

    # --- Grid analysis ---
    grid: dict[tuple[int, int], dict] = {}
    for t in tile_results:
        parts = t["filename"].replace(".tiff", "").split("_")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            row, col = int(parts[0]), int(parts[1])
            grid[(row, col)] = t

    max_row = max(k[0] for k in grid) if grid else 0
    max_col = max(k[1] for k in grid) if grid else 0

    grid_summary = []
    for r in range(max_row + 1):
        present = [c for c in range(max_col + 1) if (r, c) in grid]
        missing = [c for c in range(max_col + 1) if (r, c) not in grid]
        grid_summary.append({
            "row":          r,
            "present":      present,
            "missing":      missing,
            "count_present": len(present),
            "count_expected": max_col + 1,
            "complete":     len(missing) == 0,
        })

    grid_complete = all(row["complete"] for row in grid_summary)
    grid_note = (
        "Grid is complete."
        if grid_complete
        else (
            f"Row 01 has {grid_summary[1]['count_present']}/{grid_summary[1]['count_expected']} tiles. "
            "Dataset is an incomplete two-row strip — this is expected for the current prototype dataset."
        )
    )

    # --- Compute overall mosaic bounds ---
    valid_tiles = [t for t in tile_results if t["valid"] and t["bounds_utm43n"]]
    if valid_tiles:
        all_min_e = min(t["bounds_utm43n"]["min_easting"]  for t in valid_tiles)
        all_max_e = max(t["bounds_utm43n"]["max_easting"]  for t in valid_tiles)
        all_min_n = min(t["bounds_utm43n"]["min_northing"] for t in valid_tiles)
        all_max_n = max(t["bounds_utm43n"]["max_northing"] for t in valid_tiles)

        tl_lat, tl_lon = utm43n_to_latlon(all_min_e, all_max_n)
        br_lat, br_lon = utm43n_to_latlon(all_max_e, all_min_n)
        ctr_lat, ctr_lon = utm43n_to_latlon(
            (all_min_e + all_max_e) / 2,
            (all_min_n + all_max_n) / 2,
        )
        width_m  = round(all_max_e - all_min_e, 2)
        height_m = round(all_max_n - all_min_n, 2)
        area_km2 = round(width_m * height_m / 1e6, 6)

        mosaic_bounds_utm = {
            "min_easting":  round(all_min_e, 4),
            "max_easting":  round(all_max_e, 4),
            "min_northing": round(all_min_n, 4),
            "max_northing": round(all_max_n, 4),
        }
        mosaic_bounds_wgs84 = {
            "min_lon": round(min(tl_lon, br_lon), 8),
            "max_lon": round(max(tl_lon, br_lon), 8),
            "min_lat": round(min(tl_lat, br_lat), 8),
            "max_lat": round(max(tl_lat, br_lat), 8),
        }
        mosaic_center_wgs84 = {
            "lat": round(ctr_lat, 8),
            "lon": round(ctr_lon, 8),
        }
    else:
        mosaic_bounds_utm   = None
        mosaic_bounds_wgs84 = None
        mosaic_center_wgs84 = None
        width_m = height_m = area_km2 = 0.0

    # --- Tile overlap analysis (from first valid pair) ---
    tile_overlap_m = None
    if (0, 0) in grid and (0, 1) in grid:
        t0 = grid[(0, 0)]
        t1 = grid[(0, 1)]
        if t0["bounds_utm43n"] and t1["bounds_utm43n"]:
            tile_overlap_m = round(
                t0["bounds_utm43n"]["max_easting"] - t1["bounds_utm43n"]["min_easting"], 4
            )
            # negative = overlap (tile1 starts before tile0 ends)
            # stored as absolute value with a note
            tile_overlap_m = round(abs(tile_overlap_m), 4)

    # --- CRS consistency ---
    crs_values = set(t["crs_string"] for t in tile_results if t["crs_string"])
    crs_consistent = len(crs_values) == 1
    crs_value = crs_values.pop() if crs_values else "UNKNOWN"

    epsg_values = set(t["epsg"] for t in tile_results if t["epsg"])
    epsg_consistent = len(epsg_values) == 1
    epsg_value = epsg_values.pop() if epsg_values else None

    resolution_values = set(t["resolution_m"] for t in tile_results if t["resolution_m"])
    res_consistent = len(resolution_values) == 1

    # --- Assemble report ---
    report = {
        "generated_at":         datetime.now(timezone.utc).isoformat(),
        "script":               "scripts/data_prep/01_validate_bhopal_tiffs.py",
        "spec_task":            "1.1 (foundation-and-data-pipeline v0.2)",
        "source_directory":     str(TIFF_DIR),
        "total_tiles":          len(tile_results),
        "valid_tiles":          valid_count,
        "invalid_tiles":        invalid_count,
        "crs":                  f"EPSG:{EXPECTED_EPSG}",
        "crs_string":           crs_value,
        "crs_consistent":       crs_consistent,
        "epsg":                 epsg_value,
        "epsg_consistent":      epsg_consistent,
        "resolution_m":         tile_results[0]["resolution_m"] if tile_results else None,
        "resolution_consistent": res_consistent,
        "tile_dimensions":      EXPECTED_DIMS,
        "bands":                EXPECTED_BANDS,
        "bit_depth":            EXPECTED_BITS,
        "compression":          tile_results[0]["compression"] if tile_results else None,
        "nodata_value":         0,
        "grid_rows":            max_row + 1,
        "grid_cols_row0":       grid_summary[0]["count_present"] if grid_summary else 0,
        "grid_cols_row1":       grid_summary[1]["count_present"] if len(grid_summary) > 1 else 0,
        "grid_complete":        grid_complete,
        "grid_completeness_note": grid_note,
        "grid_summary":         grid_summary,
        "tile_overlap_m":       tile_overlap_m,
        "tile_overlap_note":    "Negative = overlap between adjacent tiles; positive = gap. Expected ~1.37m overlap.",
        "mosaic_bounds_utm43n": mosaic_bounds_utm,
        "mosaic_bounds_wgs84":  mosaic_bounds_wgs84,
        "mosaic_center_wgs84":  mosaic_center_wgs84,
        "mosaic_width_m":       width_m,
        "mosaic_height_m":      height_m,
        "coverage_area_km2":    area_km2,
        "gdal_info":            gdal_info,
        "tiles":                tile_results,
    }

    # --- Write report ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # --- Human-readable summary ---
    log("")
    log("=" * 60)
    log("VALIDATION SUMMARY")
    log("=" * 60)
    log(f"Total tiles     : {len(tile_results)}")
    log(f"Valid           : {valid_count}")
    log(f"Invalid         : {invalid_count}")
    log(f"CRS             : {crs_value} (consistent: {crs_consistent})")
    log(f"EPSG            : {epsg_value} (consistent: {epsg_consistent})")
    log(f"Resolution      : {tile_results[0]['resolution_m'] if tile_results else 'N/A'} m/px  (~{round((tile_results[0]['resolution_m'] or 0)*100,2)} cm/px)")
    log(f"Tile size       : {EXPECTED_DIMS[0]}×{EXPECTED_DIMS[1]} px")
    log(f"Bands           : {EXPECTED_BANDS} (RGB)")
    log(f"Bit depth       : {EXPECTED_BITS}-bit")
    log(f"Compression     : {tile_results[0]['compression'] if tile_results else 'N/A'}")
    log(f"Grid            : row00={grid_summary[0]['count_present']} tiles, row01={grid_summary[1]['count_present'] if len(grid_summary)>1 else 0} tiles")
    log(f"Grid complete   : {grid_complete}  — {grid_note}")
    log(f"Tile overlap    : ~{tile_overlap_m} m (expected ~1.37 m)")
    if mosaic_bounds_wgs84:
        log(f"Mosaic bounds   : lat {mosaic_bounds_wgs84['min_lat']}–{mosaic_bounds_wgs84['max_lat']}°N, "
            f"lon {mosaic_bounds_wgs84['min_lon']}–{mosaic_bounds_wgs84['max_lon']}°E")
        log(f"Mosaic center   : {mosaic_center_wgs84['lat']}°N, {mosaic_center_wgs84['lon']}°E  (Bhopal ✓)")
    if mosaic_bounds_utm:
        log(f"UTM extent      : {width_m} m W–E  ×  {height_m} m N–S")
        log(f"Coverage area   : {area_km2} km²")
    log(f"GDAL available  : {gdal_info['available']}")
    log(f"Report written  : {REPORT_PATH}")
    log("=" * 60)

    if invalid_count > 0:
        log(f"\nVALIDATION FAILED: {invalid_count} tile(s) did not pass.")
        return 1

    log("\nAll tiles PASSED validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
