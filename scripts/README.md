# scripts/

Data preparation and seeding scripts for DrishtiGIS.

---

## CRITICAL: Environment Requirements

### GIS Pipeline Scripts (`data_prep/`)

Scripts in `data_prep/` require GDAL, rasterio, geopandas, and related GIS libraries.
**DO NOT run them in the main application Python environment (Python 3.14 system install).**
Doing so risks breaking the existing fastapi/uvicorn/torch/sqlalchemy installation.

Use the dedicated GIS environment (see setup below).

### Seed Scripts (`seed/`)

Scripts in `seed/` run in the **main application Python environment** (they only use
sqlalchemy, pydantic, and json — no GDAL dependencies).

---

## GIS Environment Setup

### Option A — conda (preferred)

```bash
conda create -n drishtigis-gis python=3.11
conda activate drishtigis-gis
conda install -c conda-forge gdal rasterio geopandas shapely pyproj fiona osmium-tool
```

Verify the installation:
```bash
gdalinfo --version          # must show GDAL 3.x+
python -c "import rasterio; print(rasterio.__version__)"
python -c "import geopandas; print(geopandas.__version__)"
```

Confirm the main env is unaffected (run in a separate terminal, system Python):
```bash
python -c "import fastapi; print('Main env OK:', fastapi.__version__)"
python -c "import rasterio"   # Should FAIL here — confirms isolation
```

### Option B — OSGeo4W shell (Windows)

1. Download from https://trac.osgeo.org/osgeo4w/
2. Install packages: `gdal`, `python3-gdal`, `gdal-python-tools`
3. Run all `data_prep/` scripts from within the **OSGeo4W shell** — it provides its own
   isolated Python + GDAL environment, separate from your system Python.

**Chosen environment for this project:** _(update this line after setup)_
`[ ] conda: drishtigis-gis   [ ] OSGeo4W shell`

---

## Pipeline Execution Order

Run scripts **in order**, one at a time, verifying outputs before proceeding.

```
Phase 1 — Validation (Pillow only, runs in main Python env)
  python scripts/data_prep/01_validate_bhopal_tiffs.py
  python scripts/data_prep/05_extract_bhopal_bounds.py

Phase 2 — GIS Processing (requires GIS env — activate first)
  python scripts/data_prep/02_build_mosaic_vrt.py
  python scripts/data_prep/03_build_cog.py
  python scripts/data_prep/04_generate_xyz_tiles.py
  python scripts/data_prep/04b_verify_tiles.py

Phase 3 — OSM Extraction (requires GIS env — osmium-tool)
  python scripts/data_prep/06_extract_osm_bhopal.py
```

---

## Script Reference

| Script | Env | Input | Output | Description |
|---|---|---|---|---|
| `01_validate_bhopal_tiffs.py` | Main Python | `Dataset/Drone-Images/BHOPAL/*.tiff` | `data/processed/bhopal_validation_report.json` | Validates CRS, resolution, bands, bounds for all 30 tiles |
| `02_build_mosaic_vrt.py` | **GIS env** | 30 TIFF tiles (read-only) | `data/processed/bhopal_mosaic.vrt` | GDAL virtual mosaic, last-file-wins overlap |
| `03_build_cog.py` | **GIS env** | `bhopal_mosaic.vrt` | `data/processed/bhopal_cog.tif` | Cloud Optimized GeoTIFF with overviews |
| `04_generate_xyz_tiles.py` | **GIS env** | `bhopal_cog.tif` | `data/processed/tiles/bhopal/` | XYZ raster tile pyramid, z18–21, EPSG:3857 |
| `04b_verify_tiles.py` | **GIS env** | `data/processed/tiles/bhopal/` | (stdout + pipeline.log) | Verifies tile coordinates, placement, and imagery content |
| `05_extract_bhopal_bounds.py` | Main Python | `bhopal_validation_report.json` | `data/processed/bhopal_bounds.geojson` | Coverage bounding polygon in WGS84 |
| `06_extract_osm_bhopal.py` | **GIS env** | `india-260905.osm.pbf` (read-only) | `data/osm/bhopal-extract/*.geojson` | Extracts Bhopal-area OSM features by tag type |

---

## Raw Data Rules

- `Dataset/` is **READ ONLY**. No script may write to it.
- `Dataset/Drone-Images/india-260905.osm.pbf` must **never be loaded into the browser**.
- All outputs go to `data/processed/` or `data/osm/` (both gitignored).

---

## Seed Scripts

```bash
# Run in main application Python environment (not GIS env):
cd backend
python ../scripts/seed/seed_demo_data.py
```

The seed script inserts demo data into the database. It is idempotent — safe to re-run.
It will skip records that already exist (identified by `source = 'DEMO_DATA_PROTOTYPE_ONLY'`).
