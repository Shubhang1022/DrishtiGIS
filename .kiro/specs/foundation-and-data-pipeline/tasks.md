# Spec: DrishtiGIS Foundation and Bhopal Prototype Data Pipeline
## Implementation Tasks

**Spec ID:** foundation-and-data-pipeline  
**Version:** 0.2  
**Status:** DRAFT — Awaiting approval before implementation  
**Alignment:** CLAUDE.md · DOC/PRD.md · DOC/requirements.md  
**Changelog:** v0.2 — AI geometry correction, historical snapshot nullability, GDAL overlap strategy, GIS environment isolation, tile verification strengthening, phased execution, data integrity preservation

---

## Task Execution Rules

1. **Tasks must be executed phase by phase, with explicit verification between phases.** Do not auto-run all 30 tasks in sequence. Complete Phase 0, verify all acceptance criteria, then proceed to Phase 1, and so on.
2. Within a phase, tasks may run individually or in small dependency-safe groups — never as a single uninterrupted batch.
3. Each task has acceptance criteria that must be verified and confirmed before marking it complete and moving to the next task.
4. No task may modify files in `Dataset/` — that directory is read-only.
5. Every script that reads from `Dataset/` must verify that the source files are unmodified (by comparing expected file sizes against the audit report).
6. After completing each task, update `progress.md` with the actual status and date.
7. If a task fails, diagnose the root cause before proceeding — do not skip to the next task or make incremental patches without understanding the failure.
8. **GIS pipeline scripts (Phase 2 and Phase 3) must be run inside the dedicated GIS environment** documented in `scripts/README.md` — not in the main application Python environment.
9. Phase 2 (GDAL pipeline) is independent and can be deferred or run in parallel with Phases 3–6. Frontend and backend development do not require Phase 2 to be complete.
10. The recommended sequential gates are:
    ```
    Phase 0 → verify → Phase 1 → verify → Phase 4 + Phase 5 + Phase 6 (parallel)
                                         → Phase 2 (whenever GIS env ready)
                                         → Phase 3 (whenever GIS env ready)
    → verify all → Phase 7
    ```

---

## Phase 0 — Repository Bootstrap

### Task 0.1 — Initialize Git Repository and .gitignore

**Goal:** Create a clean git repository with correct file exclusions before any binary or sensitive file is accidentally committed.

**Steps:**
1. Initialize git: `git init` in `e:\Shubhang\projects\DrishtiGIS(SIH)\`
2. Create `.gitignore` at repository root with all entries from `requirements.md §REQ-ENV-01`
3. Create `.env.example` at repository root with all entries from `requirements.md §REQ-ENV-02`
4. Create `progress.md` at repository root (initial content: project name, date, "Phase 0 — in progress")
5. Stage only: `.gitignore`, `.env.example`, `progress.md`, `CLAUDE.md`, `DOC/PRD.md`, `DOC/requirements.md`, `.kiro/`
6. First commit: `git commit -m "chore: initialize repository with gitignore, env example, spec"`

**Acceptance Criteria:**
- [ ] `git status` shows no untracked `.tiff`, `.pbf`, `.zip` files from `Dataset/`
- [ ] `.env.example` exists and contains all required variable names
- [ ] `.gitignore` exists and correctly excludes binary data files
- [ ] `progress.md` exists

**Files Created/Modified:**
- `.gitignore` (new)
- `.env.example` (new)
- `progress.md` (new)

**Do NOT modify:**
- Any file in `Dataset/`
- `CLAUDE.md`
- `DOC/PRD.md`
- `DOC/requirements.md`

---

### Task 0.2 — Create Top-Level Directory Structure

**Goal:** Create the project skeleton directories so subsequent tasks have target locations.

**Steps:**
1. Create directories:
   - `data/processed/`
   - `data/osm/bhopal-extract/`
   - `scripts/data_prep/`
   - `scripts/seed/`
   - `drishtigis/` (Next.js project root — empty for now)
   - `backend/` (FastAPI root — empty for now)
2. Create a `scripts/README.md` explaining what each script does and the required execution order
3. Create a `data/README.md` explaining that `data/processed/` and `data/osm/` are gitignored pipeline outputs

**Acceptance Criteria:**
- [ ] All directories exist
- [ ] `scripts/README.md` exists with pipeline execution instructions
- [ ] `data/README.md` exists with explanation

**Files Created:**
- `data/README.md`
- `scripts/README.md`
- Directory structure as above

---

## Phase 1 — Bhopal Data Validation

### Task 1.1 — Write Bhopal TIFF Validation Script

**Goal:** Create an authoritative, re-runnable validation script that formally documents the properties of all 30 Bhopal TIFF tiles.

**Steps:**
1. Create `scripts/data_prep/01_validate_bhopal_tiffs.py`
2. The script must:
   - Import Pillow (already installed) as primary validation tool
   - Optionally import rasterio if available for cross-validation
   - Check all 30 TIFF files in `Dataset/Drone-Images/BHOPAL/`
   - For each file, validate: readability, CRS string, EPSG code, pixel resolution, dimensions, band count, bit depth, compression, NoData value, tiepoint coordinates, bounding box
   - Compute overall mosaic bounds in EPSG:32643 and EPSG:4326 (use the UTM→WGS84 conversion already verified in the audit)
   - Detect and report tile overlap
   - Detect missing tiles (row 01 is incomplete — this must be reported, not silently ignored)
   - Check GDAL availability and report version if present
   - Write full results to `data/processed/bhopal_validation_report.json`
   - Print a human-readable summary to stdout
3. The script must exit with code 0 on success, non-zero on validation failure
4. The script must never write to `Dataset/`

**Validation report JSON structure:**
```json
{
  "generated_at": "ISO timestamp",
  "total_tiles": 30,
  "valid_tiles": 30,
  "invalid_tiles": 0,
  "crs": "EPSG:32643",
  "crs_consistent": true,
  "resolution_m": 0.021713,
  "tile_dimensions": [2048, 2048],
  "bands": 3,
  "bit_depth": 8,
  "compression": "JPEG",
  "nodata_value": 0,
  "grid_rows": 2,
  "grid_cols_row0": 23,
  "grid_cols_row1": 7,
  "grid_complete": false,
  "grid_completeness_note": "Row 01 has 7/23 tiles. Dataset is an incomplete two-row strip.",
  "tile_overlap_m": 1.37,
  "mosaic_bounds_utm43n": {
    "min_easting": 746867.76,
    "max_easting": 747860.39,
    "min_northing": 2573899.47,
    "max_northing": 2573987.04
  },
  "mosaic_bounds_wgs84": {
    "min_lon": 77.4130,
    "max_lon": 77.4227,
    "min_lat": 23.2557,
    "max_lat": 23.2567
  },
  "mosaic_center_wgs84": {
    "lon": 77.4178,
    "lat": 23.2562
  },
  "coverage_area_km2": 0.0593,
  "tiles": [
    {
      "filename": "00_00.tiff",
      "valid": true,
      "crs": "EPSG:32643",
      "resolution_m": 0.021713,
      "dimensions": [2048, 2048],
      "bands": 3,
      "bounds_utm43n": {...},
      "bounds_wgs84": {...},
      "nodata_pct": 0.1
    }
  ]
}
```

**Acceptance Criteria:**
- [ ] Script runs without errors using only Pillow (no rasterio required)
- [ ] `data/processed/bhopal_validation_report.json` is created
- [ ] All 30 tiles reported as valid
- [ ] CRS confirmed EPSG:32643 for all tiles
- [ ] Incomplete row 01 is reported (not silently ignored)
- [ ] WGS84 bounds match the audit results: ~(77.413°E, 23.256°N) to ~(77.423°E, 23.257°N)
- [ ] Script does not modify any file in `Dataset/`

**Files Created/Modified:**
- `scripts/data_prep/01_validate_bhopal_tiffs.py` (new)
- `data/processed/bhopal_validation_report.json` (new output)

---

### Task 1.2 — Extract Bhopal Coverage Bounds GeoJSON

**Goal:** Create a GeoJSON file representing the actual UAV imagery coverage area, which serves as the authoritative reference for all subsequent parcel and feature placement.

**Steps:**
1. Create `scripts/data_prep/05_extract_bhopal_bounds.py`
2. Read bounds from `data/processed/bhopal_validation_report.json`
3. Construct a GeoJSON polygon representing the full coverage envelope (WGS84)
4. Add source metadata:
   ```json
   {
     "_source": "PROCESSED_RASTER",
     "_dataset": "Bhopal UAV Prototype",
     "_description": "Computed coverage boundary of 30-tile Bhopal UAV orthomosaic. Not a cadastral boundary.",
     "_crs_source": "EPSG:32643 (UTM Zone 43N), reprojected to WGS84 (EPSG:4326)"
   }
   ```
5. Write to `data/processed/bhopal_bounds.geojson`

**Acceptance Criteria:**
- [ ] `data/processed/bhopal_bounds.geojson` is valid GeoJSON
- [ ] Polygon vertices fall within the expected WGS84 bounds
- [ ] Opening in geojson.io shows a rectangle in Bhopal, Madhya Pradesh, India
- [ ] `_source` field is present and set to `"PROCESSED_RASTER"`

**Files Created/Modified:**
- `scripts/data_prep/05_extract_bhopal_bounds.py` (new)
- `data/processed/bhopal_bounds.geojson` (new output)

---

## Phase 2 — GIS Processing Pipeline (Requires GDAL)

> **Note:** Tasks 2.1–2.3 require GDAL tools. If GDAL is not yet installed, skip to Phase 3 and return here. The frontend and backend foundations can be built in parallel.

### Task 2.1 — Set Up Dedicated GIS Environment and Install GIS Dependencies

**Goal:** Install GDAL, rasterio, geopandas, and related tools in a **dedicated, isolated environment** that does not touch the system Python 3.14 installation or the backend application environment.

**Steps:**
1. Choose one of the two isolation options and document the choice in `scripts/README.md`:
   - **Option A (preferred): conda**
     ```bash
     conda create -n drishtigis-gis python=3.11
     conda activate drishtigis-gis
     conda install -c conda-forge gdal rasterio geopandas shapely pyproj fiona osmium-tool
     ```
   - **Option B: OSGeo4W shell (Windows)**
     - Download from https://trac.osgeo.org/osgeo4w/
     - Install: `gdal`, `python3-gdal`, `gdal-python-tools`
     - All pipeline scripts run from within the OSGeo4W shell — this is its own isolated Python environment
2. Verify the installation (run inside the GIS environment only):
   ```bash
   gdalinfo --version     # must show GDAL 3.x+
   python -c "import rasterio; print(rasterio.__version__)"
   python -c "from osgeo import gdal; print(gdal.__version__)"
   python -c "import geopandas; print(geopandas.__version__)"
   python -c "import shapely; print(shapely.__version__)"
   python -c "import pyproj; print(pyproj.__version__)"
   ```
3. Verify the main application Python is unaffected:
   ```bash
   # In a separate terminal (system Python, NOT the GIS env):
   python -c "import fastapi; print('Main env intact:', fastapi.__version__)"
   python -c "import rasterio"  # This SHOULD fail in the main env — confirms isolation
   ```
4. Run `gdalinfo Dataset/Drone-Images/BHOPAL/00_00.tiff` (inside the GIS env) and confirm the output matches the Pillow-derived validation report for CRS, bounds, and resolution

**Acceptance Criteria:**
- [ ] GIS environment name and activation command documented in `scripts/README.md`
- [ ] `gdalinfo --version` shows GDAL 3.x+ (inside the GIS env)
- [ ] `rasterio` importable (inside the GIS env)
- [ ] `geopandas` importable (inside the GIS env)
- [ ] `gdalinfo` on `00_00.tiff` matches validation report
- [ ] Main application Python still starts `uvicorn` without errors (confirms isolation — no package breakage)
- [ ] `scripts/README.md` updated with activation instructions

**Files Created/Modified:**
- `scripts/README.md` (updated with GIS environment setup instructions)

---

### Task 2.2 — Build Bhopal GDAL Virtual Mosaic

**Goal:** Create a GDAL Virtual Raster (VRT) that combines all 30 tiles into a single logical raster without duplicating pixel data.

**Steps:**
1. Create `scripts/data_prep/02_build_mosaic_vrt.py`
2. Add environment header comment at top of script:
   ```python
   # ENVIRONMENT: drishtigis-gis (conda) or OSGeo4W Python shell
   # Do NOT run in the main application Python environment.
   ```
3. The script must:
   - Locate all 30 `.tiff` files in `Dataset/Drone-Images/BHOPAL/` (READ ONLY)
   - Sort the file list lexicographically for deterministic ordering: `sorted(glob(...))`
   - Build the VRT with default overlap handling (last-file-wins by lexicographic sort order):
     ```bash
     gdalbuildvrt -resolution highest data/processed/bhopal_mosaic.vrt \
       Dataset/Drone-Images/BHOPAL/00_00.tiff \
       Dataset/Drone-Images/BHOPAL/00_01.tiff \
       ... (all 30 sorted)
     ```
   - Log the overlap strategy to `data/processed/pipeline.log`:
     ```
     Overlap strategy: gdalbuildvrt default (last-file-wins).
     Files sorted lexicographically for reproducibility.
     Overlap = ~1.37m between adjacent tiles.
     Blend/average NOT applied at VRT stage.
     ```
   - Verify the VRT was created and is readable (run `gdalinfo` on it)
   - The script must never write to `Dataset/`
4. After generating the VRT and later the XYZ tiles, visually inspect at least one tile at a seam boundary. If hard-edge seam artefacts are visible, document this finding in `pipeline.log` — a separate blending step can be added in a follow-up task.

**Acceptance Criteria:**
- [ ] `data/processed/bhopal_mosaic.vrt` is created
- [ ] VRT is readable by `gdalinfo data/processed/bhopal_mosaic.vrt`
- [ ] VRT CRS is EPSG:32643
- [ ] VRT bounds match the mosaic bounds from the validation report
- [ ] `pipeline.log` records the exact overlap strategy used (not "BLEND or LAST_WINS" — one specific strategy)
- [ ] No files in `Dataset/` were modified (verify by file size check against validation report)
- [ ] Script has environment comment header

**Files Created/Modified:**
- `scripts/data_prep/02_build_mosaic_vrt.py` (new)
- `data/processed/bhopal_mosaic.vrt` (new output)
- `data/processed/pipeline.log` (updated)

---

### Task 2.3 — Generate Cloud Optimized GeoTIFF (COG)

**Goal:** Create a single Cloud Optimized GeoTIFF from the VRT mosaic, suitable for efficient range-request serving.

**Steps:**
1. Create `scripts/data_prep/03_build_cog.py`
2. The script must run:
   ```bash
   gdal_translate \
     -of COG \
     -co COMPRESS=JPEG \
     -co QUALITY=85 \
     -co OVERVIEWS=AUTO \
     data/processed/bhopal_mosaic.vrt \
     data/processed/bhopal_cog.tif
   ```
3. Verify COG validity using `gdal_translate` output or `rio cogeo validate` if available
4. Log to `data/processed/pipeline.log`

**Acceptance Criteria:**
- [ ] `data/processed/bhopal_cog.tif` is created
- [ ] File is valid COG format
- [ ] CRS is EPSG:32643 (preserved from source)
- [ ] Internal overviews are present
- [ ] File size is significantly smaller than 206 MB combined source (JPEG compression)

**Files Created/Modified:**
- `scripts/data_prep/03_build_cog.py` (new)
- `data/processed/bhopal_cog.tif` (new output)
- `data/processed/pipeline.log` (updated)

---

### Task 2.4 — Generate XYZ Raster Tile Pyramid

**Goal:** Create a web-compatible XYZ tile pyramid for MapLibre raster source consumption, with full verification that the tiles contain real Bhopal imagery at the correct geographic coordinates.

**Steps:**
1. Create `scripts/data_prep/04_generate_xyz_tiles.py`
2. Add environment header comment: `# ENVIRONMENT: drishtigis-gis (conda) or OSGeo4W Python shell`
3. Run tile generation:
   ```bash
   gdal2tiles.py \
     --zoom=18-21 \
     --resampling=near \
     --tilesize=256 \
     --webviewer=none \
     --xyz \
     data/processed/bhopal_cog.tif \
     data/processed/tiles/bhopal/
   ```
   Notes:
   - Max zoom is 21 (not 22) — at 2 cm/pixel, zoom 21 = ~0.075 m/pixel tile resolution, which is sufficient. Zoom 22 would multiply tile count ~4× with diminishing visual gain.
   - `gdal2tiles.py` reprojects from EPSG:32643 to EPSG:3857 automatically during tiling
   - `--xyz` flag ensures Google/MapLibre-compatible XYZ tile scheme (not TMS)
4. After generation, run a **tile verification sub-script** `scripts/data_prep/04b_verify_tiles.py` that:
   a. Computes the expected XYZ tile coordinates at zoom 18 covering the Bhopal center point (~23.2562°N, ~77.4178°E) using the standard Web Mercator tile formula
   b. Checks that the computed tile file exists at `data/processed/tiles/bhopal/18/{x}/{y}.png`
   c. Opens that tile as a PIL Image and confirms:
      - File size > 500 bytes (not a blank/transparent tile)
      - Image dimensions are 256×256 pixels
      - Pixel values are non-uniform (std deviation of R channel > 5 — confirms actual imagery content, not a solid fill)
   d. Repeats checks for zoom levels 19 and 20 using the same center point
   e. Counts total tiles generated at zoom 18 and logs the count
   f. Reports tile scheme: XYZ (Google-compatible, Y-axis down), confirms by checking tile path structure
   g. Logs all verification results to `pipeline.log` with a `TILE_VERIFICATION:` prefix
5. Log total tile counts per zoom level to `data/processed/pipeline.log`
6. Warn if total tile count exceeds 50,000 (zoom range may be too wide)

**Acceptance Criteria:**
- [ ] `data/processed/tiles/bhopal/` directory is populated
- [ ] Computed XYZ tile at zoom 18 for Bhopal center exists and is non-empty
- [ ] Computed XYZ tiles at zoom 19 and 20 for Bhopal center exist and are non-empty
- [ ] Sampled tile is 256×256 pixels
- [ ] Sampled tile has non-uniform pixel values (std deviation R channel > 5)
- [ ] Tile scheme is XYZ (Y-axis down), confirmed by `--xyz` flag and path inspection
- [ ] `pipeline.log` contains `TILE_VERIFICATION:` entries with zoom levels and tile coordinates verified
- [ ] Total tile count is logged

**Files Created/Modified:**
- `scripts/data_prep/04_generate_xyz_tiles.py` (new)
- `scripts/data_prep/04b_verify_tiles.py` (new)
- `data/processed/tiles/bhopal/` (new output, gitignored)
- `data/processed/pipeline.log` (updated)

---

## Phase 3 — OSM Data Extraction

### Task 3.1 — Write Bhopal OSM Extraction Script

**Goal:** Extract Bhopal-area features (buildings, roads, waterways, landuse) from the India OSM PBF as small, usable GeoJSON files.

**Steps:**
1. Create `scripts/data_prep/06_extract_osm_bhopal.py`
2. The script must:
   - Check if `osmium` CLI is available on PATH; if not, print installation instructions and exit gracefully
   - Check if `pyosmium` is available as a Python fallback; if so, use it
   - If neither is available, print clear instructions and exit with a non-zero code
   - Extract bbox: `77.38,23.24,77.44,23.27` from `Dataset/Drone-Images/india-260905.osm.pbf`
   - Convert to GeoJSON split by feature type:
     - `data/osm/bhopal-extract/bhopal-buildings.geojson` (features with `building=*`)
     - `data/osm/bhopal-extract/bhopal-roads.geojson` (features with `highway=*`)
     - `data/osm/bhopal-extract/bhopal-waterways.geojson` (features with `waterway=*` or `natural=water`)
     - `data/osm/bhopal-extract/bhopal-landuse.geojson` (features with `landuse=*`)
   - Add `_source: "OSM_OPENSTREETMAP"` and `_attribution: "© OpenStreetMap contributors, ODbL"` to each feature
   - Report feature counts for each output file
   - Verify no output file exceeds 10 MB (if so, warn and continue)
3. The script must never write to `Dataset/`
4. The India OSM PBF must only be read, never modified

**Acceptance Criteria:**
- [ ] All 4 output GeoJSON files are created
- [ ] Every feature in every file has `_source: "OSM_OPENSTREETMAP"`
- [ ] Every feature in every file has `_attribution` field
- [ ] Buildings GeoJSON contains polygon features (not just points)
- [ ] Roads GeoJSON contains linestring features
- [ ] Files are valid GeoJSON (can be loaded in geojson.io)
- [ ] No file in `Dataset/` was modified

**Files Created/Modified:**
- `scripts/data_prep/06_extract_osm_bhopal.py` (new)
- `data/osm/bhopal-extract/bhopal-buildings.geojson` (new)
- `data/osm/bhopal-extract/bhopal-roads.geojson` (new)
- `data/osm/bhopal-extract/bhopal-waterways.geojson` (new)
- `data/osm/bhopal-extract/bhopal-landuse.geojson` (new)

---

## Phase 4 — Demo Data Package

### Task 4.1 — Create TypeScript Types for Demo Data

**Goal:** Define all TypeScript interfaces and enums for the demo data module before any GeoJSON is created.

**Steps:**
1. Create `drishtigis/lib/demo-data/types.ts` with:
   - `DataSource` enum (all 7 values from `requirements.md §3.3`)
   - `DemoParcel` interface (GeoJSON Feature with typed properties)
   - `DemoAIFeature` interface
   - `DemoDiscrepancy` interface
   - `DemoProperty` interface
   - `DemoDataset` interface
   - All as per `design.md §3.5`
2. The `city` field on `DemoParcel` and `DemoProperty` must be typed as the string literal `"Bhopal"` — TypeScript will prevent accidentally using another city name

**Acceptance Criteria:**
- [ ] `types.ts` compiles without TypeScript errors
- [ ] `DataSource` enum has all 7 values
- [ ] `DemoParcel.properties.city` type is `'Bhopal'` (string literal, not `string`)
- [ ] All interfaces have `_source` as a required field

**Files Created:**
- `drishtigis/lib/demo-data/types.ts` (new)

---

### Task 4.2 — Create Demo Parcel GeoJSON

**Goal:** Create 3 demo parcel polygons that fall within the confirmed Bhopal TIFF coverage area, clearly labeled as prototype demo data.

**Steps:**
1. Verify that `data/processed/bhopal_bounds.geojson` exists (from Task 1.2)
2. Manually construct 3 GeoJSON polygon features within the bounds `77.413°E–77.423°E, 23.2557°N–23.2567°N`:
   - DRS-BPL-00101 (Plot 101, Residential, ~600 m²)
   - DRS-BPL-00102 (Plot 102, Residential, ~550 m²)
   - DRS-BPL-00103 (Plot 103, Commercial, ~720 m²)
3. Every feature MUST have:
   - `"_source": "DEMO_DATA_PROTOTYPE_ONLY"`
   - `"_disclaimer": "This parcel is prototype demonstration data only. It is not derived from official government cadastral records."`
   - `"_datasetLabel": "Prototype Dataset — Bhopal"`
   - `"city": "Bhopal"` (never another city)
   - `"state": "Madhya Pradesh"`
4. Create `drishtigis/lib/demo-data/bhopal-parcels.geojson`
5. Write a small Python verification script that checks all coordinates fall within the TIFF bounds

**Acceptance Criteria:**
- [ ] File is valid GeoJSON FeatureCollection
- [ ] All 3 features are Polygon geometry within the TIFF bounds
- [ ] All 3 features have `_source: "DEMO_DATA_PROTOTYPE_ONLY"`
- [ ] No feature has `city` set to anything other than `"Bhopal"`
- [ ] Coordinates verified against `bhopal_bounds.geojson`
- [ ] Loading in geojson.io shows parcels in Bhopal, India

**Files Created:**
- `drishtigis/lib/demo-data/bhopal-parcels.geojson` (new)

---

### Task 4.3 — Create Demo AI Feature GeoJSON

**Goal:** Create demo AI feature detection results (building footprints) that spatially represent a discrepancy by partially extending outside the demo parcel boundaries. The discrepancy must be geometrically real, not just a numeric claim.

**Steps:**
1. Create two building polygon geometries. Each polygon must **partially intersect the parcel boundary and extend outside it** — this is the geometrically correct representation of a building detection whose footprint exceeds the recorded parcel area:
   - **AI-BLD-00101:** A polygon centered over parcel DRS-BPL-00101 that extends ~3–4m beyond one edge of the parcel. The area of this polygon must be computed from the actual coordinates (not reverse-engineered from the discrepancy value). Target computed area: ~672 m²
   - **AI-BLD-00102:** A polygon that partially overlaps the edge of parcel DRS-BPL-00102 on one side, extending ~2–3m outside. Target computed area: ~575 m²
2. Compute the actual areas of both polygons using the Shoelace formula or equivalent (not GDAL/shapely — a pure Python calculation is sufficient for verification). The `area_m2` field must reflect the computed area of the polygon geometry.
3. Every feature MUST have:
   - `"_source": "AI_DERIVED_DEMO"`
   - `"_disclaimer": "AI-derived observation from prototype demonstration model. Not a legal or official determination. Requires field verification."`
   - `"confidence"`: a float between 0.85 and 0.95
   - `"model": "demo_placeholder_v0.1"`
   - `"model_version": "0.1-demo"`
   - `"feature_type": "building"`
   - `"area_m2"`: computed from actual polygon vertices (not an asserted value)
4. Create `drishtigis/lib/demo-data/bhopal-ai-features.geojson`
5. Add a note in `bhopal-discrepancies.json` explaining the spatial basis: `"spatial_basis": "AI polygon partially extends outside parcel boundary. Discrepancy reflects area of polygon outside parcel extent."`

**Acceptance Criteria:**
- [ ] File is valid GeoJSON FeatureCollection
- [ ] Both AI polygons overlap their corresponding parcel boundaries (do NOT sit fully inside)
- [ ] Both AI polygons are fully within the overall TIFF coverage area
- [ ] `area_m2` values reflect the actual computed polygon area (not backwards-derived)
- [ ] All features have `_source: "AI_DERIVED_DEMO"`
- [ ] All features have confidence values between 0 and 1
- [ ] When loaded in geojson.io alongside the parcel GeoJSON, the overlap is visually apparent
- [ ] No feature claims to be from a real AI model version

**Files Created:**
- `drishtigis/lib/demo-data/bhopal-ai-features.geojson` (new)

---

### Task 4.4 — Create Demo Discrepancy Records

**Goal:** Create demo discrepancy records that link the demo parcels to the demo AI features, using the exact language prescribed in PRD §16 and CLAUDE.md §26.

**Steps:**
1. Create `drishtigis/lib/demo-data/bhopal-discrepancies.json` with 2 discrepancy records:
   - Discrepancy 1: DRS-BPL-00101 (600 m²) vs AI-BLD-00101 (672 m²) → +72 m², +12.0%, severity: medium
   - Discrepancy 2: DRS-BPL-00102 (550 m²) vs AI-BLD-00102 (575 m²) → +25 m², +4.5%, severity: low
2. Every record MUST have:
   - `"description": "The AI-derived building footprint differs from the recorded property area. This is a potential discrepancy that requires field verification."`
   - `"ui_label": "Potential discrepancy — Requires verification"`
   - `"legal_status": null` (never claim illegal construction)
   - `"_source": "DEMO_DATA_PROTOTYPE_ONLY"`
   - `"_disclaimer": "This potential discrepancy was detected by a demonstration AI model and is not a legal determination."` 
3. The language "illegal construction", "fraud", "encroachment", "violation" must NOT appear anywhere in this file

**Acceptance Criteria:**
- [ ] File is valid JSON
- [ ] Both records link to real parcel IDs and feature IDs from the GeoJSON files
- [ ] `legal_status` is null on all records
- [ ] The words "illegal", "fraud", "encroachment", "violation" do not appear
- [ ] Both records have `_source: "DEMO_DATA_PROTOTYPE_ONLY"`

**Files Created:**
- `drishtigis/lib/demo-data/bhopal-discrepancies.json` (new)

---

### Task 4.5 — Create Demo Property Records

**Goal:** Create demo property records corresponding to each parcel, labeled for Bhopal prototype only.

**Steps:**
1. Create `drishtigis/lib/demo-data/properties.json` with 3 property records (one per parcel)
2. Each record links to a parcel via `parcel_id`
3. Every record MUST have:
   - `"city": "Bhopal"` (never any other city)
   - `"state": "Madhya Pradesh"`
   - `"source_label": "Prototype Dataset — Bhopal"` (as prescribed in CLAUDE.md §34)
   - `"_source": "DEMO_DATA_PROTOTYPE_ONLY"`
   - `"_disclaimer": "This is prototype demonstration data. Not an official government property record."`
   - `"record_status": "Demo record"`

**Acceptance Criteria:**
- [ ] File is valid JSON
- [ ] All 3 records have `city: "Bhopal"`
- [ ] No record has `city` set to Lucknow, Delhi, Chennai, or any other city
- [ ] All records have `_source: "DEMO_DATA_PROTOTYPE_ONLY"`
- [ ] `source_label` matches exactly `"Prototype Dataset — Bhopal"`

**Files Created:**
- `drishtigis/lib/demo-data/properties.json` (new)

---

### Task 4.6 — Create Demo Data TypeScript Barrel Export

**Goal:** Create a typed TypeScript module that exports all demo data for use in the frontend.

**Steps:**
1. Create `drishtigis/lib/demo-data/index.ts` that:
   - Imports all GeoJSON and JSON files as typed objects
   - Validates that all imported data conforms to the TypeScript interfaces defined in `types.ts`
   - Exports named constants: `DEMO_PARCELS`, `DEMO_AI_FEATURES`, `DEMO_DISCREPANCIES`, `DEMO_PROPERTIES`
   - Exports a `DEMO_DATA_DISCLAIMER` constant string for UI display
   - Exports the `DataSource` enum
2. The module must compile without TypeScript errors
3. Add a prominent comment at the top:
   ```typescript
   /**
    * DEMO DATA — PROTOTYPE ONLY
    * 
    * This module contains demonstration data for the DrishtiGIS prototype.
    * All data in this module is clearly labeled as prototype/demo data.
    * 
    * NONE of this data represents:
    * - Official government cadastral records
    * - Verified property ownership
    * - Legal property boundaries
    * - Authoritative survey data
    * 
    * The AI features in this module are placeholder demonstrations,
    * not real AI model output.
    * 
    * All parcel geometries are within the Bhopal UAV prototype dataset area.
    * City: Bhopal, Madhya Pradesh, India.
    */
   ```

**Acceptance Criteria:**
- [ ] `index.ts` compiles without TypeScript errors
- [ ] All exports are typed (not `any`)
- [ ] Disclaimer comment is present at the top of the file
- [ ] `DataSource` enum is exported

**Files Created:**
- `drishtigis/lib/demo-data/index.ts` (new)

---

## Phase 5 — Frontend Foundation

### Task 5.1 — Initialize Next.js Project

**Goal:** Create the Next.js 14 project with TypeScript, Tailwind, and the App Router.

**Steps:**
1. In the workspace root, run:
   ```bash
   npx create-next-app@latest drishtigis \
     --typescript \
     --tailwind \
     --app \
     --no-src-dir \
     --import-alias "@/*" \
     --no-git
   ```
   (Do not initialize a separate git repo inside drishtigis — the root repo is already initialized)
2. Add `drishtigis/node_modules/` and `drishtigis/.next/` to `.gitignore` at repository root if not already present
3. Verify `npm run dev` starts successfully and `http://localhost:3000` responds

**Acceptance Criteria:**
- [ ] `drishtigis/package.json` exists with Next.js 14+ listed
- [ ] `npm run dev` starts without errors
- [ ] `http://localhost:3000` returns a page (default Next.js page is fine at this stage)
- [ ] `npm run build` exits 0 with zero TypeScript errors

**Files Created/Modified:**
- `drishtigis/` — full Next.js project structure
- `.gitignore` (updated with Node/Next entries if needed)

---

### Task 5.2 — Configure Design Tokens and Typography

**Goal:** Configure Tailwind CSS with the DrishtiGIS design system colors and font families.

**Steps:**
1. Update `drishtigis/tailwind.config.ts` with the color palette and font families from `design.md §3.2`
2. Add Google Fonts (Playfair Display + Inter) to `drishtigis/app/layout.tsx` using `next/font/google`
3. Apply font CSS variables to the root `<html>` element: `className={${displayFont.variable} ${uiFont.variable}}`
4. Add base CSS in `drishtigis/app/globals.css`:
   - Set `background-color: var(--color-cream)` on `body`
   - Set default `font-family: var(--font-ui)` on `body`
5. Create a simple `drishtigis/app/design-system/page.tsx` that renders swatches of each color token — this page will be used to visually verify the design system is working

**Acceptance Criteria:**
- [ ] `tailwind.config.ts` includes all DrishtiGIS color tokens
- [ ] `bg-cream`, `text-forest`, `text-ochre` etc. classes are usable in components
- [ ] Visiting `/design-system` in dev mode shows color swatches
- [ ] `npm run build` still exits 0

**Files Created/Modified:**
- `drishtigis/tailwind.config.ts` (modified)
- `drishtigis/app/layout.tsx` (modified)
- `drishtigis/app/globals.css` (modified)
- `drishtigis/app/design-system/page.tsx` (new)

---

### Task 5.3 — Install and Configure shadcn/ui

**Goal:** Initialize the shadcn/ui component library with the DrishtiGIS color scheme.

**Steps:**
1. Run `npx shadcn-ui@latest init` in `drishtigis/`:
   - Style: `default`
   - Base color: Custom (configure to use cream/forest palette)
   - CSS variables: Yes
   - `components.json` configuration
2. Install initial components needed for the foundation:
   ```bash
   npx shadcn-ui@latest add button
   npx shadcn-ui@latest add input
   npx shadcn-ui@latest add card
   npx shadcn-ui@latest add separator
   npx shadcn-ui@latest add badge
   npx shadcn-ui@latest add skeleton
   ```
3. Update the generated shadcn CSS variables in `globals.css` to use the DrishtiGIS cream/forest/ochre colors instead of the default slate/neutral palette
4. Verify that `<Button>` and `<Card>` render with the correct DrishtiGIS visual language

**Acceptance Criteria:**
- [ ] `drishtigis/components/ui/` contains generated shadcn components
- [ ] `components.json` exists
- [ ] CSS variables reflect DrishtiGIS palette (not default shadcn slate)
- [ ] `npm run build` exits 0

**Files Created/Modified:**
- `drishtigis/components.json` (new)
- `drishtigis/components/ui/` (new directory with shadcn components)
- `drishtigis/app/globals.css` (updated with shadcn CSS variables)

---

### Task 5.4 — Install MapLibre GL JS

**Goal:** Install MapLibre GL JS and configure it for Next.js client-only usage.

**Steps:**
1. Install MapLibre: `npm install maplibre-gl`
2. Install type definitions: `npm install --save-dev @types/maplibre-gl` (if needed — maplibre-gl includes its own types)
3. Install Anime.js: `npm install animejs`; `npm install --save-dev @types/animejs`
4. Update `drishtigis/next.config.ts` to handle MapLibre's browser-only dependencies:
   ```typescript
   // Handle maplibre-gl which requires browser globals
   webpack: (config, { isServer }) => {
     if (isServer) {
       config.externals = [...(config.externals || []), 'maplibre-gl'];
     }
     return config;
   }
   ```

**Acceptance Criteria:**
- [ ] `maplibre-gl` appears in `package.json` dependencies
- [ ] `animejs` appears in `package.json` dependencies
- [ ] `npm run build` exits 0 (MapLibre must not cause SSR build failures)

**Files Created/Modified:**
- `drishtigis/package.json` (updated)
- `drishtigis/next.config.ts` (updated)

---

### Task 5.5 — Create Base MapLibre Component

**Goal:** Create the reusable client-only MapLibre map component and verify it renders correctly with Bhopal coordinates.

**Steps:**
1. Create `drishtigis/lib/gis/bounds.ts` with the `BHOPAL_UAV_BOUNDS` and `BHOPAL_CITY` constants from `design.md §3.4`
2. Create `drishtigis/components/map/MapLibreMap.tsx` as a `'use client'` component using the design from `design.md §3.4`
3. The component must:
   - Accept `center`, `zoom`, `style` props with sensible defaults
   - Use a free/no-key-required tile style (OpenFreeMap or equivalent)
   - Clean up map on unmount (`map.remove()` in useEffect cleanup)
   - Handle the SSR safety concern: check `typeof window !== 'undefined'` before accessing browser APIs
4. Create `drishtigis/app/app/map/page.tsx` that:
   - Imports `MapLibreMap` via `next/dynamic` with `{ ssr: false }`
   - Centers the map on Bhopal at zoom 17
   - Displays a `<MapSkeleton />` loading state while the component loads
   - Shows a small info overlay reading "Prototype Dataset — Bhopal"
5. Verify the map renders in development mode without console errors

**Acceptance Criteria:**
- [ ] Visiting `http://localhost:3000/app/map` shows a rendered MapLibre map centered on Bhopal
- [ ] No `window is not defined` or similar SSR errors in console
- [ ] Map loads without a MapLibre API key (using free tile provider)
- [ ] `npm run build` exits 0
- [ ] Map contains "Prototype Dataset — Bhopal" overlay text

**Files Created:**
- `drishtigis/lib/gis/bounds.ts` (new)
- `drishtigis/components/map/MapLibreMap.tsx` (new)
- `drishtigis/app/app/map/page.tsx` (updated from placeholder)
- `drishtigis/lib/utils/cn.ts` (new — classnames utility)

---

### Task 5.6 — Create All Route Placeholder Pages

**Goal:** Create all required routes from `requirements.md §REQ-FE-08` so no route returns 404.

**Steps:**
1. Create placeholder pages for all routes not yet implemented:
   - `drishtigis/app/page.tsx` — landing placeholder
   - `drishtigis/app/(auth)/login/page.tsx` — login placeholder
   - `drishtigis/app/(auth)/register/page.tsx` — register placeholder
   - `drishtigis/app/app/location/page.tsx` — location placeholder
   - `drishtigis/app/app/property/[id]/page.tsx` — property placeholder
   - `drishtigis/app/app/history/page.tsx` — history placeholder
   - `drishtigis/app/app/reports/page.tsx` — reports placeholder
   - `drishtigis/app/app/assistant/page.tsx` — assistant placeholder
   - `drishtigis/app/admin/page.tsx` — admin placeholder
   - `drishtigis/app/admin/datasets/page.tsx` — datasets placeholder
   - `drishtigis/app/admin/datasets/upload/page.tsx` — upload placeholder
   - `drishtigis/app/admin/processing/page.tsx` — processing placeholder
   - `drishtigis/app/admin/review/page.tsx` — review placeholder
2. Each placeholder page must include the route name and a note: "Implementation in progress — [feature name]"
3. All placeholders must render without errors

**Acceptance Criteria:**
- [ ] All 14 routes return a valid page (not 404)
- [ ] `npm run build` exits 0 — zero TypeScript errors across all pages
- [ ] No broken imports

**Files Created:**
- All route `page.tsx` files listed above

---

### Task 5.7 — Frontend Build Verification

**Goal:** Final verification that the frontend foundation is complete and clean.

**Steps:**
1. Run `npm run build` — must exit 0
2. Run `npm run lint` — must exit 0
3. Start dev server and manually verify:
   - `http://localhost:3000` loads
   - `http://localhost:3000/app/map` shows MapLibre map centered on Bhopal
   - `http://localhost:3000/design-system` shows color swatches
   - No 404 on any route listed in REQ-FE-08
4. Open browser DevTools — no critical console errors
5. Update `progress.md` with frontend foundation status

**Acceptance Criteria:**
- [ ] `npm run build` exits 0
- [ ] `npm run lint` exits 0
- [ ] MapLibre map renders at `/app/map`
- [ ] No 404 on any required route
- [ ] No critical console errors

---

## Phase 6 — Backend Foundation

### Task 6.1 — Initialize FastAPI Project

**Goal:** Create the FastAPI project structure with all required directories and base configuration.

**Steps:**
1. Create the full `backend/` directory structure from `design.md §2`
2. Create `backend/requirements.txt` with exact pinned versions:
   ```
   fastapi==0.123.0
   uvicorn==0.38.0
   sqlalchemy==2.0.46
   asyncpg==0.31.0
   alembic==1.18.4
   pydantic==2.12.5
   pydantic-settings==2.13.0
   python-dotenv==1.2.1
   python-multipart==0.0.22
   geoalchemy2==0.15.2
   pyproj==3.7.0
   python-jose==3.5.0
   passlib==1.7.4
   bcrypt==5.0.0
   ```
3. Create `backend/requirements-dev.txt`:
   ```
   pytest==8.4.2
   pytest-asyncio==0.24.0
   httpx==0.27.2
   ```
4. Create `backend/.env.example` mirroring the root `.env.example` for backend-specific variables
5. Create all `__init__.py` files in the package structure

**Acceptance Criteria:**
- [ ] `backend/` directory structure matches `design.md §2`
- [ ] `requirements.txt` exists with pinned versions
- [ ] All `__init__.py` files exist
- [ ] `backend/.env.example` exists

**Files Created:**
- Full `backend/` directory structure
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/.env.example`

---

### Task 6.2 — Implement Core Configuration and Database Connection

**Goal:** Implement the settings module and async database connection.

**Steps:**
1. Implement `backend/app/core/config.py` as per `design.md §4.2`
2. Implement `backend/app/core/database.py` as per `design.md §4.3`
3. Implement `backend/app/utils/data_source.py` with the `DataSource` enum
4. Implement `backend/app/main.py` with CORS, router registration, and app configuration as per `design.md §4.1`
5. Implement `backend/app/api/v1/health.py` as per `design.md §4.6`
6. Create a `backend/.env` file (gitignored) for local development — use `aiosqlite` as a lightweight fallback if Supabase credentials are not yet available, so the backend can start without a live PostgreSQL connection

**Acceptance Criteria:**
- [ ] `uvicorn app.main:app --reload` starts without import errors
- [ ] `GET /health` returns `{"status": "ok", "version": "0.1.0", "database": ...}`
- [ ] `/docs` loads Swagger UI
- [ ] `/redoc` loads ReDoc
- [ ] No secrets are hard-coded

**Files Created/Modified:**
- `backend/app/core/config.py` (new)
- `backend/app/core/database.py` (new)
- `backend/app/utils/data_source.py` (new)
- `backend/app/main.py` (new)
- `backend/app/api/v1/health.py` (new)
- `backend/.env` (new, gitignored)

---

### Task 6.3 — Implement SQLAlchemy Models

**Goal:** Create all database models corresponding to the schema defined in `requirements.md §REQ-DB-02`.

**Steps:**
1. Implement SQLAlchemy ORM models for all 8 entities:
   - `backend/app/models/user.py`
   - `backend/app/models/dataset.py`
   - `backend/app/models/parcel.py`
   - `backend/app/models/property.py`
   - `backend/app/models/ai_feature.py`
   - `backend/app/models/discrepancy.py`
   - `backend/app/models/processing_job.py`
   - `backend/app/models/historical_snapshot.py`
2. All geometry columns use `geoalchemy2.Geometry` with SRID 4326
3. All models include the `source` field with `DataSource` enum
4. All models include `created_at` with server default `now()`
5. The `HistoricalSnapshot` model must explicitly define `change_type` as `nullable=True`. Add a comment:
   ```python
   change_type = Column(String, nullable=True)
   # NULL = no historical change classification available.
   # Reason: no real multi-temporal imagery exists for the prototype dataset.
   # Valid non-null values when real data exists:
   #   'new_structure', 'boundary_change', 'demolition', 'land_use_change'
   ```
6. Update `backend/app/models/__init__.py` to export all models

**Acceptance Criteria:**
- [ ] All 8 model files exist
- [ ] All geometry columns specify `srid=4326`
- [ ] All models have `source` field
- [ ] `HistoricalSnapshot.change_type` column is explicitly `nullable=True` with an explanatory comment
- [ ] Models import cleanly (no circular imports)
- [ ] `python -c "from app.models import *"` runs without errors

**Files Created:**
- `backend/app/models/*.py` (8 new model files)

---

### Task 6.4 — Configure Alembic and Create Initial Migration

**Goal:** Configure Alembic for async migrations and create the initial database schema migration.

**Steps:**
1. Run `alembic init backend/alembic` (or create manually)
2. Configure `alembic.ini` to use the `DATABASE_URL` from settings
3. Configure `backend/alembic/env.py` for async engine operation with SQLAlchemy
4. Create initial migration `001_initial_schema.py` that:
   - Creates `CREATE EXTENSION IF NOT EXISTS postgis;`
   - Creates all 8 tables with correct column types and constraints
   - Creates GIST indexes on all geometry columns
   - Creates `updated_at` auto-update triggers
5. Document how to run the migration in `scripts/README.md`

**Note:** The migration cannot be applied until a PostgreSQL + PostGIS connection is available. The migration file itself must be correct and ready.

**Acceptance Criteria:**
- [ ] `alembic.ini` and `backend/alembic/env.py` exist
- [ ] `001_initial_schema.py` migration file exists
- [ ] Migration includes `CREATE EXTENSION IF NOT EXISTS postgis`
- [ ] Migration includes GIST indexes on all geometry columns
- [ ] `alembic check` (if applicable) shows no configuration errors

**Files Created:**
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/alembic.ini`

---

### Task 6.5 — Implement Placeholder API Endpoints

**Goal:** Create placeholder API endpoints that return demo data, enabling frontend development before the real backend is connected.

**Steps:**
1. Implement `backend/app/schemas/parcel.py` — Pydantic response schemas
2. Implement `backend/app/schemas/feature.py` — Pydantic response schemas
3. Implement `backend/app/schemas/common.py` — shared response models
4. Implement `backend/app/api/v1/parcels.py` with:
   - `GET /api/v1/parcels/{parcel_id}` — returns demo parcel data when called with `DRS-BPL-00101`
   - `GET /api/v1/parcels/` — returns list of demo parcels with `?city=Bhopal`
5. Implement `backend/app/api/v1/features.py` with:
   - `GET /api/v1/features/?parcel_id={id}` — returns demo AI features for a parcel
6. All placeholder responses must include the `source` field set to `DEMO_DATA_PROTOTYPE_ONLY`
7. Placeholder responses must include a response header: `X-Data-Status: demo-placeholder`

**Acceptance Criteria:**
- [ ] `GET /api/v1/parcels/DRS-BPL-00101` returns a valid JSON response
- [ ] Response includes `source: "DEMO_DATA_PROTOTYPE_ONLY"`
- [ ] Response header `X-Data-Status: demo-placeholder` is present
- [ ] `/docs` shows all endpoints documented

**Files Created:**
- `backend/app/schemas/parcel.py`
- `backend/app/schemas/feature.py`
- `backend/app/schemas/common.py`
- `backend/app/api/v1/parcels.py`
- `backend/app/api/v1/features.py`

---

### Task 6.6 — Backend Verification

**Goal:** Final verification that the backend foundation is complete and clean.

**Steps:**
1. Start backend: `uvicorn app.main:app --reload`
2. Verify all endpoints documented at `/docs`
3. Test health endpoint
4. Test parcel placeholder endpoint
5. Run: `python -m pytest backend/` if any tests exist
6. Update `progress.md` with backend foundation status

**Acceptance Criteria:**
- [ ] Backend starts without errors
- [ ] `/health` returns OK
- [ ] `/api/v1/parcels/DRS-BPL-00101` returns demo data
- [ ] `/docs` loads cleanly

---

## Phase 7 — Integration Verification and Progress Documentation

### Task 7.1 — Full Stack Smoke Test

**Goal:** Verify that frontend and backend can communicate and that the demo data is correctly wired.

**Steps:**
1. Start backend on port 8000
2. Start frontend on port 3000 (set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`)
3. Verify that the MapLibre map page loads at `http://localhost:3000/app/map`
4. Verify that a fetch to `http://localhost:3000/api/...` or directly to the backend returns demo parcel data
5. Verify that demo parcel GeoJSON is accessible and loadable in the frontend
6. Check browser console for errors

**Acceptance Criteria:**
- [ ] Frontend starts and loads without errors
- [ ] Backend starts and responds at `/health`
- [ ] Map page renders MapLibre map at Bhopal coordinates
- [ ] No CORS errors in browser console
- [ ] Demo parcel data is accessible

---

### Task 7.2 — Update progress.md

**Goal:** Document the complete implementation status at the end of this spec, including what is real data, what is demo, and what is still missing.

**Steps:**
1. Update `progress.md` with:
   - Completed tasks with dates
   - Current state of each data asset (real / demo / missing)
   - Known gaps (no historical imagery, no real cadastral data, no real AI output)
   - Next spec requirements
   - Blockers if any

**Required content in progress.md:**
```
## Data Assets Status

| Asset | Type | Status |
|---|---|---|
| Bhopal UAV TIFF tiles (30) | RAW_RASTER_UAV | Available — unprocessed |
| Bhopal mosaic VRT | PROCESSED_RASTER | [Generated / Not yet generated] |
| Bhopal COG | PROCESSED_RASTER | [Generated / Not yet generated] |
| Bhopal XYZ tiles | PROCESSED_RASTER | [Generated / Not yet generated] |
| Bhopal OSM buildings | OSM_OPENSTREETMAP | [Extracted / Not yet extracted] |
| Bhopal OSM roads | OSM_OPENSTREETMAP | [Extracted / Not yet extracted] |
| Bhopal parcel data | — | NOT AVAILABLE — Demo data used |
| AI feature annotations | — | NOT AVAILABLE — Demo data used |
| Historical imagery | — | NOT AVAILABLE — Feature deferred |
| Bhopal DEM/DSM | — | NOT AVAILABLE — No Bhopal DEM in dataset |

## What Is Missing Before Full Demo Works

- Real cadastral parcel data (government source required)
- Real AI model output (YOLO inference required)
- Historical imagery (second time epoch required)
- Bhopal DEM/DSM for terrain features
```

**Acceptance Criteria:**
- [ ] `progress.md` is updated with accurate implementation status
- [ ] Every data asset is classified (real/demo/missing)
- [ ] Missing items are not claimed as implemented

---

## Task Dependency Summary

```
Task 0.1 → Task 0.2 → All other tasks

Task 1.1 → Task 1.2
Task 1.2 → Task 4.2, Task 4.3 (bounds validation)

Task 2.1 (GDAL install) → Task 2.2 → Task 2.3 → Task 2.4
Task 2.1 can be deferred; Tasks 3–6 can proceed in parallel

Task 4.1 → Task 4.2 → Task 4.3 → Task 4.4 → Task 4.5 → Task 4.6

Task 5.1 → Task 5.2 → Task 5.3 → Task 5.4 → Task 5.5 → Task 5.6 → Task 5.7

Task 6.1 → Task 6.2 → Task 6.3 → Task 6.4 → Task 6.5 → Task 6.6

Task 5.7 + Task 6.6 → Task 7.1 → Task 7.2

Phases 3, 4, 5, 6 can run in parallel after Phase 0 and Task 1.1/1.2.
Phase 2 (GDAL) is independent and can be done whenever GDAL is installed.
```

---

## Estimated Effort Summary

| Phase | Tasks | Estimated Sessions |
|---|---|---|
| Phase 0 — Repository Bootstrap | 2 | 1 |
| Phase 1 — Bhopal Data Validation | 2 | 1 |
| Phase 2 — GIS Processing (GDAL required) | 4 | 2–3 |
| Phase 3 — OSM Extraction | 1 | 1 |
| Phase 4 — Demo Data Package | 6 | 2 |
| Phase 5 — Frontend Foundation | 7 | 3 |
| Phase 6 — Backend Foundation | 6 | 2–3 |
| Phase 7 — Integration and Documentation | 2 | 1 |
| **Total** | **30** | **13–15** |
