# DrishtiGIS Phase 1 — Annotation Download + Validation Report

Generated: 2026-09-11 11:17 UTC  
Source: `doi:10.17026/DANS-Z55-6GT4` (phys-techsciences.datastations.nl)  

---

## Download Summary

| Item | Value |
|---|---|
| Total tiles downloaded | 30 |
| Total bytes | 528,642 (516.3 KB) |
| Download errors | 0 |
| SHA-1 verified (all) | YES |

---

## Train / Test Split

| Split | Count |
|---|---|
| Train | 18 |
| Test  | 12  |
| Total | 30 |

---

## Validation Results

| Item | Value |
|---|---|
| Successful validations | 30/30 |
| Failed validations | 0 |
| All tiles 2048×2048 | YES |
| All tiles EPSG:32643 | YES |
| All tiles uint8 | YES |
| All tiles class values 0-5 only | YES |
| All tiles spatially aligned | YES |

---

## Per-Class Pixel Statistics (all 30 tiles combined)

| Class ID | Class Name | Total Pixels | % of all pixels |
|---|---|---|---|
| 0 | Background | 33,272,434 | 26.443% |
| 1 | Water | 330,116 | 0.262% |
| 2 | Road | 14,158,045 | 11.252% |
| 3 | Car | 1,083,283 | 0.861% |
| 4 | Building | 71,610,322 | 56.911% |
| 5 | Tree | 5,374,920 | 4.272% |

---

## Building Pixel Statistics (Class 4)

| Metric | Train (18 tiles) | Test (12 tiles) |
|---|---|---|
| Tiles with building pixels | 18/18 | 12/12 |
| Total building pixels | 44,225,889 | 27,384,433 |
| Avg building pixel % | 58.579% | 54.408% |
| Combined building pixels | 71,610,322 | — |

### Per-tile building statistics

| Tile | Split | Bld Pixels | Bld % | Has Buildings |
|---|---|---|---|---|
| 00_00.tiff | train | 1,205,758 | 28.747% | YES |
| 00_01.tiff | test | 1,353,735 | 32.276% | YES |
| 00_02.tiff | test | 2,023,570 | 48.246% | YES |
| 00_03.tiff | train | 2,770,079 | 66.044% | YES |
| 00_04.tiff | test | 2,530,883 | 60.341% | YES |
| 00_05.tiff | train | 2,810,866 | 67.016% | YES |
| 00_06.tiff | train | 2,874,118 | 68.524% | YES |
| 00_07.tiff | test | 1,726,181 | 41.155% | YES |
| 00_08.tiff | train | 3,149,796 | 75.097% | YES |
| 00_09.tiff | train | 2,478,399 | 59.090% | YES |
| 00_10.tiff | test | 1,751,040 | 41.748% | YES |
| 00_11.tiff | train | 146,677 | 3.497% | YES |
| 00_12.tiff | train | 170,428 | 4.063% | YES |
| 00_13.tiff | test | 985,220 | 23.489% | YES |
| 00_14.tiff | test | 2,755,207 | 65.689% | YES |
| 00_15.tiff | train | 957,143 | 22.820% | YES |
| 00_16.tiff | train | 746,826 | 17.806% | YES |
| 00_17.tiff | train | 3,430,571 | 81.791% | YES |
| 00_18.tiff | train | 3,628,706 | 86.515% | YES |
| 00_19.tiff | test | 2,680,667 | 63.912% | YES |
| 00_20.tiff | train | 3,697,259 | 88.150% | YES |
| 00_21.tiff | train | 3,706,020 | 88.358% | YES |
| 00_22.tiff | train | 3,849,477 | 91.779% | YES |
| 01_00.tiff | test | 2,875,897 | 68.567% | YES |
| 01_01.tiff | train | 3,093,495 | 73.755% | YES |
| 01_02.tiff | train | 2,848,473 | 67.913% | YES |
| 01_03.tiff | test | 2,902,900 | 69.210% | YES |
| 01_04.tiff | test | 3,055,834 | 72.857% | YES |
| 01_05.tiff | test | 2,743,299 | 65.405% | YES |
| 01_06.tiff | train | 2,661,798 | 63.462% | YES |

---

## CRS / Dimension Validation

All 30 tiles: GeoTIFF, 2048×2048 px, EPSG:32643, single-band uint8.

---

## RGB-to-Label Spatial Alignment

Each label tile was opened alongside its corresponding RGB tile.  
Pixel scale and spatial bounds were compared with 1% tolerance.  
Result: see `spatial_aligned_with_rgb` in manifest.

---

## SHA-256 / Checksum Results

| Tile | DANS SHA-1 | Verified |
|---|---|---|
| 00_00.tiff | `83ee0ebba1aa6bce...` | ✓ |
| 00_01.tiff | `7f86ec2d2c8ec7c9...` | ✓ |
| 00_02.tiff | `4b5ceeaada734373...` | ✓ |
| 00_03.tiff | `44fb74575dc8c211...` | ✓ |
| 00_04.tiff | `2143d55bb60ea8a1...` | ✓ |
| 00_05.tiff | `baa53b79ae397fee...` | ✓ |
| 00_06.tiff | `ff01121ffe19c07f...` | ✓ |
| 00_07.tiff | `eb3d74b5a0ed6e49...` | ✓ |
| 00_08.tiff | `162b1798ec2e8b7f...` | ✓ |
| 00_09.tiff | `e03fb34a908e9d6e...` | ✓ |
| 00_10.tiff | `65ea9aaec4c807e8...` | ✓ |
| 00_11.tiff | `afc26c65c1836dea...` | ✓ |
| 00_12.tiff | `ce4e18c427734d52...` | ✓ |
| 00_13.tiff | `ed3c05c7ba72554a...` | ✓ |
| 00_14.tiff | `506a3a2a92388d43...` | ✓ |
| 00_15.tiff | `3178b24c1b69aace...` | ✓ |
| 00_16.tiff | `f75f15e5650acf58...` | ✓ |
| 00_17.tiff | `708f8deb4a20ad2d...` | ✓ |
| 00_18.tiff | `60908b4c78724289...` | ✓ |
| 00_19.tiff | `35f88468ca447db4...` | ✓ |
| 00_20.tiff | `a6f1c80d34351959...` | ✓ |
| 00_21.tiff | `84d0b03be79d018b...` | ✓ |
| 00_22.tiff | `a9633f95283ac979...` | ✓ |
| 01_00.tiff | `e0a42ade1f67f627...` | ✓ |
| 01_01.tiff | `97e310c9b6778ca2...` | ✓ |
| 01_02.tiff | `d06a13cdd9ac857b...` | ✓ |
| 01_03.tiff | `f9978795429bbda5...` | ✓ |
| 01_04.tiff | `53767de5f0984dc3...` | ✓ |
| 01_05.tiff | `e5c4147f86d1859a...` | ✓ |
| 01_06.tiff | `2d69f90eab7c32fa...` | ✓ |

---

## Dataset/ Integrity

30 RGB TIFFs in `Dataset/Drone-Images/BHOPAL/` — verified byte-exact before and after this phase.
No RGB file was modified, renamed, or converted.

---

## Anomalies

None — all 30 tiles downloaded and validated successfully.

---

## Pre-existing Test Failure (not introduced by Phase 1)

- **test_ai_feature_filter_by_parcel** — `assert data['total'] == 1` fails with `2`.
  Caused by uncommitted `bhopal-ai-features.geojson` having two features for `parcel-bpl-001`.
  Pre-existing data drift from a previous session. Not modified by this phase.
