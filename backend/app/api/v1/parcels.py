"""
DrishtiGIS — Parcels API v1
==============================
Placeholder endpoints that return demo data.

All responses include:
  X-Data-Status: demo-placeholder
  source: DEMO_DATA_PROTOTYPE_ONLY

These stubs will be replaced with real PostGIS queries in a later spec
once the database is seeded with processed data.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# Path to the demo data GeoJSON (relative to repo root)
_DEMO_DIR = Path(__file__).resolve().parents[4] / "drishtigis" / "lib" / "demo-data"
_DEMO_PARCELS_PATH  = _DEMO_DIR / "bhopal-parcels.geojson"
_DEMO_PROPS_PATH    = _DEMO_DIR / "properties.json"
_DEMO_DISC_PATH     = _DEMO_DIR / "bhopal-discrepancies.json"
_DEMO_AI_PATH       = _DEMO_DIR / "bhopal-ai-features.geojson"

_DEMO_HEADER = {"X-Data-Status": "demo-placeholder"}
_DISCLAIMER  = "Prototype demonstration data only — not official government records."


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("", summary="List parcels (demo placeholder)")
async def list_parcels(city: Optional[str] = None) -> JSONResponse:
    """
    Returns the demo parcel FeatureCollection.
    Filtered by city when provided — only 'Bhopal' has demo data.
    """
    data = _load_json(_DEMO_PARCELS_PATH)
    features = data.get("features", [])

    if city and city.lower() != "bhopal":
        features = []

    response_body = {
        "type": "FeatureCollection",
        "total": len(features),
        "features": features,
        "_source": "DEMO_DATA_PROTOTYPE_ONLY",
        "_disclaimer": _DISCLAIMER,
    }
    return JSONResponse(content=response_body, headers=_DEMO_HEADER)


@router.get("/{property_id}", summary="Get parcel by property_id (demo placeholder)")
async def get_parcel(property_id: str) -> JSONResponse:
    """
    Returns a single demo parcel feature by property_id (e.g. DRS-BPL-00101).
    Also includes the linked property record and any discrepancies.
    """
    parcels = _load_json(_DEMO_PARCELS_PATH)
    props   = _load_json(_DEMO_PROPS_PATH)
    discs   = _load_json(_DEMO_DISC_PATH)
    ai_feat = _load_json(_DEMO_AI_PATH)

    feature = next(
        (f for f in parcels["features"] if f["properties"]["property_id"] == property_id),
        None,
    )
    if not feature:
        raise HTTPException(
            status_code=404,
            detail=f"Parcel '{property_id}' not found in prototype dataset.",
        )

    parcel_id = feature["properties"]["id"]

    property_record = next(
        (p for p in props["properties"] if p["parcel_id"] == parcel_id),
        None,
    )
    discrepancies = [d for d in discs["discrepancies"] if d["parcel_id"] == parcel_id]
    ai_features   = [f for f in ai_feat["features"] if f["properties"]["associated_parcel_id"] == parcel_id]

    response_body = {
        "parcel":       feature,
        "property":     property_record,
        "discrepancies": discrepancies,
        "ai_features":  ai_features,
        "_source":      "DEMO_DATA_PROTOTYPE_ONLY",
        "_disclaimer":  _DISCLAIMER,
    }
    return JSONResponse(content=response_body, headers=_DEMO_HEADER)
