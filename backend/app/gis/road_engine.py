"""
DrishtiGIS — GIS Road & Access Corridor Processing Engine
============================================================
CRS-aware spatial processing for road feature extraction, centerline length,
width estimation, spatial indexing, and parcel access corridor proximity analysis.

DISCLAIMER: All access corridor analysis represents spatial geometry proximity.
It does NOT constitute legal property access rights or official land record status.
"""

from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import shape, mapping, Polygon, LineString, MultiLineString
from shapely.strtree import STRtree
from shapely.ops import transform
import pyproj

from backend.app.models.road import RoadFeature, AccessCorridorSummary

# Spatial transformation helper for EPSG:4326 to metric EPSG:3857
_project_to_metric = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform


def compute_line_length_m(geom: Any) -> float:
    """Computes length of LineString / MultiLineString in meters using EPSG:3857 metric projection."""
    if geom is None or geom.is_empty:
        return 0.0
    metric_geom = transform(_project_to_metric, geom)
    return round(float(metric_geom.length), 2)


def compute_parcel_road_distance_m(parcel_geom: Any, road_geom: Any) -> float:
    """Computes minimum spatial distance between parcel boundary and road in meters."""
    if parcel_geom is None or road_geom is None or parcel_geom.is_empty or road_geom.is_empty:
        return 99999.0
    metric_parcel = transform(_project_to_metric, parcel_geom)
    metric_road = transform(_project_to_metric, road_geom)
    return round(float(metric_parcel.distance(metric_road)), 2)


def process_road_features(
    raw_geojson_features: List[Dict[str, Any]],
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01",
    city: str = "Bhopal",
    state: str = "Madhya Pradesh",
    source_name: str = "OpenStreetMap",
    source_type: str = "REFERENCE_GIS"
) -> List[RoadFeature]:
    """Parses raw road GeoJSON features into normalized RoadFeature models with metric attributes."""
    results: List[RoadFeature] = []

    for idx, f in enumerate(raw_geojson_features):
        props = f.get("properties", {})
        geom_dict = f.get("geometry")
        if not geom_dict:
            continue

        geom = shape(geom_dict)
        if not geom.is_valid:
            geom = geom.buffer(0)

        road_id = str(props.get("osm_id") or props.get("id") or f"ROAD-{idx+1:04d}")
        road_class_raw = str(props.get("highway") or props.get("road_class") or "LOCAL").upper()

        # Map OpenStreetMap highway tags to standardized road classes
        if road_class_raw in ["PRIMARY", "TRUNK", "MOTORWAY"]:
            std_class = "PRIMARY"
            est_width = 12.0
        elif road_class_raw in ["SECONDARY", "TERTIARY"]:
            std_class = "SECONDARY"
            est_width = 8.0
        elif road_class_raw in ["RESIDENTIAL", "UNCLASSIFIED", "LOCAL", "LIVING_STREET"]:
            std_class = "LOCAL"
            est_width = 5.5
        elif road_class_raw in ["SERVICE", "ACCESS", "TRACK"]:
            std_class = "ACCESS"
            est_width = 3.5
        elif road_class_raw in ["FOOTWAY", "PATH", "PEDESTRIAN", "STEPS"]:
            std_class = "PATHWAY"
            est_width = 2.0
        else:
            std_class = "LOCAL"
            est_width = 4.5

        length_m = compute_line_length_m(geom)
        road_name = props.get("name")

        results.append(RoadFeature(
            road_id=road_id,
            dataset_id=dataset_id,
            region_id=region_id,
            city=city,
            state=state,
            country="India",
            crs="EPSG:4326",
            source=source_name,
            source_type=source_type,
            road_class=std_class,
            name=road_name,
            surface_type=props.get("surface", "PAVED").upper(),
            estimated_width_m=est_width,
            length_m=length_m,
            confidence=float(props.get("confidence", 0.95)) if source_type == "AI_DERIVED" else None,
            geometry_geojson=mapping(geom),
            review_status="UNREVIEWED"
        ))

    return results


def analyze_parcel_access(
    parcel_id: str,
    parcel_geojson_geom: Dict[str, Any],
    road_features: List[RoadFeature],
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01",
    proximity_buffer_m: float = 50.0
) -> AccessCorridorSummary:
    """Analyzes road access corridor spatial relationships for a specific parcel geometry."""
    parcel_geom = shape(parcel_geojson_geom)
    if not parcel_geom.is_valid:
        parcel_geom = parcel_geom.buffer(0)

    if not road_features:
        return AccessCorridorSummary(
            parcel_id=parcel_id,
            dataset_id=dataset_id,
            region_id=region_id,
            access_status="ACCESS_REVIEW_REQUIRED",
            has_direct_access=False,
            nearest_road_id=None,
            nearest_road_name=None,
            nearest_road_class=None,
            distance_to_road_m=999.0,
            nearby_road_count=0
        )

    # Parse road geometries into Shapely objects
    road_geoms = [shape(r.geometry_geojson) for r in road_features if r.geometry_geojson]
    tree = STRtree(road_geoms) if road_geoms else None

    nearest_road: Optional[RoadFeature] = None
    min_dist = 99999.0
    nearby_count = 0

    metric_parcel = transform(_project_to_metric, parcel_geom)
    buffered_parcel = metric_parcel.buffer(proximity_buffer_m)

    for idx, r in enumerate(road_features):
        if not r.geometry_geojson:
            continue
        r_geom = shape(r.geometry_geojson)
        dist = compute_parcel_road_distance_m(parcel_geom, r_geom)
        if dist < min_dist:
            min_dist = dist
            nearest_road = r
        if dist <= proximity_buffer_m:
            nearby_count += 1

    has_direct = min_dist <= 2.0  # Within 2 meters considered adjoining/direct access

    if has_direct or min_dist <= 15.0:
        access_status = "ACCESS_DETECTED"
    elif min_dist <= 50.0:
        access_status = "ACCESS_REVIEW_REQUIRED"
    else:
        access_status = "NO_DETECTED_ACCESS_CORRIDOR"

    return AccessCorridorSummary(
        parcel_id=parcel_id,
        dataset_id=dataset_id,
        region_id=region_id,
        access_status=access_status,
        has_direct_access=has_direct,
        nearest_road_id=nearest_road.road_id if nearest_road else None,
        nearest_road_name=nearest_road.name if nearest_road else None,
        nearest_road_class=nearest_road.road_class if nearest_road else None,
        distance_to_road_m=min_dist if min_dist < 99999 else 0.0,
        nearby_road_count=nearby_count
    )
