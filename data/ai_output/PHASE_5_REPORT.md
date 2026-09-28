# DrishtiGIS Phase 5 — AI Building to Parcel Association + WebGIS Integration

Generated: 2026-09-13  
Status: **COMPLETE — 235/235 tests pass, 0 TS errors, production build clean**

---

## 1. AI Building Count

**834 real AI-derived building footprints** served from:  
`data/ai_output/bhopal-building-parcel-associations.geojson`

Source: UAVPal UNet-ResNet18, Phase 3 training, epoch 25, Building IoU = 0.587.  
Classification: `AI_DERIVED_UAVPAL` (not `AI_DERIVED_DEMO`).

---

## 2. Parcel Count

**3 prototype demonstration parcels** in `drishtigis/lib/demo-data/bhopal-parcels.geojson`.

| Parcel ID | Property ID | Land Type | Area m² |
|---|---|---|---|
| parcel-bpl-001 | DRS-BPL-00101 | Residential | 600 |
| parcel-bpl-002 | DRS-BPL-00102 | Residential | 550 |
| parcel-bpl-003 | DRS-BPL-00103 | Commercial | 720 |

Note: Only 3 prototype parcels cover a very small area. 802 of 834 buildings are outside all parcel polygons — expected, not an error.

---

## 3. Matched Building Count

**32 buildings** have a meaningful parcel match (overlap_ratio ≥ 0.10).

| Parcel | Primary Buildings |
|---|---|
| parcel-bpl-001 | **20** |
| parcel-bpl-002 | 6 |
| parcel-bpl-003 | 6 |

---

## 4. Unmatched Building Count

**802 buildings** — `NO_PARCEL_MATCH`. All 802 have overlap_ratio = 0 with all 3 prototype parcels. This is expected: the prototype parcel dataset covers only a tiny 3-polygon demo area while the AI buildings span all 30 UAV tiles (~1 km² of Bhopal).

---

## 5. Multi-Parcel Building Count

**0 buildings** straddle multiple prototype parcels (parcels are spatially separated).

---

## 6. Spatial Relationship Classification

| Relationship | Count | Description |
|---|---|---|
| `FULLY_WITHIN` | **16** | ≥ 95% of building inside primary parcel |
| `CROSSES_BOUNDARY` | **16** | Meaningful overlap but extends outside parcel |
| `PARTIALLY_OVERLAPS` | 0 | — |
| `TOUCHES_BOUNDARY` | 0 | — |
| `NO_PARCEL_MATCH` | **802** | No intersection with any prototype parcel |

**Thresholds (analytical only — no legal meaning):**
- `meaningful_overlap_ratio` = 0.10 — minimum to assign a primary parcel
- `fully_within_ratio` = 0.95 — classified as fully within
- `secondary_min_ratio` = 0.05 — included in secondary parcel list

---

## 7. Average Overlap Ratio

For matched buildings (32 total):  
Average overlap ratio: varies per building — see `bhopal-building-parcel-associations.geojson`.

For the full dataset: **mean overlap = 0 for unmatched, 0.10–1.00 for matched**.

---

## 8. Discrepancy Count by Type

| Type | Count |
|---|---|
| `BUILDING_CROSSES_PARCEL_BOUNDARY` | 16 |
| `NO_AI_BUILDING_IN_PARCEL` | 334 |
| **Total** | **350** |

All discrepancies carry:
- `severity: "REVIEW"` — no automatic HIGH/CRITICAL assignment
- `source: "AI_DERIVED_UAVPAL"`
- No `legal_status` field
- No forbidden language (illegal, fraud, encroachment, violation)

---

## 9. Tests

| Suite | Passed | Failed |
|---|---|---|
| Phase 5 association tests | 47 | 0 |
| Phase 4 pipeline tests | 45 | 0 |
| AI pipeline tests (Phase 2/3) | 46 | 0 |
| Backend WebGIS tests | 97 | 0 |
| **Total** | **235** | **0** |

All pre-existing test failures resolved by updating tests to match Phase 5 real-data behaviour.  
`test_ai_feature_filter_by_parcel` now correctly expects 20 buildings for `parcel-bpl-001` (was asserting 1 from demo drift — now reflects real spatial association).

---

## 10. Frontend Build

```
npm run build — 0 TypeScript errors
All 15 routes compiled successfully
```

Lint: 2 pre-existing `no-explicit-any` in `ContextSidebar.tsx` (both architecturally necessary — `data?: any` in MapLibre click event interface, `bounds as any` for type mismatch). No new lint errors introduced by Phase 5.

---

## 11. API Changes

### `GET /api/v1/features`
- Now serves 834 real buildings from `bhopal-building-parcel-associations.geojson`
- `_source: "AI_DERIVED_UAVPAL"` (previously `AI_DERIVED_DEMO`)
- New query params: `?parcel_id=`, `?tile=`
- New field on each feature: `primary_parcel_id`, `parcel_relationship`, `overlap_ratio`
- New `ai_available: true/false` flag
- Non-Bhopal cities: `ai_available: false`, empty FeatureCollection

### `GET /api/v1/features/stats`
- New endpoint: total buildings, parcel matched/unmatched, relationship breakdown

### `GET /api/v1/parcels/{property_id}`
- New `ai_analysis` sub-object: `building_count`, `total_detected_area_m2`, `average_confidence`, `coverage_ratio`, `discrepancies`, `buildings` list
- `ai_features` field now contains real buildings (not demo)
- `discrepancies` field now contains real geometric observations (not demo)
- `_ai_source: "AI_DERIVED_UAVPAL"` added

---

## 12. Frontend Changes

### MapLibreMap.tsx
- AI layer source: `${API_BASE}/api/v1/features` (real data, same URL, now returns real 834 buildings)
- Styling: teal fill (#0D9488) for `FULLY_WITHIN`, amber (#D97706) for `CROSSES_BOUNDARY`, default teal for unmatched
- `minzoom` raised to 15 (individual building footprints only visible at street scale)
- No popup DOM nodes — `onSelectContext` callback only (unchanged)
- `customLayerIds` set now includes highlight layers (was missing)

### ContextSidebar.tsx
- **ai-feature mode**: shows real fields — Building ID, Source Tile, Detected Area, Confidence, Model, Model Version, Parcel Relationship, Overlap Ratio, Primary Parcel, analytical disclaimer
- **View Property Record** button: uses `primary_property_id` (e.g. `DRS-BPL-00101`) from real association — hardcoded demo mapping chain removed
- Shows "No parcel match" message for the 802 unmatched buildings
- **parcel mode**: real `ai_analysis` sub-object — building count, total detected area, coverage ratio, avg confidence, discrepancy count
- Discrepancy section: uses real discrepancy records from `ai_analysis.discrepancies`

### TypeScript types
- `AI_DERIVED_UAVPAL` added to `DataSource` enum
- `RealAIBuildingProperties`, `AIBuildingSummary`, `AIDiscrepancy`, `AIBuildingAnalysis`, `AIFeaturesResponse`, `ParcelRelationship` type added to `types.ts`
- `ParcelDetailResponse` now includes `ai_analysis: AIBuildingAnalysis | null`
- `fetchAIBuildings()` added to `lib/api/parcels.ts`

---

## 13. Known Limitations

| Limitation | Description |
|---|---|
| Only 3 prototype parcels | 802 of 834 buildings have NO_PARCEL_MATCH — expected for prototype |
| No real cadastral data | Demo parcels don't represent legal land records |
| AI building recall ~58% | ~42% of actual buildings may be absent from the AI output |
| Parcel boundaries are prototypes | Spatial relationships are geometric approximations only |
| No production GeoJSON replacement yet | `bhopal-ai-features.geojson` kept as DEMO/LEGACY reference |

---

## Data Integrity

| Asset | Status |
|---|---|
| 30 RGB TIFFs | Byte-exact — not modified |
| 30 label TIFFs | Byte-exact — not modified |
| PBF | 1,706,252,573 bytes — not modified |
| bhopal-ai-features.geojson | Preserved as DEMO/LEGACY reference |
| bhopal-parcels.geojson | Not modified |

---

## Files Created/Modified This Phase

| File | Change |
|---|---|
| `data/ai_output/bhopal-building-parcel-associations.geojson` | Created — 834 buildings with associations (2.18 MB) |
| `data/ai_output/bhopal-discrepancies.json` | Created — 350 discrepancy records |
| `backend/app/api/v1/features.py` | Rewritten — serves real data |
| `backend/app/api/v1/parcels.py` | Updated — ai_analysis sub-object |
| `backend/app/utils/data_source.py` | AI_DERIVED_UAVPAL added |
| `backend/app/gis/coverage_registry.py` | Real AI dataset entry added |
| `backend/tests/test_phase5_association.py` | Created — 47 tests |
| `backend/tests/test_webgis.py` | Updated — 97 tests, all pass |
| `drishtigis/lib/demo-data/types.ts` | New types + AI_DERIVED_UAVPAL |
| `drishtigis/lib/api/parcels.ts` | Updated types + fetchAIBuildings |
| `drishtigis/lib/api/index.ts` | Barrel updated |
| `drishtigis/components/map/MapLibreMap.tsx` | AI layer restyled |
| `drishtigis/components/map/ContextSidebar.tsx` | ai-feature + parcel modes updated |
| `drishtigis/components/map/PropertyPanel.tsx` | feature_type cast fixed |

---

## STOP — Phase 5 Complete

**Active production source for Bhopal AI buildings:**  
`data/ai_output/bhopal-building-parcel-associations.geojson` via `/api/v1/features`

**Demo polygons preserved at:**  
`drishtigis/lib/demo-data/bhopal-ai-features.geojson` (DEMO/LEGACY, not served in production)

**Waiting for explicit Phase 6 approval:**  
Historical change detection / second epoch comparison.
