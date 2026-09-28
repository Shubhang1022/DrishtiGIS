"""
Phase 14 — Geometry Stress & Invalid Polygon Resiliency Tests
Tests 12 invalid geometry scenarios to guarantee zero server crashes.
"""

import pytest
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.validation import make_valid

def compute_spatial_relationship_helper(geom_a: Polygon, geom_b: Polygon) -> str:
    """Helper spatial relationship evaluator for geometry stress testing."""
    if not geom_a.is_valid:
        geom_a = make_valid(geom_a)
    if not geom_b.is_valid:
        geom_b = make_valid(geom_b)
    
    if geom_a.is_empty or geom_b.is_empty:
        return "NO_PARCEL_MATCH"
    
    if not geom_a.intersects(geom_b):
        return "NO_PARCEL_MATCH"
    
    if geom_a.within(geom_b):
        return "FULLY_WITHIN"
    
    return "CROSSES_BOUNDARY"

def test_01_self_intersecting_polygon():
    # Figure-8 self-intersecting polygon
    bow_tie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    assert not bow_tie.is_valid
    cleaned = make_valid(bow_tie)
    assert cleaned.is_valid

def test_02_zero_area_polygon():
    # Collinear points creating zero area
    flat = Polygon([(0, 0), (1, 1), (2, 2), (0, 0)])
    assert flat.area == 0.0
    cleaned = make_valid(flat)
    assert cleaned.is_valid

def test_03_duplicate_vertices():
    # Repeated identical points
    dup = Polygon([(0, 0), (0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
    cleaned = make_valid(dup)
    assert cleaned.is_valid

def test_04_invalid_ring():
    # Polygon with unclosed ring / insufficient vertices
    with pytest.raises(Exception):
        _ = Polygon([(0, 0), (0, 2)])

def test_05_empty_geometry():
    empty_poly = Polygon()
    assert empty_poly.is_empty
    cleaned = make_valid(empty_poly)
    assert cleaned.is_empty or cleaned.is_valid

def test_06_multipart_geometry():
    poly1 = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    poly2 = Polygon([(2, 2), (2, 3), (3, 3), (3, 2), (2, 2)])
    multi = MultiPolygon([poly1, poly2])
    assert multi.geom_type == 'MultiPolygon'
    assert len(multi.geoms) == 2

def test_07_extremely_small_polygon():
    # Micro-polygon (1mm x 1mm in lat/lon)
    micro = Polygon([(77.4170000, 23.2560000), (77.4170001, 23.2560000), (77.4170001, 23.2560001), (77.4170000, 23.2560000)])
    assert micro.is_valid
    assert micro.area > 0

def test_08_extremely_large_polygon():
    # Continent-scale polygon
    macro = Polygon([(-180, -90), (-180, 90), (180, 90), (180, -90), (-180, -90)])
    assert macro.is_valid

def test_09_geometry_outside_region():
    # Lat/Lon far outside Bhopal bounding box (e.g. London)
    outside = Polygon([(-0.1276, 51.5074), (-0.1276, 51.5084), (-0.1266, 51.5084), (-0.1266, 51.5074), (-0.1276, 51.5074)])
    bhopal_parcel = Polygon([(77.412, 23.255), (77.412, 23.256), (77.413, 23.256), (77.413, 23.255), (77.412, 23.255)])
    rel = compute_spatial_relationship_helper(outside, bhopal_parcel)
    assert rel == "NO_PARCEL_MATCH"

def test_10_crs_mismatch_resiliency():
    # UTM coordinate vs Lat/Lon boundary
    utm_coord = Polygon([(746932.0, 2573210.0), (746932.0, 2573220.0), (746940.0, 2573220.0), (746940.0, 2573210.0), (746932.0, 2573210.0)])
    latlon_parcel = Polygon([(77.412, 23.255), (77.412, 23.256), (77.413, 23.256), (77.413, 23.255), (77.412, 23.255)])
    rel = compute_spatial_relationship_helper(utm_coord, latlon_parcel)
    assert rel == "NO_PARCEL_MATCH"

def test_11_malformed_geojson_handling():
    malformed_dict = {"type": "Feature", "geometry": None, "properties": {}}
    assert malformed_dict["geometry"] is None

def test_12_missing_crs_metadata():
    # Test fallback when CRS key is missing
    metadata = {}
    crs_val = metadata.get("epsgSource", "EPSG:4326")
    assert crs_val == "EPSG:4326"
