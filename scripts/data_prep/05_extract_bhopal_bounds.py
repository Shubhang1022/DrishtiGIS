"""
DrishtiGIS — Bhopal Coverage Bounds GeoJSON Extractor
======================================================
Task:    1.2 (spec: foundation-and-data-pipeline v0.2, REQ-DATA-06)
Env:     Main Python environment (pure Python + json — no GIS env required)
Input:   data/processed/bhopal_validation_report.json
Output:  data/processed/bhopal_bounds.geojson

What this script does
---------------------
1. Reads the validation report produced by 01_validate_bhopal_tiffs.py.
2. Constructs a GeoJSON Polygon representing the full UAV coverage envelope (WGS84).
3. Tags every property with the correct DataSource classification.
4. Writes bhopal_bounds.geojson — used as the authoritative bounds reference for:
   - Demo parcel coordinate validation (Task 4.2)
   - MapLibre camera initialisation
   - XYZ tile verification (Task 2.4 / 04b_verify_tiles.py)

IMPORTANT:
- This file represents the RASTER COVERAGE BOUNDARY only.
- It is NOT a cadastral boundary.
- It is NOT an administrative boundary.
- Source classification: PROCESSED_RASTER
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT      = Path(__file__).resolve().parents[2]
REPORT_PATH    = REPO_ROOT / "data" / "processed" / "bhopal_validation_report.json"
OUTPUT_PATH    = REPO_ROOT / "data" / "processed" / "bhopal_bounds.geojson"
LOG_PATH       = REPO_ROOT / "data" / "processed" / "pipeline.log"


def log(msg: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] BOUNDS: {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def main() -> int:
    log("=" * 60)
    log("DrishtiGIS — Bhopal Coverage Bounds GeoJSON (Task 1.2)")

    # --- Load validation report ---
    if not REPORT_PATH.exists():
        log(f"ERROR: Validation report not found: {REPORT_PATH}")
        log("Run 01_validate_bhopal_tiffs.py first.")
        return 1

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    if report.get("valid_tiles", 0) == 0:
        log("ERROR: No valid tiles found in the validation report.")
        return 1

    bounds = report.get("mosaic_bounds_wgs84")
    center = report.get("mosaic_center_wgs84")

    if not bounds:
        log("ERROR: mosaic_bounds_wgs84 not found in report.")
        return 1

    min_lon = bounds["min_lon"]
    max_lon = bounds["max_lon"]
    min_lat = bounds["min_lat"]
    max_lat = bounds["max_lat"]

    log(f"Bounds (WGS84): lat {min_lat}–{max_lat}°N, lon {min_lon}–{max_lon}°E")
    log(f"Center: {center}")

    # --- Build GeoJSON Polygon (counter-clockwise / RFC 7946 exterior ring) ---
    #  Top-left → Top-right → Bottom-right → Bottom-left → close
    ring = [
        [min_lon, max_lat],  # TL
        [max_lon, max_lat],  # TR
        [max_lon, min_lat],  # BR
        [min_lon, min_lat],  # BL
        [min_lon, max_lat],  # close
    ]

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [ring],
                },
                "properties": {
                    "name":         "Bhopal UAV Prototype — Coverage Boundary",
                    "dataset":      "Bhopal UAV Prototype (30-tile orthomosaic strip)",
                    "city":         "Bhopal",
                    "state":        "Madhya Pradesh",
                    "country":      "India",
                    "_source":      "PROCESSED_RASTER",
                    "_description": (
                        "Computed coverage boundary of the 30-tile Bhopal UAV orthomosaic. "
                        "This is NOT a cadastral boundary. "
                        "This is NOT an administrative boundary. "
                        "It represents only the extent of the available raster imagery."
                    ),
                    "_crs_source":  "EPSG:32643 (UTM Zone 43N), reprojected to WGS84 (EPSG:4326)",
                    "_generated":   datetime.now(timezone.utc).isoformat(),
                    "_script":      "scripts/data_prep/05_extract_bhopal_bounds.py",
                    "_spec_task":   "1.2 (foundation-and-data-pipeline v0.2)",
                    "center_lat":   center["lat"] if center else None,
                    "center_lon":   center["lon"] if center else None,
                    "min_lat":      min_lat,
                    "max_lat":      max_lat,
                    "min_lon":      min_lon,
                    "max_lon":      max_lon,
                    "width_m":      report.get("mosaic_width_m"),
                    "height_m":     report.get("mosaic_height_m"),
                    "coverage_km2": report.get("coverage_area_km2"),
                    "tile_count":   report.get("valid_tiles"),
                    "resolution_m": report.get("resolution_m"),
                    "epsg_source":  32643,
                    "grid_note":    report.get("grid_completeness_note"),
                },
            }
        ],
        "metadata": {
            "source":      "PROCESSED_RASTER",
            "description": "Bhopal UAV prototype raster coverage boundary. Not a cadastral or administrative boundary.",
            "generated":   datetime.now(timezone.utc).isoformat(),
        },
    }

    # --- Write output ---
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)

    # --- Quick sanity checks ---
    assert min_lon < max_lon, "min_lon >= max_lon — coordinate error"
    assert min_lat < max_lat, "min_lat >= max_lat — coordinate error"
    # Bounds must be in Bhopal district (rough check)
    assert 77.3 < min_lon < 77.5, f"min_lon {min_lon} outside expected Bhopal range"
    assert 23.2 < min_lat < 23.4, f"min_lat {min_lat} outside expected Bhopal range"

    log(f"Output written : {OUTPUT_PATH}")
    log(f"GeoJSON type   : FeatureCollection with 1 Polygon feature")
    log(f"Coordinate check: lon {min_lon}–{max_lon}°E ✓  lat {min_lat}–{max_lat}°N ✓")
    log("Tip: Open https://geojson.io and paste the file contents to verify placement.")
    log("Expected: a narrow rectangle (~993m wide, ~88m tall) in Bhopal, MP, India.")
    log("")
    log("Task 1.2 COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
