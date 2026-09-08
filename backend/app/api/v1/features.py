"""
DrishtiGIS — AI Features API v1
=================================
Placeholder endpoints returning demo AI feature data.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

_DEMO_DIR     = Path(__file__).resolve().parents[4] / "drishtigis" / "lib" / "demo-data"
_DEMO_AI_PATH = _DEMO_DIR / "bhopal-ai-features.geojson"
_DEMO_HEADER  = {"X-Data-Status": "demo-placeholder"}
_DISCLAIMER   = (
    "AI-derived observation — prototype demonstration model only. "
    "Not a legal determination. Requires field verification."
)


@router.get("", summary="List AI features (demo placeholder)")
async def list_features(parcel_id: Optional[str] = None) -> JSONResponse:
    with open(_DEMO_AI_PATH, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    if parcel_id:
        features = [
            feat for feat in features
            if feat["properties"].get("associated_parcel_id") == parcel_id
        ]

    return JSONResponse(
        content={
            "type": "FeatureCollection",
            "total": len(features),
            "features": features,
            "_source": "AI_DERIVED_DEMO",
            "_disclaimer": _DISCLAIMER,
        },
        headers=_DEMO_HEADER,
    )
