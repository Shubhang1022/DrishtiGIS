"""
DrishtiGIS — India Location Search Endpoint
============================================
GET /api/v1/locations/search?q={query}

Returns matching Indian cities with their coverage availability.
Backed by a static city list — no external geocoding API required.

Never fabricates intelligence coverage for non-Bhopal cities.
"""

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.gis.india_cities import search_cities
from app.gis.coverage_registry import get_coverage, coverage_to_dict

router = APIRouter()


@router.get(
    "/search",
    summary="Search India cities/locations",
    tags=["locations"],
)
async def search_locations(
    q: str = Query(..., min_length=1, max_length=100, description="City or state name query"),
    country: str = Query(default="India", description="Country filter (currently only India supported)"),
) -> JSONResponse:
    """
    Search for Indian cities/locations.

    Returns city name, coordinates, default zoom level, and coverage
    availability for each match.

    Coverage availability reflects real data only:
    - Bhopal: imagery + parcels + AI analysis (prototype)
    - All other cities: map and OSM context only

    Results are capped at 10 to avoid excessive responses.
    The search uses a static list of major Indian cities — no external
    geocoding API is called.
    """
    matches = search_cities(q.strip(), limit=10)

    results = []
    for city in matches:
        coverage = get_coverage(city.name)
        results.append({
            "name":       city.name,
            "state":      city.state,
            "country":    "India",
            "center":     {"lat": city.lat, "lon": city.lon},
            "zoom_level": city.zoom,
            "coverage":   coverage_to_dict(coverage),
        })

    return JSONResponse(content={
        "query":   q,
        "country": country,
        "results": results,
        "total":   len(results),
    })
