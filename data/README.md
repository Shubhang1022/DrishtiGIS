# data/

This directory holds pipeline outputs and OSM extracts derived from the raw `Dataset/` assets.

**`data/processed/` and `data/osm/` are listed in `.gitignore` — their contents are NOT committed to Git.**

Regenerate them by running the scripts in `scripts/data_prep/` (see `scripts/README.md`).

---

## Subdirectories

### `data/processed/`
Pipeline outputs from `scripts/data_prep/`:

| File | Source Script | Description |
|---|---|---|
| `bhopal_validation_report.json` | `01_validate_bhopal_tiffs.py` | GeoTIFF metadata for all 30 Bhopal tiles |
| `pipeline.log` | All pipeline scripts | Operation log with timestamps |
| `bhopal_mosaic.vrt` | `02_build_mosaic_vrt.py` | GDAL virtual mosaic (references originals) |
| `bhopal_cog.tif` | `03_build_cog.py` | Cloud Optimized GeoTIFF |
| `bhopal_bounds.geojson` | `05_extract_bhopal_bounds.py` | UAV coverage bounding box (WGS84) |
| `tiles/bhopal/{z}/{x}/{y}.png` | `04_generate_xyz_tiles.py` | XYZ raster tile pyramid for MapLibre |

### `data/osm/bhopal-extract/`
OSM features extracted from `Dataset/Drone-Images/india-260905.osm.pbf` by `scripts/data_prep/06_extract_osm_bhopal.py`:

| File | Content |
|---|---|
| `bhopal-buildings.geojson` | OSM building polygons (~2km bbox around UAV site) |
| `bhopal-roads.geojson` | OSM road linestrings |
| `bhopal-waterways.geojson` | OSM waterway linestrings and polygons |
| `bhopal-landuse.geojson` | OSM land use polygons |

All OSM files carry `"_source": "OSM_OPENSTREETMAP"` and `"_attribution": "© OpenStreetMap contributors, ODbL"` on every feature.

---

## Data Classification

Every data file in this project uses one of these classifications:

| Value | Meaning |
|---|---|
| `OFFICIAL_REFERENCE` | Authoritative government cadastral/survey data |
| `AI_DERIVED` | Output from a real AI model inference run |
| `OSM_OPENSTREETMAP` | From OpenStreetMap — supplementary context, NOT official cadastral data |
| `DEMO_DATA_PROTOTYPE_ONLY` | Created for demonstration — never authoritative |
| `RAW_RASTER_UAV` | Original unprocessed UAV imagery |
| `PROCESSED_RASTER` | Derived from RAW_RASTER_UAV via documented pipeline |
| `AI_DERIVED_DEMO` | Demo placeholder AI output — NOT from a real model run |
