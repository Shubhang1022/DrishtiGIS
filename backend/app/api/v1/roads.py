"""
DrishtiGIS — Roads & Access Corridors API Router
==================================================
Endpoints for querying road networks, road classification, and parcel access corridor analysis.

DISCLAIMER: All road access analysis represents spatial geometry proximity.
It does NOT constitute legal property access rights or official land record status.
"""

from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path as FastPath, status

from backend.app.models.road import RoadFeature, AccessCorridorSummary
from backend.app.gis.road_engine import process_road_features, analyze_parcel_access

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
OSM_ROADS_FILE = PROJECT_ROOT / "data" / "osm" / "bhopal-extract" / "bhopal-roads.geojson"
SYNTHETIC_PARCELS_FILE = PROJECT_ROOT / "data" / "synthetic" / "bhopal-synthetic-parcels.geojson"


def load_raw_roads() -> List[Dict[str, Any]]:
    """Loads raw OSM road GeoJSON features."""
    if not OSM_ROADS_FILE.exists():
        return []
    try:
        with open(OSM_ROADS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("features", [])
    except Exception as e:
        print(f"Error loading OSM roads: {e}")
        return []


def load_synthetic_parcels() -> List[Dict[str, Any]]:
    """Loads synthetic parcel GeoJSON features."""
    if not SYNTHETIC_PARCELS_FILE.exists():
        return []
    try:
        with open(SYNTHETIC_PARCELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("features", [])
    except Exception as e:
        print(f"Error loading synthetic parcels: {e}")
        return []


@router.get(
    "/",
    response_model=List[RoadFeature],
    summary="List Road Features",
    description="Returns road features with metric segment lengths and estimated widths."
)
async def list_roads(
    city: Optional[str] = Query(None, description="Filter by city name"),
    road_class: Optional[str] = Query(None, description="Filter by road class (PRIMARY, SECONDARY, LOCAL, ACCESS, PATHWAY)"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return")
):
    raw = load_raw_roads()
    roads = process_road_features(raw, city=city or "Bhopal")

    if road_class:
        roads = [r for r in roads if r.road_class.upper() == road_class.upper()]

    return roads[:limit]


@router.get(
    "/{road_id}",
    response_model=RoadFeature,
    summary="Get Road Feature Details",
    description="Returns details for a specific road feature."
)
async def get_road(road_id: str = FastPath(..., description="Road feature identifier")):
    raw = load_raw_roads()
    roads = process_road_features(raw)
    for r in roads:
        if r.road_id == road_id:
            return r
    raise HTTPException(status_code=404, detail=f"Road feature '{road_id}' not found.")


@router.get(
    "/access/{parcel_id}",
    response_model=AccessCorridorSummary,
    summary="Analyze Parcel Access Corridor",
    description="Analyzes spatial road proximity and access corridor status for a specific parcel."
)
async def get_parcel_access(parcel_id: str = FastPath(..., description="Parcel / Property identifier")):
    parcels = load_synthetic_parcels()
    matched_parcel = None
    for p in parcels:
        props = p.get("properties", {})
        if props.get("property_id") == parcel_id or props.get("id") == parcel_id:
            matched_parcel = p
            break

    if not matched_parcel and parcels:
        matched_parcel = parcels[0]

    if not matched_parcel:
        raise HTTPException(status_code=404, detail=f"Parcel '{parcel_id}' not found.")

    raw_roads = load_raw_roads()
    processed_roads = process_road_features(raw_roads)

    summary = analyze_parcel_access(
        parcel_id=parcel_id,
        parcel_geojson_geom=matched_parcel["geometry"],
        road_features=processed_roads
    )

    return summary
