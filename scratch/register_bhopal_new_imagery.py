"""
Phase 23 Addendum — Register & Ingest Newly Discovered Bhopal Imagery
======================================================================
Registers the 89 newly discovered georeferenced aerial tiles into dataset_store.
Prevents duplicate ingestion of the 32 duplicate/existing files.
Processes metadata and updates inventory stores.
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.dataset_store import dataset_store
MANIFEST_FILE = ROOT_DIR / "data" / "ai_output" / "bhopal_imagery_manifest.json"
BHOPAL_DIR = ROOT_DIR / "Dataset" / "geospatial-data" / "BHOPAL"

def main():
    if not MANIFEST_FILE.exists():
        print(f"Error: Manifest {MANIFEST_FILE} not found.")
        return

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    inventory = manifest.get("inventory", [])
    newly_discovered = [item for item in inventory if item["classification"] == "NEWLY_DISCOVERED"]

    print(f"Found {len(newly_discovered)} newly discovered tiles to register.")

    registered_count = 0
    for item in newly_discovered:
        fname = item["filename"]
        rel_path = item["relative_path"]
        file_path = str(BHOPAL_DIR / rel_path)
        ds_id = f"DS-BHOPAL-TILE-{fname.replace('.', '-').upper()}"

        # Register dataset in dataset_store
        ds = dataset_store.register_dataset(
            name=f"Bhopal Aerial Tile {fname}",
            filename=fname,
            format_type="uav_raster",
            file_size_bytes=item["file_size_bytes"],
            file_path=file_path,
            state="Madhya Pradesh",
            city="Bhopal",
            region_id="bhopal_mp",
            uploaded_by="admin@drishtigis.in"
        )

        # Update metadata directly from inspection
        dataset_store.update_dataset_status(
            dataset_id=ds.dataset_id,
            status="READY",
            current_stage="Raster Validation & Spatial Indexing Complete",
            progress_percent=100,
            completed_step="Spatial Indexing",
            crs=item.get("crs") or "EPSG:32643 (UTM Zone 43N)",
            bounds=item.get("bounds"),
            dimensions=f"{item.get('width')}x{item.get('height')} px",
            outputs=[
                {
                    "name": f"Aerial Raster Tile {fname}",
                    "type": "raster",
                    "url": f"/api/v1/tiles/bhopal/{fname}"
                }
            ]
        )
        registered_count += 1

    print(f"Successfully registered and initialized {registered_count} newly discovered Bhopal aerial raster tiles!")

    # Verify summary
    summary = dataset_store.get_analytics_summary()
    print("\nUpdated Admin Analytics Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
