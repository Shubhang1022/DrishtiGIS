"""
DrishtiGIS — Land-Use Intelligence API Router
================================================
Endpoints for querying land-use polygons and observed parcel land-use pattern analysis.

DISCLAIMER: All observed land-use classifications represent AI-derived visual patterns
or reference GIS data. They do NOT constitute official legal land-use designations,
permitted zoning uses, or property ownership titles.
"""

from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path as FastPath, status

from backend.app.models.landuse import LandUseFeature, ParcelLandUseSummary
from backend.app.gis.landuse_engine import process_landuse_features, analyze_parcel_landuse

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
OSM_LANDUSE_FILE = PROJECT_ROOT / "data" / "osm" / "bhopal-extract" / "bhopal-landuse.geojson"
SYNTHETIC_PARCELS_FILE = PROJECT_ROOT / "data" / "synthetic" / "bhopal-synthetic-parcels.geojson"
AI_BUILDINGS_FILE = PROJECT_ROOT / "data" / "ai_output" / "bhopal-building-parcel-associations.geojson"


def load_raw_landuse() -> List[Dict[str, Any]]:
    """Loads raw OSM land-use GeoJSON features."""
    if not OSM_LANDUSE_FILE.exists():
        return []
    try:
        with open(OSM_LANDUSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("features", [])
    except Exception as e:
        print(f"Error loading OSM landuse: {e}")
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


def load_ai_buildings() -> List[Dict[str, Any]]:
    """Loads AI building features."""
    if not AI_BUILDINGS_FILE.exists():
        return []
    try:
        with open(AI_BUILDINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("features", [])
    except Exception as e:
        print(f"Error loading AI buildings: {e}")
        return []


@router.get(
    "/",
    response_model=List[LandUseFeature],
    summary="List Land-Use Features",
    description="Returns land-use polygon features with metric areas and classification metadata."
)
async def list_landuse(
    city: Optional[str] = Query(None, description="Filter by city name"),
    classification: Optional[str] = Query(None, description="Filter by classification (RESIDENTIAL, COMMERCIAL, INDUSTRIAL, etc.)"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return")
):
    raw = load_raw_landuse()
    landuses = process_landuse_features(raw, city=city or "Bhopal")

    if classification:
        landuses = [lu for lu in landuses if lu.classification.upper() == classification.upper()]

    return landuses[:limit]


@router.get(
    "/{landuse_id}",
    response_model=LandUseFeature,
    summary="Get Land-Use Feature Details",
    description="Returns details for a specific land-use feature."
)
async def get_landuse(landuse_id: str = FastPath(..., description="Land-use feature identifier")):
    raw = load_raw_landuse()
    landuses = process_landuse_features(raw)
    for lu in landuses:
        if lu.landuse_id == landuse_id:
            return lu
    raise HTTPException(status_code=404, detail=f"Land-use feature '{landuse_id}' not found.")


@router.get(
    "/parcel/{parcel_id}",
    response_model=ParcelLandUseSummary,
    summary="Analyze Observed Parcel Land-Use Pattern",
    description="Analyzes spatial land-use coverage and building density to derive observed land-use pattern."
)
async def get_parcel_landuse(parcel_id: str = FastPath(..., description="Parcel / Property identifier")):
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

    raw_landuses = load_raw_landuse()
    processed_landuses = process_landuse_features(raw_landuses)
    all_buildings = load_ai_buildings()

    parcel_buildings = [
        b for b in all_buildings
        if b.get("properties", {}).get("primary_parcel_id") == parcel_id
        or b.get("properties", {}).get("property_id") == parcel_id
    ]

    summary = analyze_parcel_landuse(
        parcel_id=parcel_id,
        parcel_geojson_geom=matched_parcel["geometry"],
        landuse_features=processed_landuses,
        associated_buildings=parcel_buildings
    )

    return summary
