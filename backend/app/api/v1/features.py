"""
DrishtiGIS — AI Features API v1
=================================
Phase 5: serves real AI-derived building footprints from the UAVPal pipeline.
Source: data/ai_output/bhopal-building-parcel-associations.geojson (834 features)

Endpoints:
  GET /api/v1/features
    ?parcel_id=<parcel_id>   — filter by primary_parcel_id
    ?city=<city>             — filter by city (only 'bhopal' has data)
    ?tile=<tile_id>          — filter by source_tile

Replaces the old demo placeholder that served bhopal-ai-features.geojson.
The old demo file is preserved at its original path for regression reference.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.app.auth.user_model import User
from backend.app.auth.dependencies import get_current_user

router = APIRouter()

# Real AI output (Phase 5 — with parcel associations)
_AI_ASSOC_PATH = (
    Path(__file__).resolve().parents[4]
    / "data" / "ai_output" / "bhopal-building-parcel-associations.geojson"
)

# Legacy demo file — preserved for regression reference; NOT served as production
_DEMO_AI_PATH = (
    Path(__file__).resolve().parents[4]
    / "drishtigis" / "lib" / "demo-data" / "bhopal-ai-features.geojson"
)

_DISCLAIMER = (
    "AI-derived building footprints from the UAVPal U-Net ResNet18 pipeline. "
    "NOT cadastral boundaries. NOT legal property boundaries. "
    "Spatial relationships with parcels are geometric observations only — "
    "they carry no legal weight. For research and visualization purposes only."
)

_HEADER = {"X-Data-Status": "real-ai-uavpal"}


@lru_cache(maxsize=1)
def _load_ai_features() -> list:
    """Load and cache the full AI features list (834 individual building footprints)."""
    with open(_AI_ASSOC_PATH, encoding="utf-8") as f:
        data = json.load(f)
    raw_features = data.get("features", [])
    normalized = []
    for f in raw_features:
        props = dict(f.get("properties", {}))
        b_id = props.get("id") or f.get("id") or f"AI-BPL-{len(normalized):05d}"
        f_copy = dict(f)
        f_copy["id"] = b_id

        # Expose explicit building properties per specification
        props["building_id"] = b_id
        props["source"] = props.get("source", "AI_DERIVED_UAVPAL")

        parent_id = props.get("primary_property_id") or props.get("primary_parcel_id")
        props["parent_parcel_id"] = parent_id if parent_id else "No parcel match"

        rel = props.get("parcel_relationship", "UNKNOWN")
        props["boundary_status"] = rel

        if rel == "CROSSES_BOUNDARY":
            props["review_status"] = "FLAGGED_OVERHANG"
        elif rel == "PARTIALLY_OVERLAPS":
            props["review_status"] = "PARTIAL_ENCROACHMENT"
        elif rel == "FULLY_WITHIN":
            props["review_status"] = "VERIFIED"
        else:
            props["review_status"] = "UNASSOCIATED"

        props["land_use"] = props.get("land_use") or "Residential / Built-up"

        f_copy["properties"] = props
        normalized.append(f_copy)

    return normalized


@router.get("", summary="List AI building features (real UAVPal output)")
async def list_features(
    parcel_id: Optional[str] = None,
    city:      Optional[str] = None,
    tile:      Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Returns real AI-derived building footprints with parcel associations.

    Filters:
      parcel_id — filter by primary_parcel_id (e.g. parcel-bpl-001)
      city      — only 'bhopal' has data; other cities return empty collection
      tile      — filter by source_tile (e.g. 00_10)
    """
    # Non-Bhopal cities: honest unavailable
    if city and city.lower() != "bhopal":
        return JSONResponse(
            content={
                "type":        "FeatureCollection",
                "total":       0,
                "features":    [],
                "_source":     "AI_DERIVED_UAVPAL",
                "ai_available": False,
                "_coverage_note": (
                    f"No AI building data available for {city.title()}. "
                    "DrishtiGIS currently has real AI building data for Bhopal only."
                ),
                "_disclaimer": _DISCLAIMER,
            },
            headers=_HEADER,
        )

    features = _load_ai_features()

    # Apply filters
    if parcel_id:
        features = [
            f for f in features
            if f["properties"].get("primary_parcel_id") == parcel_id
            or f["properties"].get("parent_parcel_id") == parcel_id
        ]
    if tile:
        features = [
            f for f in features
            if f["properties"].get("source_tile") == tile
        ]

    return JSONResponse(
        content={
            "type":        "FeatureCollection",
            "total":       len(features),
            "features":    features,
            "_source":     "AI_DERIVED_UAVPAL",
            "ai_available": True,
            "_disclaimer": _DISCLAIMER,
        },
        headers=_HEADER,
    )


@router.get("/stats", summary="AI feature statistics")
async def feature_stats() -> JSONResponse:
    """Return high-level statistics about the real AI building dataset."""
    features = _load_ai_features()
    rel_counts: dict[str, int] = {}
    for f in features:
        rel = f["properties"].get("parcel_relationship", "UNKNOWN")
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

    return JSONResponse(
        content={
            "total_buildings":   len(features),
            "parcel_matched":    sum(1 for f in features if f["properties"].get("primary_parcel_id")),
            "parcel_unmatched":  sum(1 for f in features if not f["properties"].get("primary_parcel_id")),
            "relationship_breakdown": rel_counts,
            "_source":           "AI_DERIVED_UAVPAL",
        },
        headers=_HEADER,
    )
