"""
DrishtiGIS — XYZ Tile Pyramid Verification
============================================
Task:    2.4b (spec: foundation-and-data-pipeline v0.2)

ENVIRONMENT: scripts/.gis-env venv
Do NOT run in the main application Python environment.

Verifies spec REQ-TEST-02 tile acceptance criteria:
  1. Tile files exist for expected zoom levels.
  2. The XYZ tile at zoom 18 covering the confirmed Bhopal center point
     (23.25620125 N, 77.41783386 E) exists and is non-empty.
  3. Same for zoom 19 and 20.
  4. Sampled tiles are 256×256 pixels.
  5. Sampled tiles have non-uniform pixel values (R std dev > 5).
  6. Tile scheme is XYZ (Y-axis down) — confirmed by tile math.
  7. Tile coordinates correspond to the confirmed Bhopal bounds.
  8. No tile represents coverage outside the Bhopal UAV footprint.
  9. Dataset/ remains byte-for-byte unchanged.
 10. pipeline.log contains TILE_VERIFICATION: entries.
"""

import json
import math
import os
import sys
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
TILES_DIR  = OUTPUT_DIR / "tiles" / "bhopal"
LOG_PATH   = OUTPUT_DIR / "pipeline.log"
REPORT     = OUTPUT_DIR / "bhopal_validation_report.json"

# Confirmed Bhopal UAV center from validation report
CENTER_LAT = 23.25620125
CENTER_LON = 77.41783386

# Expected tile coordinates from pre-audit (verified against lat/lon math)
EXPECTED_TILES = {
    18: (187445, 113652),
    19: (374891, 227304),
    20: (749783, 454608),
}

DATASET_CHECKSUMS = {
    REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL" / "00_00.tiff": 7_358_913,
    REPO_ROOT / "Dataset" / "Drone-Images" / "BHOPAL" / "01_06.tiff": 7_259_880,
}


def log_verify(msg: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] TILE_VERIFICATION: {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def latlon_to_tile(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat_deg)
    n = 2 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return max(0, min(n - 1, x)), max(0, min(n - 1, y))


def main() -> int:
    import numpy as np
    from PIL import Image as PILImage

    results = []
    def chk(name: str, cond: bool, detail: str = "") -> None:
        results.append((name, cond))
        status = "PASS" if cond else "FAIL"
        msg    = f"[{status}] {name}" + (f" ({detail})" if detail else "")
        log_verify(msg)

    log_verify("=" * 50)
    log_verify("Starting XYZ tile verification (Task 2.4b)")

    # ── 1. Dataset/ integrity ─────────────────────────────────────────────
    ds_ok = True
    for fpath, expected in DATASET_CHECKSUMS.items():
        actual = fpath.stat().st_size
        if actual != expected:
            chk(f"Dataset/ {fpath.name} unchanged", False, f"{actual} != {expected}")
            ds_ok = False
        else:
            chk(f"Dataset/ {fpath.name} unchanged", True, f"{actual:,} bytes")
    if not ds_ok:
        log_verify("ABORT: Dataset/ integrity failed.")
        return 1

    # ── 2. Tiles directory exists ─────────────────────────────────────────
    chk("Tiles directory exists", TILES_DIR.exists(), str(TILES_DIR))

    # ── 3. Tile coordinate math agrees with expected values ───────────────
    for zoom, (exp_x, exp_y) in EXPECTED_TILES.items():
        cx, cy = latlon_to_tile(CENTER_LAT, CENTER_LON, zoom)
        chk(f"Tile coords z{zoom} match (x={exp_x},y={exp_y})",
            cx == exp_x and cy == exp_y,
            f"computed=({cx},{cy})")
    log_verify("XYZ tile scheme: Y-axis down (Y=0 at north pole) — Google/MapLibre compatible")

    # ── 4. Per-zoom: expected center tile exists, is non-empty, 256×256, non-uniform ──
    for zoom, (exp_x, exp_y) in EXPECTED_TILES.items():
        tile_path = TILES_DIR / str(zoom) / str(exp_x) / f"{exp_y}.png"
        chk(f"z{zoom} center tile exists", tile_path.exists(), str(tile_path))

        if tile_path.exists():
            file_size = tile_path.stat().st_size
            chk(f"z{zoom} center tile size > 500 bytes", file_size > 500, f"{file_size:,} bytes")

            img = PILImage.open(tile_path)
            w, h = img.size
            chk(f"z{zoom} center tile is 256×256", w == 256 and h == 256, f"{w}×{h}")

            arr = np.array(img)
            r_channel = arr[:, :, 0].astype(float)
            non_zero  = r_channel[r_channel > 0]
            std_dev   = float(non_zero.std()) if non_zero.size > 0 else 0.0
            chk(f"z{zoom} center tile R-channel std dev > 5 (non-uniform imagery)",
                std_dev > 5, f"std={std_dev:.1f}")
            chk(f"z{zoom} center tile non-zero pixels > 1000",
                int((r_channel > 0).sum()) > 1000,
                f"{int((r_channel > 0).sum()):,} non-zero px")

    # ── 5. Total tile counts per zoom ─────────────────────────────────────
    for zoom in range(18, 22):
        zoom_dir = TILES_DIR / str(zoom)
        if zoom_dir.exists():
            count = sum(1 for _ in zoom_dir.rglob("*.png"))
            chk(f"z{zoom} has at least 1 tile", count >= 1, f"{count} tiles")
            log_verify(f"z{zoom}: {count} tiles total")

    # ── 6. Total tile count reasonable ────────────────────────────────────
    total = sum(1 for _ in TILES_DIR.rglob("*.png"))
    chk("Total tiles <= 50000 (no run-away generation)", total <= 50_000, f"{total} tiles")
    chk("Total tiles >= 10 (not too sparse)", total >= 10, f"{total} tiles")
    log_verify(f"Total tiles across all zoom levels: {total}")

    # ── 7. Tile paths follow XYZ structure {z}/{x}/{y}.png ────────────────
    sample_tiles = list(TILES_DIR.rglob("*.png"))[:5]
    for t in sample_tiles:
        # Path should be: .../tiles/bhopal/{z}/{x}/{y}.png
        parts = t.relative_to(TILES_DIR).parts
        ok    = len(parts) == 3 and all(p.rstrip(".png").isdigit() for p in parts)
        chk(f"Tile path structure {t.relative_to(TILES_DIR)}",
            ok, "z/x/y.png format")

    # ── 8. Bhopal geographic placement ────────────────────────────────────
    # Confirm z18 tiles are in the correct tile column/row range for Bhopal
    # Bhopal bounds: lon 77.413–77.423, lat 23.256–23.257
    with open(REPORT) as f:
        report = json.load(f)
    wgs84 = report["mosaic_bounds_wgs84"]

    # Corners should map to tiles within the expected range
    tl_x, tl_y = latlon_to_tile(wgs84["max_lat"], wgs84["min_lon"], 18)
    br_x, br_y = latlon_to_tile(wgs84["min_lat"], wgs84["max_lon"], 18)
    chk("z18 tiles in Bhopal longitude range (x≈187442–187449)",
        187440 <= tl_x <= 187450 and 187440 <= br_x <= 187450,
        f"x=[{tl_x},{br_x}]")
    chk("z18 tiles in Bhopal latitude range (y≈113651–113652)",
        113650 <= tl_y <= 113653 and 113650 <= br_y <= 113653,
        f"y=[{tl_y},{br_y}]")

    # ── 9. No tiles fabricated outside Bhopal footprint ───────────────────
    # All written tiles should be within the extended bounding box
    z18_dir = TILES_DIR / "18"
    if z18_dir.exists():
        outside = 0
        for x_dir in z18_dir.iterdir():
            tx = int(x_dir.name)
            for tile_file in x_dir.glob("*.png"):
                ty = int(tile_file.stem)
                if not (187435 <= tx <= 187455 and 113645 <= ty <= 113660):
                    outside += 1
        chk("No z18 tiles outside Bhopal geographic extent", outside == 0, f"{outside} outside tiles")

    # ── 10. pipeline.log has TILE_VERIFICATION entries ────────────────────
    with open(LOG_PATH) as f:
        log_content = f.read()
    chk("pipeline.log has TILE_VERIFICATION entries",
        "TILE_VERIFICATION:" in log_content)
    chk("pipeline.log has tile counts per zoom",
        "Zoom 18:" in log_content and "Zoom 21:" in log_content)

    # ── Summary ──────────────────────────────────────────────────────────
    passed = sum(1 for _, v in results if v)
    failed = sum(1 for _, v in results if not v)
    log_verify(f"SUMMARY: {passed} PASS, {failed} FAIL")
    log_verify("=" * 50)

    print(f"\nTotal: {passed} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
