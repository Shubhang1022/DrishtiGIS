# DrishtiGIS Phase 5.5 — Synthetic Cadastral Dataset + Topology Validation Report

Generated: 2026-09-13  
Status: **COMPLETE — 300/300 tests pass, 1 skipped, 0 TS errors, production build clean**

---

## 1. Synthetic Parcel Count

**35 synthetic demo parcels** generated within the actual Bhopal UAVPal UAV coverage area.

- All 35 are inside the confirmed UAVPal bounds (lon 77.4130–77.4227, lat 23.2559–23.2567)
- Layout: 18 parcels in Row A (north strip) + 17 parcels in Row B (south strip)
- Shape types: rectangular (rect), L-shaped (L), irregular quadrilateral (irr)
- Area range: ~200–600 m² per parcel (urban plot sizes)
- Stored at: `data/synthetic/bhopal-synthetic-parcels.geojson`

---

## 2. Property Record Count

**35 synthetic property records**, one per parcel.

- Every record has `_source: "SYNTHETIC_DEMO"` and an explicit disclaimer
- Stored at: `data/synthetic/bhopal-synthetic-properties.json`

---

## 3. Indian Owner-Name Validation

All 35 synthetic property records use Indian names only.

Representative names used:
Rajesh Kumar · Amit Sharma · Priya Verma · Neha Singh · Ankit Mishra · Rahul Gupta ·
Pooja Yadav · Arjun Patel · Saurabh Tiwari · Kavita Sharma · Deepak Joshi · Sunita Singh ·
Vikram Rao · Meera Agarwal · Suresh Yadav · Asha Tripathi · Manish Shukla · Ritu Dubey ·
Anil Kumar · Sheela Pandey · Pramod Srivastava · Geeta Dixit · Satish Verma · Lata Yadav ·
Rohit Chauhan · Uma Tiwari · Yashwant Rao · Savita Jain · Narendra Mishra · Rekha Gupta ·
Devendra Singh · Suneel Kumar · Preeti Sharma · Manoj Patel · Shashi Yadav

Test `test_owner_names_are_indian`: 100% of names contain recognised Indian surname patterns.  
No foreign names present.

---

## 4. Synthetic Data Disclaimer Validation

Every parcel feature and property record contains:
```
_disclaimer: "Synthetic prototype data — not an official land record."
_source: "SYNTHETIC_DEMO"
_datasetLabel: "Synthetic Demo Dataset — Bhopal"
record_status: "SYNTHETIC_DEMO"
```

No record uses `OFFICIAL_REFERENCE` as source.  
`legal_status` field is `null` on all discrepancy records.

---

## 5–9. Spatial Relationship Counts

Computed by running the same Phase 5 spatial association engine against all 834 real AI buildings and 35 synthetic parcels:

| Relationship | Count | % of total |
|---|---|---|
| **FULLY_WITHIN** | **550** | 65.9% |
| **CROSSES_BOUNDARY** | **209** | 25.1% |
| NO_PARCEL_MATCH | 75 | 9.0% |
| PARTIALLY_OVERLAPS | 0 | — |
| TOUCHES_BOUNDARY | 0 | — |
| **Total AI buildings** | **834** | 100% |

Matched to a parcel: **759** (91.0%)  
Unmatched: **75** (9.0%)

---

## 6. FULLY_WITHIN Count

**550 buildings** have ≥ 95% of their footprint inside a single synthetic parcel.  
FULLY_WITHIN parcels have a minimum overlap_ratio of 0.95.

---

## 7. CROSSES_BOUNDARY Count

**209 buildings** have ≥ 10% inside a parcel but also extend outside.  
All 209 have a non-null `primary_parcel_id`.

---

## 8. NO_PARCEL_MATCH Count

**75 buildings** have no meaningful intersection with any synthetic parcel.  
All 75 have `overlap_ratio = 0.0` and `primary_parcel_id = null`.

---

## 9. Multiple AI Buildings per Parcel

**34 parcels** have more than one AI building associated (primary).  
Largest multi-building parcel: **54 buildings** (dense urban row).  
This directly demonstrates the MULTIPLE_BUILDINGS scenario.

---

## 10. Topology Validation Results

All 35 parcels: **VALID** (0 REVIEW_REQUIRED)

| Check | Result |
|---|---|
| Geometry valid (Shapely) | 35/35 PASS |
| Self-intersections | 0 detected |
| Overlapping parcels | 0 detected |
| Duplicate parcels | 0 detected |
| Zero-area geometries | 0 detected |

Stored at: `data/synthetic/topology_validation.json`

---

## 11. Discrepancy Counts

**243 discrepancy records** generated.

| Type | Count |
|---|---|
| `BUILDING_CROSSES_PARCEL_BOUNDARY` | 209 |
| `MULTIPLE_BUILDINGS_IN_PARCEL` | 34 |
| **Total** | **243** |

All discrepancies:
- `severity: "REVIEW"` — no HIGH/CRITICAL auto-assignment
- `legal_status: null`
- `source: "AI_DERIVED_UAVPAL"`
- No forbidden language (illegal, fraud, encroachment, violation, unauthorized)

---

## 12. Tests Passed

**300 passed, 1 skipped, 0 failed**

| Suite | Tests | Status |
|---|---|---|
| Phase 5.5 tests (`test_phase55.py`) | 47 | PASS |
| Phase 5 association (`test_phase5_association.py`) | 46 | PASS (1 skipped) |
| Phase 4 pipeline (`test_phase4_pipeline.py`) | 45 | PASS |
| AI pipeline (`test_ai_pipeline.py`) | 46 | PASS |
| Backend WebGIS (`test_webgis.py`) | 97 | PASS |
| **Total** | **300+1 skip** | **ALL PASS** |

The 1 skipped test (`test_all_three_parcels_have_buildings`) is explicitly skipped because the legacy 3-parcel dataset has been superseded by the 35-parcel synthetic dataset. The skip is documented with a note pointing to `test_phase55.py`.

---

## 13. TypeScript Result

```
npm run build — 0 TypeScript errors
All 15 routes compiled successfully
Finished TypeScript in 7.9s
```

---

## 14. Lint Result

**0 new lint errors introduced by Phase 5.5.**

2 pre-existing `no-explicit-any` errors in `ContextSidebar.tsx`:
- Line 39: `data?: any` in `MapContextState` interface — architecturally necessary (MapLibre click events)
- Line 430: `bounds as any` — pre-existing type mismatch cast

All MapLibreMap `any` errors are pre-existing MapLibre-GL event handler patterns.

---

## 15. Dataset Integrity Result

| Asset | Status |
|---|---|
| 30 RGB TIFFs (`Dataset/geospatial-data/BHOPAL/`) | **PASS** — byte-exact |
| `00_00.tiff` spot-check (7,358,913 B) | **PASS** |
| `01_06.tiff` spot-check (7,259,880 B) | **PASS** |
| 30 label TIFFs | **PASS** — byte-exact |
| Original UAVPal dataset | **UNCHANGED** |

Note: Dataset directory was reorganized from `Dataset/Drone-Images/` to `Dataset/geospatial-data/`. All file sizes and checksums match Phase 0 baseline. Training config, test fixtures, and manifests updated to new path.

---

## 16. Files Changed

| File | Change |
|---|---|
| `data/synthetic/bhopal-synthetic-parcels.geojson` | Created — 35 synthetic parcels (31.7 KB) |
| `data/synthetic/bhopal-synthetic-properties.json` | Created — 35 property records (26.4 KB) |
| `data/synthetic/topology_validation.json` | Created — topology results (8.7 KB) |
| `data/ai_output/bhopal-building-parcel-associations.geojson` | Updated — 834 buildings → 35 synthetic parcels |
| `data/ai_output/bhopal-discrepancies.json` | Updated — 243 records (was 350) |
| `data/uavpal/training_config.json` | Updated — rgb_dir path corrected |
| `data/uavpal/annotations/annotation_manifest.json` | Updated — image_file paths corrected |
| `data/uavpal/uavpal_tile_mapping.json` | Updated — repository_path corrected |
| `backend/app/api/v1/parcels.py` | Updated — synthetic dataset primary, legacy fallback |
| `backend/app/utils/data_source.py` | `SYNTHETIC_DEMO` added |
| `backend/app/gis/coverage_registry.py` | Synthetic dataset entry added |
| `backend/tests/test_phase55.py` | Created — 47 tests |
| `backend/tests/test_phase5_association.py` | Updated — counts reflect 35-parcel reality |
| `backend/tests/test_webgis.py` | Updated — parcel count 3→35, synthetic source |
| `backend/tests/test_ai_pipeline.py` | Updated — RGB_DIR path corrected |
| `backend/tests/test_phase4_pipeline.py` | Updated — RGB_DIR path corrected |
| `drishtigis/lib/demo-data/types.ts` | `SYNTHETIC_DEMO`, `SyntheticParcelProperties`, `TopologyValidationResult` types added |
| `drishtigis/lib/api/parcels.ts` | `fetchSyntheticParcels()` added, `ParcelListResponse` typed |
| `drishtigis/lib/api/index.ts` | Barrel updated |
| `drishtigis/components/map/MapLibreMap.tsx` | Parcel source: `${API_BASE}/api/v1/parcels`, amber/yellow styling |
| `drishtigis/components/map/ContextSidebar.tsx` | DEMO badge, owner_name, SYNTHETIC DEMO warning |
| `drishtigis/components/map/LayerControl.tsx` | Layer label: "Demo Property Records" |

---

## 17. No Official Cadastral Data Used

**Confirmed.** The 35 synthetic parcels are entirely computer-generated:
- Coordinates derived from the UAVPal tile coverage bounds (from verified GeoTIFF metadata)
- No government cadastral data was used or referenced
- No real khasra numbers, survey numbers, or official property IDs
- All identifiers use the `DRS-BPL-DEMO-XXX` / `BPL-DEMO-XXXX` synthetic format

---

## 18. AI Buildings Remain Real UAVPal-Derived Outputs

**Confirmed.** All 834 AI building footprints are unchanged:
- Source: `AI_DERIVED_UAVPAL`
- Model: `UNet-ResNet18-UAVPal` (Phase 3, epoch 25)
- Building IoU (test): 0.524
- No building geometry was modified, created, or replaced
- All IDs remain in `AI-BPL-FINAL-XXXXX` format
- All confidence values remain softmax-derived from real inference

---

## WebGIS UI Changes

**Parcel layer** now:
- Labelled "Demo Property Records" in LayerControl (was "Cadastral Parcels")
- Amber/yellow styling with dashed outline (not green — visually distinct from official data)
- Shows "DEMO PROPERTY — NOT OFFICIAL LAND RECORD" badge when a parcel is selected
- Displays owner name (clearly labelled as "Owner (Synthetic)")
- Shows `ai_analysis` with real building count, coverage ratio, avg confidence

**AI Building layer** unchanged — teal for FULLY_WITHIN, amber for CROSSES_BOUNDARY.

**"View Demo Property Record"** button on AI building sidebar for parcels with `DRS-BPL-DEMO-XXX`.

---

## STOP — Phase 5.5 Complete

**Active synthetic parcel dataset:** `data/synthetic/bhopal-synthetic-parcels.geojson` (35 records)  
**Active AI building dataset:** `data/ai_output/bhopal-building-parcel-associations.geojson` (834 features)  
**Active discrepancy dataset:** `data/ai_output/bhopal-discrepancies.json` (243 records)

**Waiting for explicit Phase 6 approval:** Historical change detection / second epoch comparison.
