"""
DrishtiGIS — Review & Spatial Recomputation GIS Engine
=========================================================
Phase 8: Surveyor Review, Ground-Truthing & Cadastral Geometry Editing

Provides:
1. Strict topology & geometry validation before saving reviewer edits.
2. CRS-aware spatial relationship recomputation (FULLY_WITHIN, CROSSES_BOUNDARY, NO_PARCEL_MATCH).
3. Dynamic discrepancy calculation strictly derived from spatial geometry.
"""

from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import transform
import pyproj

# Projection helper for metric calculations (EPSG:4326 to EPSG:3857)
_metric_transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform


def compute_geometry_area_m2(geom: Any) -> float:
    """Computes accurate metric area in m² for a Shapely geometry."""
    if geom is None or geom.is_empty:
        return 0.0
    try:
        metric_geom = transform(_metric_transformer, geom)
        return round(float(metric_geom.area), 2)
    except Exception:
        return 0.0


def validate_edited_geometry(
    geojson_geom: Dict[str, Any],
    crs: str = "EPSG:4326"
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validates an edited geometry before saving surveyor edits.

    Checks:
    - Valid GeoJSON dictionary format
    - Supported geometry type (Polygon or MultiPolygon)
    - Valid coordinate ring structure
    - Non-empty geometry
    - Shapely validity (no self-intersections, valid interior/exterior rings)
    - Non-zero metric area

    Returns:
        (is_valid, error_message, metadata_dict)
    """
    if not isinstance(geojson_geom, dict) or "type" not in geojson_geom or "coordinates" not in geojson_geom:
        return False, "Geometry requires correction before approval. Invalid GeoJSON structure.", {}

    geom_type = geojson_geom.get("type")
    if geom_type not in ["Polygon", "MultiPolygon"]:
        return False, f"Geometry requires correction before approval. Geometry type '{geom_type}' is not supported.", {}

    coords = geojson_geom.get("coordinates", [])
    if not coords or len(coords) == 0:
        return False, "Geometry requires correction before approval. Empty coordinate array.", {}

    # Inspect ring coordinates
    try:
        if geom_type == "Polygon":
            exterior_ring = coords[0]
            if len(exterior_ring) < 4:
                return False, "Geometry requires correction before approval. Polygon ring must have at least 4 points.", {}
            if exterior_ring[0] != exterior_ring[-1]:
                return False, "Geometry requires correction before approval. Polygon ring is not closed.", {}
        elif geom_type == "MultiPolygon":
            for poly in coords:
                if not poly or len(poly[0]) < 4:
                    return False, "Geometry requires correction before approval. MultiPolygon ring must have at least 4 points.", {}
    except Exception as e:
        return False, f"Geometry requires correction before approval. Invalid coordinate structure: {str(e)}", {}

    # Shapely validation
    try:
        geom = shape(geojson_geom)
    except Exception as e:
        return False, f"Geometry requires correction before approval. Failed to parse geometry: {str(e)}", {}

    if geom.is_empty:
        return False, "Geometry requires correction before approval. Geometry is empty.", {}

    if not geom.is_valid:
        return False, "Geometry requires correction before approval. Geometry is self-intersecting or invalid.", {}

    area_m2 = compute_geometry_area_m2(geom)
    if area_m2 <= 0.001:
        return False, "Geometry requires correction before approval. Geometry has zero or near-zero area.", {}

    metadata = {
        "area_m2": area_m2,
        "geometry_type": geom_type,
        "vertex_count": len(geom.exterior.coords) if geom_type == "Polygon" else sum(len(p.exterior.coords) for p in geom.geoms),
        "is_valid": True,
        "crs": crs,
    }

    return True, None, metadata


def recompute_parcel_building_relationships(
    parcel_geom_dict: Dict[str, Any],
    building_features: List[Dict[str, Any]],
    parcel_id: str
) -> Dict[str, Any]:
    """
    Recomputes parcel-building spatial relationships after parcel or building geometry is edited.

    Recomputes:
    - FULLY_WITHIN, CROSSES_BOUNDARY, NO_PARCEL_MATCH
    - overlap_ratio (intersection_area / building_area)
    - total_building_area_m2
    - building_count
    - coverage_ratio
    - derived discrepancies list
    """
    parcel_geom = shape(parcel_geom_dict)
    if not parcel_geom.is_valid:
        parcel_geom = parcel_geom.buffer(0)

    parcel_area_m2 = compute_geometry_area_m2(parcel_geom)

    recomputed_buildings: List[Dict[str, Any]] = []
    discrepancies: List[Dict[str, Any]] = []

    total_building_area = 0.0

    for idx, b_feat in enumerate(building_features):
        b_geom_dict = b_feat.get("geometry")
        if not b_geom_dict:
            continue

        b_geom = shape(b_geom_dict)
        if not b_geom.is_valid:
            b_geom = b_geom.buffer(0)

        b_area = compute_geometry_area_m2(b_geom)
        b_id = b_feat.get("properties", {}).get("id") or f"AI-BLD-{idx+1:04d}"

        if parcel_geom.intersects(b_geom):
            intersection = parcel_geom.intersection(b_geom)
            inter_area = compute_geometry_area_m2(intersection)
            overlap_ratio = round(inter_area / b_area, 4) if b_area > 0 else 0.0

            if overlap_ratio >= 0.95 or parcel_geom.contains(b_geom):
                relationship = "FULLY_WITHIN"
            else:
                relationship = "CROSSES_BOUNDARY"
                discrepancies.append({
                    "id": f"DISC-REV-{parcel_id}-{b_id}",
                    "parcel_id": parcel_id,
                    "building_id": b_id,
                    "type": "BUILDING_CROSSES_PARCEL_BOUNDARY",
                    "severity": "REVIEW",
                    "description": "AI-detected building intersects parcel boundary. Spatial relationship recomputed from edited geometry.",
                    "spatial_basis": {
                        "primary_overlap_ratio": overlap_ratio,
                        "building_area_m2": b_area,
                        "intersection_area_m2": inter_area,
                    },
                    "legal_status": None,
                    "source": "REVIEWED_AI_GEOMETRY",
                })
        else:
            overlap_ratio = 0.0
            relationship = "NO_PARCEL_MATCH"

        if relationship in ["FULLY_WITHIN", "CROSSES_BOUNDARY"]:
            total_building_area += b_area

        updated_props = dict(b_feat.get("properties", {}))
        updated_props.update({
            "parcel_relationship": relationship,
            "overlap_ratio": overlap_ratio,
            "building_area_m2": b_area,
            "primary_parcel_id": parcel_id if relationship != "NO_PARCEL_MATCH" else None
        })

        recomputed_buildings.append({
            "type": "Feature",
            "geometry": b_geom_dict,
            "properties": updated_props
        })

    # If multiple buildings are in parcel, append multiple buildings discrepancy
    if len(recomputed_buildings) > 1:
        discrepancies.append({
            "id": f"DISC-REV-{parcel_id}-MULTI",
            "parcel_id": parcel_id,
            "building_id": None,
            "type": "MULTIPLE_BUILDINGS_IN_PARCEL",
            "severity": "INFO",
            "description": f"Parcel contains {len(recomputed_buildings)} building footprints.",
            "spatial_basis": {
                "building_count": len(recomputed_buildings),
                "total_building_area_m2": round(total_building_area, 2),
            },
            "legal_status": None,
            "source": "REVIEWED_AI_GEOMETRY",
        })

    coverage_ratio = round(total_building_area / parcel_area_m2, 4) if parcel_area_m2 > 0 else 0.0

    return {
        "parcel_id": parcel_id,
        "parcel_area_m2": parcel_area_m2,
        "building_count": len(recomputed_buildings),
        "total_building_area_m2": round(total_building_area, 2),
        "coverage_ratio": coverage_ratio,
        "buildings": recomputed_buildings,
        "discrepancies": discrepancies,
    }
