"""
Phase 23 Addendum — Comprehensive Bhopal Imagery Audit & Inventory Script
========================================================================
Inspects E:\\Shubhang\\projects\\DrishtiGIS(SIH)\\Dataset\\geospatial-data\\BHOPAL
Extracts metadata via rasterio, calculates SHA-256 hashes, checks against existing assets,
classifies files, and generates a structured manifest.
"""

import os
import json
import hashlib
from pathlib import Path
import rasterio

ROOT_DIR = Path(__file__).resolve().parents[1]
BHOPAL_DIR = ROOT_DIR / "Dataset" / "geospatial-data" / "BHOPAL"
DATASETS_FILE = ROOT_DIR / "data" / "datasets.json"
UAVPAL_DIR = ROOT_DIR / "data" / "uavpal"
OUTPUT_MANIFEST = ROOT_DIR / "data" / "ai_output" / "bhopal_imagery_manifest.json"

def calculate_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(64 * 1024):
            h.update(chunk)
    return h.hexdigest()

def get_existing_hashes_and_files():
    existing_hashes = {}
    existing_filenames = set()

    # 1. Scan datasets.json
    if DATASETS_FILE.exists():
        with open(DATASETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("datasets", []):
                existing_filenames.add(item.get("filename"))
                fpath = ROOT_DIR / item.get("file_path", "")
                if fpath.exists() and fpath.is_file():
                    existing_hashes[calculate_sha256(fpath)] = item.get("dataset_id")

    # 2. Scan UAVPal folder
    if UAVPAL_DIR.exists():
        for root, _, files in os.walk(UAVPAL_DIR):
            for fname in files:
                fpath = Path(root) / fname
                existing_filenames.add(fname)
                if fpath.is_file() and fpath.suffix.lower() in [".tif", ".tiff", ".geojson"]:
                    try:
                        existing_hashes[calculate_sha256(fpath)] = f"UAVPAL-{fname}"
                    except Exception:
                        pass

    return existing_hashes, existing_filenames

def inspect_file(filepath: Path, existing_hashes: dict, existing_filenames: set):
    rel_path = filepath.relative_to(BHOPAL_DIR).as_posix()
    file_size = filepath.stat().st_size
    sha256 = calculate_sha256(filepath)

    meta = {
        "relative_path": rel_path,
        "filename": filepath.name,
        "file_size_bytes": file_size,
        "sha256": sha256,
        "format": filepath.suffix.lower().lstrip("."),
        "width": None,
        "height": None,
        "band_count": None,
        "dtype": None,
        "crs": None,
        "bounds": None,
        "resolution": None,
        "has_georeference": False,
        "classification": "UNSET",
        "notes": []
    }

    try:
        with rasterio.open(filepath) as src:
            meta["width"] = src.width
            meta["height"] = src.height
            meta["band_count"] = src.count
            meta["dtype"] = str(src.dtypes[0]) if src.dtypes else None
            meta["crs"] = str(src.crs) if src.crs else None
            meta["resolution"] = [round(abs(src.transform.a), 6), round(abs(src.transform.e), 6)]

            if src.crs and src.bounds:
                b = src.bounds
                meta["bounds"] = [round(b.left, 6), round(b.bottom, 6), round(b.right, 6), round(b.top, 6)]
                meta["has_georeference"] = True
            else:
                meta["bounds"] = None
                meta["has_georeference"] = False
                meta["notes"].append("Lacks spatial CRS or georeference affine transform (pixel space).")
    except Exception as e:
        meta["notes"].append(f"Rasterio read warning: {str(e)}")

    # Classification logic
    if sha256 in existing_hashes:
        meta["classification"] = "PREVIOUSLY_INTEGRATED"
        meta["notes"].append(f"Byte-identical match with existing asset: {existing_hashes[sha256]}")
    elif filepath.name in existing_filenames:
        meta["classification"] = "EXACT_DUPLICATE_NAME"
        meta["notes"].append(f"Filename '{filepath.name}' exists in system store.")
    elif " (1)" in filepath.name or " (2)" in filepath.name:
        meta["classification"] = "EXACT_DUPLICATE"
        meta["notes"].append("OS duplicate naming convention detected.")
    elif not meta["has_georeference"]:
        meta["classification"] = "NEEDS_GEOREFERENCING"
        meta["notes"].append("Raster image requires georeferencing / CRS calibration.")
    else:
        meta["classification"] = "NEWLY_DISCOVERED"

    return meta

def main():
    print(f"Scanning directory: {BHOPAL_DIR}")
    if not BHOPAL_DIR.exists():
        print(f"Error: Directory {BHOPAL_DIR} does not exist.")
        return

    existing_hashes, existing_filenames = get_existing_hashes_and_files()
    print(f"Loaded {len(existing_hashes)} existing hashes, {len(existing_filenames)} filenames.")

    all_files = []
    for root, _, files in os.walk(BHOPAL_DIR):
        for f in files:
            all_files.append(Path(root) / f)

    print(f"Found {len(all_files)} total files in BHOPAL folder.")

    # Detect SHA256 duplicates within BHOPAL directory itself
    seen_hashes = {}
    inventory = []

    for fpath in sorted(all_files):
        item = inspect_file(fpath, existing_hashes, existing_filenames)
        h = item["sha256"]
        if h in seen_hashes:
            item["classification"] = "EXACT_DUPLICATE"
            item["notes"].append(f"Duplicate of {seen_hashes[h]}")
        else:
            seen_hashes[h] = item["filename"]
        inventory.append(item)

    # Summary statistics
    summary = {
        "total_files": len(inventory),
        "by_classification": {},
        "georeferenced_count": sum(1 for i in inventory if i["has_georeference"]),
        "needs_georeferencing_count": sum(1 for i in inventory if not i["has_georeference"]),
        "total_size_bytes": sum(i["file_size_bytes"] for i in inventory)
    }

    for item in inventory:
        c = item["classification"]
        summary["by_classification"][c] = summary["by_classification"].get(c, 0) + 1

    manifest = {
        "summary": summary,
        "inventory": inventory
    }

    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest successfully created at {OUTPUT_MANIFEST}")
    print("Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
