"""
DrishtiGIS Phase 4 — Cross-tile deduplication of building footprints.

Context from tile overlap analysis:
  - All 48 overlap pairs are narrow ~61 m² strips (1–2 pixel wide seams)
  - No large-area duplicates exist between tiles
  - Duplicates arise ONLY when a building straddles a tile boundary seam
  - Strategy: centroid proximity in EPSG:32643 metric CRS
              If two buildings from adjacent tiles have centroids within
              DEDUP_CENTROID_DIST_M of each other AND polygon overlap > DEDUP_IOU_THRESH,
              they are considered the same physical building.
  - Retention policy: keep the polygon with the larger area (more complete geometry)

DEDUP_CENTROID_DIST_M = 5.0 m  (chosen based on ~2.17 cm/px × 2-pixel seam ≈ 0.04 m,
                                  but allow 5 m for positioning uncertainty at boundaries)
DEDUP_IOU_THRESH      = 0.15   (conservative — seam buildings have small overlap)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
import json
import math

try:
    from shapely.geometry import shape, mapping
    from shapely.ops import transform as shapely_transform
    from pyproj import Transformer
    _OK = True
except ImportError:
    _OK = False

DEDUP_CENTROID_DIST_M = 5.0    # metres — max centroid-to-centroid distance for candidates
DEDUP_IOU_THRESH      = 0.15   # minimum IoU to consider a duplicate

# Adjacent tile pairs (from tile_coverage.json — only these can produce edge duplicates)
# Format: frozenset({tile_a, tile_b})
ADJACENT_PAIRS: Set[frozenset] = {
    frozenset({"00_00", "00_01"}), frozenset({"00_01", "00_02"}),
    frozenset({"00_02", "00_03"}), frozenset({"00_03", "00_04"}),
    frozenset({"00_04", "00_05"}), frozenset({"00_05", "00_06"}),
    frozenset({"00_06", "00_07"}), frozenset({"00_07", "00_08"}),
    frozenset({"00_08", "00_09"}), frozenset({"00_09", "00_10"}),
    frozenset({"00_10", "00_11"}), frozenset({"00_11", "00_12"}),
    frozenset({"00_12", "00_13"}), frozenset({"00_13", "00_14"}),
    frozenset({"00_14", "00_15"}), frozenset({"00_15", "00_16"}),
    frozenset({"00_16", "00_17"}), frozenset({"00_17", "00_18"}),
    frozenset({"00_18", "00_19"}), frozenset({"00_19", "00_20"}),
    frozenset({"00_20", "00_21"}), frozenset({"00_21", "00_22"}),
    frozenset({"01_00", "01_01"}), frozenset({"01_01", "01_02"}),
    frozenset({"01_02", "01_03"}), frozenset({"01_03", "01_04"}),
    frozenset({"01_04", "01_05"}), frozenset({"01_05", "01_06"}),
    # Cross-row adjacency
    frozenset({"00_00", "01_00"}), frozenset({"00_01", "01_01"}),
    frozenset({"00_02", "01_02"}), frozenset({"00_03", "01_03"}),
    frozenset({"00_04", "01_04"}), frozenset({"00_05", "01_05"}),
    frozenset({"00_06", "01_06"}),
}


def _cen_32643(feature: dict) -> Tuple[float, float]:
    """Get centroid in EPSG:32643 from a feature's stored 4326 centroid."""
    props = feature["properties"]
    lon   = props["centroid_lon"]
    lat   = props["centroid_lat"]
    t = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    return t.transform(lon, lat)


def _geom_32643(feature: dict) -> object:
    """Convert feature geometry (4326) to EPSG:32643 Shapely polygon."""
    geom_4326 = shape(feature["geometry"])
    t = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    return shapely_transform(lambda x, y: t.transform(x, y), geom_4326)


def _centroid_dist_m(feat_a: dict, feat_b: dict) -> float:
    """Euclidean distance between two feature centroids in EPSG:32643 (metres)."""
    ax, ay = _cen_32643(feat_a)
    bx, by = _cen_32643(feat_b)
    return math.sqrt((ax - bx)**2 + (ay - by)**2)


def _polygon_iou(feat_a: dict, feat_b: dict) -> float:
    """Intersection-over-Union of two features' geometries in EPSG:32643."""
    try:
        ga = _geom_32643(feat_a)
        gb = _geom_32643(feat_b)
        inter = ga.intersection(gb).area
        union = ga.union(gb).area
        return inter / union if union > 0 else 0.0
    except Exception:
        return 0.0


def deduplicate_features(
    features: List[dict],
) -> Tuple[List[dict], int, int]:
    """
    Remove duplicate building features caused by tile-boundary overlaps.

    Algorithm:
      1. Group features by source tile
      2. For each adjacent tile pair, find candidate duplicates:
         - centroid distance ≤ DEDUP_CENTROID_DIST_M
         - polygon IoU ≥ DEDUP_IOU_THRESH
      3. For each duplicate pair, keep the polygon with larger area
      4. Assign stable final IDs (AI-BPL-FINAL-XXXXX)

    Args:
        features: All raw GeoJSON features from all tiles

    Returns:
        (deduplicated_features, n_removed, n_merged)
    """
    if not _OK:
        raise ImportError("shapely and pyproj required")

    # Index by tile
    by_tile: Dict[str, List[int]] = {}
    for i, feat in enumerate(features):
        tile = feat["properties"]["source_tile"]
        by_tile.setdefault(tile, []).append(i)

    # Find duplicate pairs
    to_remove: Set[int] = set()

    n_removed = 0
    n_merged  = 0

    for pair in ADJACENT_PAIRS:
        tiles = list(pair)
        if len(tiles) != 2:
            continue
        ta, tb = tiles[0], tiles[1]
        idxs_a = by_tile.get(ta, [])
        idxs_b = by_tile.get(tb, [])

        if not idxs_a or not idxs_b:
            continue

        for ia in idxs_a:
            if ia in to_remove:
                continue
            fa = features[ia]

            for ib in idxs_b:
                if ib in to_remove:
                    continue
                fb = features[ib]

                # Fast pre-filter: centroid proximity
                try:
                    dist = _centroid_dist_m(fa, fb)
                except Exception:
                    continue
                if dist > DEDUP_CENTROID_DIST_M:
                    continue

                # Accurate test: polygon IoU
                iou = _polygon_iou(fa, fb)
                if iou < DEDUP_IOU_THRESH:
                    continue

                # Duplicate found — keep larger area
                area_a = fa["properties"].get("area_m2", 0.0)
                area_b = fb["properties"].get("area_m2", 0.0)
                if area_a >= area_b:
                    to_remove.add(ib)
                else:
                    to_remove.add(ia)
                n_removed += 1
                break   # one match per feature

    # Filter and assign final stable IDs
    final_features = []
    counter = 0
    for i, feat in enumerate(features):
        if i in to_remove:
            continue
        feat = dict(feat)
        feat["properties"] = dict(feat["properties"])
        feat["properties"]["id"] = f"AI-BPL-FINAL-{counter:05d}"
        feat["properties"]["raw_id"] = features[i]["properties"].get("id", "")
        final_features.append(feat)
        counter += 1

    return final_features, n_removed, n_merged


def assign_stable_ids(features: List[dict]) -> List[dict]:
    """Assign sequential stable IDs to a list of features (in-place)."""
    for i, feat in enumerate(features):
        feat["properties"]["id"] = f"AI-BPL-FINAL-{i:05d}"
    return features
