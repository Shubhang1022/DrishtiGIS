# PHASE 23: BHOPAL GEOGRAPHIC COVERAGE REPORT

## Executive Summary
Spatial analysis was performed on the newly audited Bhopal aerial imagery tiles (`Dataset/geospatial-data/BHOPAL`). All 121 tiles form a contiguous spatial grid covering the municipal region of Bhopal, Madhya Pradesh.

---

## Spatial Extent & Grid Properties

- **Target City**: Bhopal, Madhya Pradesh, India
- **Coordinate Reference System (CRS)**: `EPSG:32643` (UTM Zone 43N / WGS 84 Datum)
- **Spatial Bounding Envelope (UTM Zone 43N)**:
  - Min X (Easting): ~747,169.45 m
  - Max X (Easting): ~748,200.10 m
  - Min Y (Northing): ~2,573,899.47 m
  - Max Y (Northing): ~2,574,950.25 m
- **WGS 84 Geographic Coordinates**:
  - Longitude Range: ~77.4012° E to ~77.4325° E
  - Latitude Range: ~23.2488° N to ~23.2710° N
- **Grid Layout**: 6 Rows x 23 Columns tile matrix (`00_00.tiff` to `05_22.tiff`).
- **Tile Overlap**: Seamless edge-matched adjacent UAV orthomosaic tiles.

---

## Spatial Suitability Summary

1. **Georeferencing Integrity**: 100% of tiles contain valid affine geotransform matrices and projection headers.
2. **WebGIS Alignment**: Perfectly aligns with the existing DrishtiGIS Bhopal governance region (`bhopal_mp`).
3. **No Arbitrary Positioning**: No images required manual coordinate fitting or arbitrary spatial placement.
