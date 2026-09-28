"""
DrishtiGIS — GIS Land-Use Intelligence Processing Engine
===========================================================
CRS-aware spatial processing for land-use polygon features, metric area
calculation, spatial indexing, and observed land-use pattern analysis.

DISCLAIMER: All observed land-use classifications represent AI-derived visual patterns
or reference GIS data. They do NOT constitute official legal land-use designations,
permitted zoning uses, or property ownership titles.
"""

from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import transform
import pyproj

from backend.app.models.landuse import LandUseFeature, ParcelLandUseSummary

# Spatial transformation helper for EPSG:4326 to metric EPSG:3857
_project_to_metric = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform


def compute_polygon_area_m2(geom: Any) -> float:
    """Computes area of polygon in square meters using EPSG:3857 metric projection."""
    if geom is None or geom.is_empty:
        return 0.0
    metric_geom = transform(_project_to_metric, geom)
    return round(float(metric_geom.area), 2)


def process_landuse_features(
    raw_geojson_features: List[Dict[str, Any]],
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01",
    city: str = "Bhopal",
    state: str = "Madhya Pradesh",
    source_name: str = "OpenStreetMap",
    source_type: str = "REFERENCE_GIS"
) -> List[LandUseFeature]:
    """Parses raw land-use GeoJSON features into normalized LandUseFeature models with metric area."""
    results: List[LandUseFeature] = []

    for idx, f in enumerate(raw_geojson_features):
        props = f.get("properties", {})
        geom_dict = f.get("geometry")
        if not geom_dict:
            continue

        geom = shape(geom_dict)
        if not geom.is_valid:
            geom = geom.buffer(0)

        landuse_id = str(props.get("osm_id") or props.get("id") or f"LU-{idx+1:04d}")
        raw_use = str(props.get("landuse") or props.get("type") or props.get("classification") or "RESIDENTIAL").upper()

        # Standardize classification into canonical categories
        if raw_use in ["RESIDENTIAL", "APARTMENTS", "HOUSING"]:
            std_class = "RESIDENTIAL"
        elif raw_use in ["COMMERCIAL", "RETAIL", "MARKET"]:
            std_class = "COMMERCIAL"
        elif raw_use in ["INDUSTRIAL", "FACTORY", "WAREHOUSE"]:
            std_class = "INDUSTRIAL"
        elif raw_use in ["INSTITUTIONAL", "CIVIC", "SCHOOL", "HOSPITAL", "GOVERNMENT"]:
            std_class = "INSTITUTIONAL"
        elif raw_use in ["GRASS", "PARK", "FOREST", "MEADOW", "VEGETATION", "WOOD"]:
            std_class = "VEGETATION"
        elif raw_use in ["WATER", "BASIN", "RESERVOIR"]:
            std_class = "WATER"
        elif raw_use in ["FARMLAND", "OPEN_AREA", "CLEAR", "RECREATION_GROUND"]:
            std_class = "OPEN_AREA"
        else:
            std_class = "RESIDENTIAL"

        area_m2 = compute_polygon_area_m2(geom)

        results.append(LandUseFeature(
            landuse_id=landuse_id,
            dataset_id=dataset_id,
            region_id=region_id,
            city=city,
            state=state,
            country="India",
            crs="EPSG:4326",
            source=source_name,
            source_type=source_type,
            classification=std_class,
            area_m2=area_m2,
            confidence=float(props.get("confidence", 0.90)) if source_type == "AI_DERIVED" else 0.95,
            evidence=f"Observed spatial polygon pattern from {source_name}.",
            geometry_geojson=mapping(geom),
            review_status="UNREVIEWED"
        ))

    return results


def analyze_parcel_landuse(
    parcel_id: str,
    parcel_geojson_geom: Dict[str, Any],
    landuse_features: List[LandUseFeature],
    associated_buildings: List[Dict[str, Any]] = None,
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01"
) -> ParcelLandUseSummary:
    """Analyzes observed land-use pattern for a specific parcel geometry."""
    parcel_geom = shape(parcel_geojson_geom)
    if not parcel_geom.is_valid:
        parcel_geom = parcel_geom.buffer(0)

    parcel_area = compute_polygon_area_m2(parcel_geom)

    # Calculate building density ratio
    bld_area_total = 0.0
    if associated_buildings:
        for b in associated_buildings:
            b_geom = shape(b["geometry"])
            bld_area_total += compute_polygon_area_m2(b_geom)

    density_ratio = round(min(1.0, bld_area_total / parcel_area if parcel_area > 0 else 0.0), 3)

    # Check for overlapping land-use feature
    best_match_id = None
    best_overlap_area = 0.0
    best_class = "RESIDENTIAL"
    best_source_type = "REFERENCE_GIS"

    for lu in landuse_features:
        if not lu.geometry_geojson:
            continue
        lu_geom = shape(lu.geometry_geojson)
        if parcel_geom.intersects(lu_geom):
            intersection_area = compute_polygon_area_m2(parcel_geom.intersection(lu_geom))
            if intersection_area > best_overlap_area:
                best_overlap_area = intersection_area
                best_match_id = lu.landuse_id
                best_class = lu.classification
                best_source_type = lu.source_type

    # Infer pattern if no reference overlap
    if not best_match_id:
        if density_ratio > 0.65:
            best_class = "COMMERCIAL"
        elif density_ratio > 0.15:
            best_class = "RESIDENTIAL"
        else:
            best_class = "OPEN_AREA"
        best_source_type = "AI_DERIVED"

    return ParcelLandUseSummary(
        parcel_id=parcel_id,
        dataset_id=dataset_id,
        region_id=region_id,
        observed_land_use_pattern=best_class,
        source_type=best_source_type,
        confidence=0.90,
        building_density_ratio=density_ratio,
        overlapping_landuse_id=best_match_id
    )
