"""
DrishtiGIS — Coverage Availability Endpoints
=============================================
GET /api/v1/coverage/{city_slug}

Returns what intelligence data is available for a given city.
Only Bhopal has prototype data. All other cities return map-only coverage.

city_slug: lowercase, hyphenated (e.g., "bhopal", "new-delhi", "lucknow")
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.gis.coverage_registry import (
    get_coverage,
    coverage_to_dict,
    BHOPAL_DATASETS,
)

router = APIRouter()


@router.get(
    "/{city_slug}",
    summary="Coverage availability for a city",
    tags=["coverage"],
)
async def get_city_coverage(city_slug: str) -> JSONResponse:
    """
    Return coverage availability for a city identified by its slug.

    Slug format: lowercase, hyphens for spaces (e.g., 'bhopal', 'new-delhi').

    Only Bhopal currently has prototype intelligence data (imagery, parcels,
    AI analysis). All other cities return map and OSM context only.
    historical_data_available is always False — no multi-temporal imagery
    has been acquired for any city.
    """
    # Normalise slug to a city name
    city_name = city_slug.strip().replace("-", " ").title()
    coverage  = get_coverage(city_name)
    body      = coverage_to_dict(coverage)

    # Attach dataset registry for Bhopal
    if city_slug.lower() == "bhopal":
        body["datasets"] = BHOPAL_DATASETS

    return JSONResponse(content=body)
