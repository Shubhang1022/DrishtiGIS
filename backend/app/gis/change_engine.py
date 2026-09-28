"""
DrishtiGIS — Spatial Building Change Detection Engine
======================================================
CRS-aware vector polygon comparison engine for temporal building extractions.
Calculates IoU, centroid shift, area deltas, and change classifications.

DISCLAIMER: All output observations represent spatial geometry differences derived
from AI processing. They do NOT constitute legal conclusions, property title changes,
or official cadastral determinations.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import transform
import pyproj

from backend.app.models.epoch import BuildingChangeItem, ParcelChangeSummary

# Spatial transformation helper for EPSG:4326 to metric EPSG:3857
_project_to_metric = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
_project_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform


def compute_polygon_area_m2(geom: Any) -> float:
    """Computes area in square meters using EPSG:3857 metric projection."""
    if geom is None or geom.is_empty:
        return 0.0
    metric_geom = transform(_project_to_metric, geom)
    return round(float(metric_geom.area), 2)


def compute_centroid_distance_m(geom1: Any, geom2: Any) -> float:
    """Computes distance between centroids of two geometries in meters."""
    if geom1 is None or geom2 is None or geom1.is_empty or geom2.is_empty:
        return 0.0
    c1 = transform(_project_to_metric, geom1.centroid)
    c2 = transform(_project_to_metric, geom2.centroid)
    return round(float(c1.distance(c2)), 2)


def compute_iou(geom1: Any, geom2: Any) -> float:
    """Computes Intersection over Union (IoU) ratio between two Shapely geometries."""
    if geom1 is None or geom2 is None or geom1.is_empty or geom2.is_empty:
        return 0.0
    intersection_area = geom1.intersection(geom2).area
    union_area = geom1.union(geom2).area
    if union_area <= 0:
        return 0.0
    return round(float(intersection_area / union_area), 4)


def compare_building_epochs(
    baseline_buildings: List[Dict[str, Any]],
    target_buildings: List[Dict[str, Any]],
    parcel_id: Optional[str] = None,
    iou_unchanged_threshold: float = 0.85,
    iou_modified_threshold: float = 0.10,
) -> List[BuildingChangeItem]:
    """
    Compares building features between two temporal epochs and returns change observations.
    
    Classification rules:
      - IoU >= 0.85: UNCHANGED
      - 0.10 <= IoU < 0.85: MODIFIED
      - Baseline building unmatched in target: REMOVED
      - Target building unmatched in baseline: ADDED
    """
    results: List[BuildingChangeItem] = []

    # Parse baseline features into Shapely objects
    base_items: List[Tuple[str, Any, float, Dict[str, Any]]] = []
    for idx, f in enumerate(baseline_buildings):
        b_id = str(f.get("properties", {}).get("id") or f.get("id") or f"base-bld-{idx}")
        g = shape(f["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        area = compute_polygon_area_m2(g)
        base_items.append((b_id, g, area, f))

    # Parse target features into Shapely objects
    tgt_items: List[Tuple[str, Any, float, Dict[str, Any]]] = []
    for idx, f in enumerate(target_buildings):
        t_id = str(f.get("properties", {}).get("id") or f.get("id") or f"tgt-bld-{idx}")
        g = shape(f["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        area = compute_polygon_area_m2(g)
        tgt_items.append((t_id, g, area, f))

    matched_tgt_indices = set()
    matched_base_indices = set()

    # Spatial indexing using STRtree on target geometries
    tgt_geoms = [t[1] for t in tgt_items]
    tree = STRtree(tgt_geoms) if tgt_geoms else None

    # Step 1: Match baseline buildings against target buildings
    for b_idx, (b_id, b_geom, b_area, b_feat) in enumerate(base_items):
        best_tgt_idx = None
        best_iou = 0.0

        if tree and not b_geom.is_empty:
            possible_matches = tree.query(b_geom)
            for candidate in possible_matches:
                # Identify index of candidate geometry safely (handles Shapely 2.x numpy indices)
                if hasattr(candidate, "item"):
                    t_idx = int(candidate.item())
                elif isinstance(candidate, int):
                    t_idx = candidate
                else:
                    try:
                        t_idx = tgt_geoms.index(candidate)
                    except ValueError:
                        continue

                if t_idx < 0 or t_idx >= len(tgt_geoms):
                    continue

                t_geom = tgt_geoms[t_idx]
                iou = compute_iou(b_geom, t_geom)
                if iou > best_iou:
                    best_iou = iou
                    best_tgt_idx = t_idx

        if best_tgt_idx is not None and best_iou >= iou_modified_threshold:
            matched_base_indices.add(b_idx)
            matched_tgt_indices.add(best_tgt_idx)
            t_id, t_geom, t_area, t_feat = tgt_items[best_tgt_idx]

            change_type = "UNCHANGED" if best_iou >= iou_unchanged_threshold else "MODIFIED"
            centroid_shift = compute_centroid_distance_m(b_geom, t_geom)
            area_delta = round(t_area - b_area, 2)

            results.append(BuildingChangeItem(
                change_id=f"CHG-{b_id}-{t_id}",
                change_type=change_type,
                baseline_building_id=b_id,
                target_building_id=t_id,
                parcel_id=parcel_id,
                area_baseline_m2=b_area,
                area_target_m2=t_area,
                area_delta_m2=area_delta,
                iou_score=best_iou,
                centroid_shift_m=centroid_shift,
                confidence_score=round(float(b_feat.get("properties", {}).get("confidence", 0.90)), 2),
                geometry_geojson=mapping(t_geom),
            ))

    # Step 2: Identify REMOVED buildings (in baseline but unmatched in target)
    for b_idx, (b_id, b_geom, b_area, b_feat) in enumerate(base_items):
        if b_idx not in matched_base_indices:
            results.append(BuildingChangeItem(
                change_id=f"CHG-RMV-{b_id}",
                change_type="REMOVED",
                baseline_building_id=b_id,
                target_building_id=None,
                parcel_id=parcel_id,
                area_baseline_m2=b_area,
                area_target_m2=0.0,
                area_delta_m2=-b_area,
                iou_score=0.0,
                centroid_shift_m=0.0,
                confidence_score=round(float(b_feat.get("properties", {}).get("confidence", 0.90)), 2),
                geometry_geojson=mapping(b_geom),
            ))

    # Step 3: Identify ADDED buildings (in target but unmatched in baseline)
    for t_idx, (t_id, t_geom, t_area, t_feat) in enumerate(tgt_items):
        if t_idx not in matched_tgt_indices:
            results.append(BuildingChangeItem(
                change_id=f"CHG-ADD-{t_id}",
                change_type="ADDED",
                baseline_building_id=None,
                target_building_id=t_id,
                parcel_id=parcel_id,
                area_baseline_m2=0.0,
                area_target_m2=t_area,
                area_delta_m2=t_area,
                iou_score=0.0,
                centroid_shift_m=0.0,
                confidence_score=round(float(t_feat.get("properties", {}).get("confidence", 0.90)), 2),
                geometry_geojson=mapping(t_geom),
            ))

    return results


def summarize_parcel_changes(
    parcel_id: str,
    baseline_epoch_id: str,
    target_epoch_id: str,
    baseline_buildings: List[Dict[str, Any]],
    target_buildings: List[Dict[str, Any]],
) -> ParcelChangeSummary:
    """Summarizes building footprint change detection for a single parcel/property."""
    changes = compare_building_epochs(
        baseline_buildings=baseline_buildings,
        target_buildings=target_buildings,
        parcel_id=parcel_id
    )

    added = [c for c in changes if c.change_type == "ADDED"]
    removed = [c for c in changes if c.change_type == "REMOVED"]
    modified = [c for c in changes if c.change_type == "MODIFIED"]
    unchanged = [c for c in changes if c.change_type == "UNCHANGED"]

    total_area_change = round(sum(c.area_delta_m2 for c in changes), 2)

    return ParcelChangeSummary(
        parcel_id=parcel_id,
        baseline_epoch_id=baseline_epoch_id,
        target_epoch_id=target_epoch_id,
        baseline_building_count=len(baseline_buildings),
        target_building_count=len(target_buildings),
        added_count=len(added),
        removed_count=len(removed),
        modified_count=len(modified),
        unchanged_count=len(unchanged),
        total_area_change_m2=total_area_change,
        changes=changes
    )
