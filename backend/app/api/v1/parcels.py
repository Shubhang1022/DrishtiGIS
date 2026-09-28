"""
DrishtiGIS — Parcels API v1
==============================
Phase 5.5: serves 35 synthetic demo parcels (SYNTHETIC_DEMO) as primary dataset.
Maintains backward compatibility with legacy 3-parcel demo (DRS-BPL-00101/02/03).
AI building analysis is AI_DERIVED_UAVPAL (real UAVPal pipeline output).

Endpoints:
  GET /api/v1/parcels?city=<city>
  GET /api/v1/parcels/{property_id}
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from backend.app.auth.user_model import User
from backend.app.auth.dependencies import get_current_user

router = APIRouter()

ROOT = Path(__file__).resolve().parents[4]

# ── Data paths ────────────────────────────────────────────────────────────────

# Phase 5.5: synthetic dataset (35 parcels, SYNTHETIC_DEMO)
_SYNTHETIC_PARCELS   = ROOT / "data" / "synthetic" / "bhopal-synthetic-parcels.geojson"
_SYNTHETIC_PROPS     = ROOT / "data" / "synthetic" / "bhopal-synthetic-properties.json"

# Legacy demo (3 parcels, DEMO_DATA_PROTOTYPE_ONLY) — kept for backward compat
_LEGACY_DIR          = ROOT / "drishtigis" / "lib" / "demo-data"
_LEGACY_PARCELS      = _LEGACY_DIR / "bhopal-parcels.geojson"
_LEGACY_PROPS        = _LEGACY_DIR / "properties.json"

# Real AI output (Phase 5+)
_AI_ASSOC_PATH       = ROOT / "data" / "ai_output" / "bhopal-building-parcel-associations.geojson"
_DISC_PATH           = ROOT / "data" / "ai_output" / "bhopal-discrepancies.json"
_TOPO_PATH           = ROOT / "data" / "synthetic" / "topology_validation.json"

_SYNTHETIC_HEADER    = {"X-Data-Status": "synthetic-demo-parcel-real-ai"}
_LEGACY_HEADER       = {"X-Data-Status": "demo-placeholder-parcel-real-ai"}
_SYNTHETIC_DISCLAIMER = (
    "Synthetic prototype data — not an official land record. "
    "All identifiers, owner names, and property data are synthetic."
)
_LEGACY_DISCLAIMER   = "Prototype demonstration parcel data only — not official government records."
_AI_DISCLAIMER       = (
    "AI analysis is derived from the UAVPal U-Net ResNet18 pipeline. "
    "NOT cadastral boundaries. NOT legal determinations. "
    "Spatial relationships are geometric observations only."
)


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_synthetic_parcels() -> list:
    return _load_json(_SYNTHETIC_PARCELS).get("features", [])


def _load_synthetic_props() -> list:
    return _load_json(_SYNTHETIC_PROPS).get("properties", [])


@lru_cache(maxsize=1)
def _load_legacy_parcels() -> list:
    return _load_json(_LEGACY_PARCELS).get("features", [])


@lru_cache(maxsize=1)
def _load_legacy_props() -> list:
    return _load_json(_LEGACY_PROPS).get("properties", [])


@lru_cache(maxsize=1)
def _load_ai_features() -> list:
    return _load_json(_AI_ASSOC_PATH).get("features", [])


@lru_cache(maxsize=1)
def _load_discrepancies() -> list:
    return _load_json(_DISC_PATH).get("discrepancies", [])


# ── AI analysis helper ─────────────────────────────────────────────────────────

def _build_ai_analysis(parcel_id: str, parcel_area_m2: float) -> dict:
    all_buildings = _load_ai_features()
    buildings     = [f for f in all_buildings if f["properties"].get("primary_parcel_id") == parcel_id]
    all_discs     = _load_discrepancies()
    discs         = [d for d in all_discs if d.get("parcel_id") == parcel_id]

    total_area    = sum(f["properties"].get("building_area_m2", 0) for f in buildings)
    avg_conf      = (
        sum(f["properties"].get("confidence", 0) for f in buildings) / len(buildings)
        if buildings else None
    )
    coverage_ratio = round(total_area / parcel_area_m2, 4) if parcel_area_m2 > 0 else None

    return {
        "ai_available":           True,
        "building_count":         len(buildings),
        "total_detected_area_m2": round(total_area, 2),
        "average_confidence":     round(avg_conf, 4) if avg_conf else None,
        "discrepancy_count":      len(discs),
        "buildings": [
            {
                "id":                 f["properties"].get("id"),
                "area_m2":            f["properties"].get("building_area_m2"),
                "confidence":         f["properties"].get("confidence"),
                "confidence_median":  f["properties"].get("confidence_median"),
                "relationship":       f["properties"].get("parcel_relationship"),
                "overlap_ratio":      f["properties"].get("overlap_ratio"),
                "source_tile":        f["properties"].get("source_tile"),
                "model":              f["properties"].get("model"),
                "model_version":      f["properties"].get("model_version"),
                "was_watershed_split":f["properties"].get("was_watershed_split"),
            }
            for f in buildings
        ],
        "discrepancies":          discs,
        "parcel_area_m2":         parcel_area_m2,
        "coverage_ratio":         coverage_ratio,
        "_source":                "AI_DERIVED_UAVPAL",
        "_disclaimer":            _AI_DISCLAIMER,
    }


# ── Parcel list ────────────────────────────────────────────────────────────────

@router.get("", summary="List parcels")
async def list_parcels(city: Optional[str] = None, current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Returns the synthetic demo parcel FeatureCollection for Bhopal.
    Non-Bhopal cities: empty collection with coverage note.
    """
    if city and city.lower() != "bhopal":
        return JSONResponse(
            content={
                "type":           "FeatureCollection",
                "total":          0,
                "features":       [],
                "_source":        "SYNTHETIC_DEMO",
                "_coverage_note": (
                    f"No parcel data available for {city.title()}. "
                    "DrishtiGIS currently has prototype data for Bhopal only."
                ),
                "_disclaimer": _SYNTHETIC_DISCLAIMER,
            },
            headers=_SYNTHETIC_HEADER,
        )

    features = _load_synthetic_parcels()
    return JSONResponse(
        content={
            "type":        "FeatureCollection",
            "total":       len(features),
            "features":    features,
            "_source":     "SYNTHETIC_DEMO",
            "_disclaimer": _SYNTHETIC_DISCLAIMER,
        },
        headers=_SYNTHETIC_HEADER,
    )


# ── Parcel detail ──────────────────────────────────────────────────────────────

@router.get("/{property_id}", summary="Get parcel with AI analysis")
async def get_parcel(property_id: str, current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Returns a parcel with AI building analysis.

    Lookup order:
      1. Synthetic parcels (DRS-BPL-DEMO-XXX) — primary
      2. Legacy demo parcels (DRS-BPL-001XX)  — backward compat for existing tests
    """
    # 1. Try synthetic dataset
    syn_features = _load_synthetic_parcels()
    syn_props    = _load_synthetic_props()

    feature = next(
        (f for f in syn_features if f["properties"]["property_id"] == property_id),
        None,
    )
    is_synthetic = feature is not None

    if is_synthetic:
        parcel_id = feature["properties"]["id"]
        property_record = next(
            (p for p in syn_props if p["property_id"] == property_id), None
        )
        source      = "SYNTHETIC_DEMO"
        disclaimer  = _SYNTHETIC_DISCLAIMER
        resp_header = _SYNTHETIC_HEADER

    else:
        # 2. Fallback to legacy 3-parcel demo
        leg_features = _load_legacy_parcels()
        leg_props    = _load_legacy_props()
        feature      = next(
            (f for f in leg_features if f["properties"]["property_id"] == property_id),
            None,
        )
        if not feature:
            raise HTTPException(
                status_code=404,
                detail=f"Parcel '{property_id}' not found in prototype or synthetic dataset.",
            )
        parcel_id = feature["properties"]["id"]
        property_record = next(
            (p for p in leg_props if p["parcel_id"] == parcel_id), None
        )
        source      = "DEMO_DATA_PROTOTYPE_ONLY"
        disclaimer  = _LEGACY_DISCLAIMER
        resp_header = _LEGACY_HEADER

    parcel_area = feature["properties"].get("area_m2", 0)
    ai_analysis = _build_ai_analysis(parcel_id, parcel_area)

    all_buildings = _load_ai_features()
    ai_features   = [
        f for f in all_buildings
        if f["properties"].get("primary_parcel_id") == parcel_id
    ]

    return JSONResponse(
        content={
            "parcel":        feature,
            "property":      property_record,
            "ai_analysis":   ai_analysis,
            "ai_features":   ai_features,
            "discrepancies": ai_analysis["discrepancies"],
            "_source":       source,
            "_ai_source":    "AI_DERIVED_UAVPAL",
            "_disclaimer":   disclaimer,
        },
        headers=resp_header,
    )
