# PHASE 23: NEW VS EXISTING IMAGERY AUDIT REPORT

## Executive Summary
This audit compares the 121 files discovered in `Dataset/geospatial-data/BHOPAL` against existing DrishtiGIS datasets, UAVPal baseline assets (`data/uavpal/`), and internal file system stores.

---

## Duplicate Detection Methodology
1. **SHA-256 Cryptographic Hash Matching**: Evaluates exact byte equality to prevent re-processing identical rasters.
2. **Filename & System Store Lookup**: Cross-references against `data/datasets.json` registered records and `data/uavpal/` baseline tiles.
3. **OS Naming Safeguards**: Identifies duplicate OS copy patterns (such as `filename (1).tiff`).

---

## Audit Findings

| Category | File Count | Representative Files | Resolution & Pipeline Action |
|----------|------------|----------------------|------------------------------|
| **Newly Discovered** | 89 | `01_07.tiff`, `01_08.tiff`, `01_09.tiff`, ..., `05_04.tiff` | Registered as distinct datasets (`DS-BHOPAL-TILE-*`). Validated and processed through Phase 23 pipeline. |
| **Filename Overlap (Existing System)** | 30 | `00_00.tiff` to `01_06.tiff` | Flagged as previously integrated assets. Kept read-only without redundant registration. |
| **Exact SHA-256 Duplicates** | 2 | `02_10 (1).tiff` (SHA-256: `a93...`) matching `02_10.tiff` | Marked `EXACT_DUPLICATE`. Skipped to prevent duplicate database entries and storage bloat. |

---

## Data Preservation Guarantee
- No original files in `Dataset/geospatial-data/BHOPAL` were modified, renamed, deleted, or overwritten.
- All original raw imagery remains preserved as read-only source files.
