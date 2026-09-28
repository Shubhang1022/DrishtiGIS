"""
DrishtiGIS Phase 4 — Georeferencing: pixel coords → EPSG:32643 → EPSG:4326.

Every coordinate is derived from the GeoTIFF affine transform.
No coordinates are hard-coded or derived from filenames.

Also handles:
  - Geometry validation (shapely.is_valid)
  - Documented geometry repair (buffer(0) / make_valid)
  - Area / perimeter calculation in source CRS (m)
  - Centroid calculation in EPSG:4326
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from shapely.geometry import Polygon, MultiPolygon, mapping, shape
    from shapely.validation import make_valid
    from shapely.ops import transform as shapely_transform
    _SHAPELY_OK = True
except ImportError:
    _SHAPELY_OK = False

try:
    from pyproj import Transformer
    _PYPROJ_OK = True
except ImportError:
    _PYPROJ_OK = False

try:
    import rasterio
    _RASTERIO_OK = True
except ImportError:
    _RASTERIO_OK = False

from backend.ai.segmentation.postprocess import BuildingComponent

BUILDING_CLASS_ID = 4


# ── Geometry repair stats ─────────────────────────────────────────────────────

@dataclass
class GeometryRepairStats:
    total:     int = 0
    invalid:   int = 0
    repaired:  int = 0
    failed:    int = 0
    method:    str = "shapely make_valid (Polygonize + buffer(0) fallback)"


# ── Main conversion ───────────────────────────────────────────────────────────

def build_geojson_feature(
    comp: BuildingComponent,
    rgb_path: Path,
    repair_stats: Optional[GeometryRepairStats] = None,
) -> Optional[dict]:
    """
    Convert a BuildingComponent (pixel coords) to a GeoJSON Feature in EPSG:4326.

    Coordinate chain:
      pixel (col, row) → raster affine → EPSG:32643 (metres) → EPSG:4326 (lon/lat)

    Args:
        comp:         BuildingComponent with pixel_contour in (col, row) order
        rgb_path:     Path to source RGB GeoTIFF (for affine transform)
        repair_stats: Optional mutable stats accumulator

    Returns:
        GeoJSON Feature dict, or None if the geometry is invalid and unrepairable.
    """
    if not (_SHAPELY_OK and _PYPROJ_OK and _RASTERIO_OK):
        raise ImportError("shapely, pyproj and rasterio are all required")

    # 1. Load raster affine transform
    with rasterio.open(str(rgb_path)) as src:
        affine = src.transform
        src_crs_epsg = src.crs.to_epsg()   # should be 32643

    # 2. Pixel → EPSG:32643
    #    affine maps (col, row) → (easting, northing) in the raster CRS
    contour_px = comp.pixel_contour   # (N, 2) in (col, row) order
    # Apply affine: easting = a*col + b*row + c, northing = d*col + e*row + f
    a, b, c = affine.a, affine.b, affine.c
    d, e, f = affine.d, affine.e, affine.f
    col = contour_px[:, 0].astype(float)
    row = contour_px[:, 1].astype(float)
    easting  = a * col + b * row + c
    northing = d * col + e * row + f
    coords_32643 = list(zip(easting.tolist(), northing.tolist()))

    # Ensure polygon is closed
    if coords_32643[0] != coords_32643[-1]:
        coords_32643.append(coords_32643[0])

    if len(coords_32643) < 4:
        return None

    # 3. Build Shapely polygon in EPSG:32643
    try:
        poly_32643 = Polygon(coords_32643)
    except Exception:
        return None

    if repair_stats is not None:
        repair_stats.total += 1

    # 4. Validate & repair
    if not poly_32643.is_valid:
        if repair_stats is not None:
            repair_stats.invalid += 1
        poly_32643 = _repair_geometry(poly_32643)
        if poly_32643 is None or poly_32643.is_empty:
            if repair_stats is not None:
                repair_stats.failed += 1
            return None
        if repair_stats is not None:
            repair_stats.repaired += 1

    # 5. Calculate geometric properties in EPSG:32643 (metric)
    area_m2    = poly_32643.area
    perimeter_m = poly_32643.length
    centroid_32643 = poly_32643.centroid

    # 6. Transform to EPSG:4326
    transformer = Transformer.from_crs(
        f"EPSG:{src_crs_epsg}", "EPSG:4326",
        always_xy=True,
    )
    poly_4326 = shapely_transform(
        lambda x, y: transformer.transform(x, y),
        poly_32643,
    )

    # Centroid in 4326 (lon, lat)
    cen_lon, cen_lat = transformer.transform(
        centroid_32643.x, centroid_32643.y
    )

    # Final validity check on 4326 geometry
    if not poly_4326.is_valid:
        poly_4326 = _repair_geometry(poly_4326)
        if poly_4326 is None or poly_4326.is_empty:
            return None

    # 7. Build GeoJSON feature
    stable_id = f"AI-BPL-{comp.tile_id}-{comp.component_id:04d}"

    feature = {
        "type": "Feature",
        "geometry": mapping(poly_4326),
        "properties": {
            "id":                  stable_id,
            "source":              "AI_DERIVED_UAVPAL",
            "model":               "UNet-ResNet18-UAVPal",
            "model_version":       "phase3-epoch25-bld_iou0.587",
            "source_tile":         comp.tile_id,
            "source_class":        BUILDING_CLASS_ID,
            "source_class_name":   "Building",
            # Confidence: mean softmax P(Building=4) over all pixels in this component
            # This is the per-feature mean of the model's class-4 probability output.
            # It reflects the model's average certainty, not a calibrated probability.
            "confidence":          round(comp.mean_confidence, 4),
            "confidence_median":   round(comp.median_confidence, 4),
            "confidence_method":   "mean_softmax_p_building_over_component_pixels",
            "area_m2":             round(area_m2, 2),
            "perimeter_m":         round(perimeter_m, 2),
            "centroid_lon":        round(cen_lon, 7),
            "centroid_lat":        round(cen_lat, 7),
            "crs_source":          f"EPSG:{src_crs_epsg}",
            "crs_output":          "EPSG:4326",
            "pixel_area_px2":      round(comp.pixel_area, 1),
            "was_watershed_split": comp.was_watershed,
        },
    }
    return feature


def _repair_geometry(geom):
    """
    Attempt to repair an invalid Shapely geometry.
    Strategy:
      1. make_valid (Polygonize — preferred, preserves shape)
      2. buffer(0)  (fallback — may simplify slightly)
    Returns repaired geometry or None.
    """
    if geom is None:
        return None
    try:
        fixed = make_valid(geom)
        if fixed is not None and not fixed.is_empty and fixed.is_valid:
            # make_valid can return GeometryCollection — extract polygons
            from shapely.geometry import GeometryCollection
            if isinstance(fixed, GeometryCollection):
                polys = [g for g in fixed.geoms if isinstance(g, (Polygon, MultiPolygon))]
                if not polys:
                    return None
                fixed = max(polys, key=lambda g: g.area)
            return fixed
    except Exception:
        pass
    try:
        fixed = geom.buffer(0)
        if fixed is not None and not fixed.is_empty:
            return fixed
    except Exception:
        pass
    return None


def tile_components_to_features(
    components: list,
    rgb_dir: Path,
    repair_stats: Optional[GeometryRepairStats] = None,
) -> List[dict]:
    """
    Convert all BuildingComponents for a tile to GeoJSON features.

    Args:
        components: List of BuildingComponent
        rgb_dir:    Directory containing RGB GeoTIFFs
        repair_stats: Mutable stats accumulator (shared across tiles)

    Returns:
        List of GeoJSON Feature dicts
    """
    features = []
    for comp in components:
        rgb_path = rgb_dir / f"{comp.tile_id}.tiff"
        feat = build_geojson_feature(comp, rgb_path, repair_stats)
        if feat is not None:
            features.append(feat)
    return features
