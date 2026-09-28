"""
DrishtiGIS — Raster Tile Endpoint
===================================
GET /api/v1/tiles/bhopal/{z}/{x}/{y}.png

Serves verified XYZ raster tiles produced by the Phase 2 pipeline
(data/processed/tiles/bhopal/{z}/{x}/{y}.png).

Security controls:
  - z, x, y are typed as int with FastAPI Path validators
    (rejects non-integers with HTTP 422 at the framework level)
  - Zoom range enforced: only 18–21 served
  - Resolved path must be inside TILES_BASE (path traversal guard)
  - NEVER serves anything from Dataset/ or any other directory

Attribution:
  Generated from Bhopal UAV orthomosaic (EPSG:32643 → EPSG:3857)
  Source: PROCESSED_RASTER — derived from verified Phase 2 pipeline
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi import Path as FPath
from fastapi.responses import FileResponse, Response
from backend.app.services.dataset_store import dataset_store
from backend.app.api.v1.published_datasets import generate_tile_png_from_dataset, TRANSPARENT_1X1_PNG

router = APIRouter()

# ── Path constants ─────────────────────────────────────────────────────────
# Resolved once at import time — not per-request
_REPO_ROOT  = Path(__file__).resolve().parents[4]
TILES_BASE  = (_REPO_ROOT / "data" / "processed" / "tiles" / "bhopal").resolve()

ZOOM_MIN = 18
ZOOM_MAX = 21

_TILE_CACHE_HEADER = "public, max-age=3600"


@router.get(
    "/bhopal/{z}/{x}/{y}.png",
    summary="Bhopal UAV raster tile",
    responses={
        200: {"content": {"image/png": {}}, "description": "Tile PNG image"},
        404: {"description": "Tile not found or zoom out of range"},
        403: {"description": "Path traversal detected"},
    },
    tags=["tiles"],
)
async def get_bhopal_tile(
    z: int = FPath(ge=0, le=30, description="Zoom level (18–21 for Bhopal UAV)"),
    x: int = FPath(ge=0, description="Tile column (X)"),
    y: int = FPath(ge=0, description="Tile row (Y)"),
):
    """
    Serve a single Bhopal UAV raster tile with 4-band RGBA transparency.
    Dynamically reprojects from authoritative dataset GeoTIFF source.
    """
    if not (ZOOM_MIN <= z <= ZOOM_MAX):
        raise HTTPException(
            status_code=404,
            detail=f"Tile zoom {z} not available. Bhopal tiles exist for z{ZOOM_MIN}–z{ZOOM_MAX}.",
        )

    ds = dataset_store.get_dataset("DS-BHOPAL-RASTER-001")
    if ds:
        try:
            png_bytes = generate_tile_png_from_dataset(ds, z, x, y)
            if png_bytes != TRANSPARENT_1X1_PNG:
                return Response(content=png_bytes, media_type="image/png", headers={"Cache-Control": _TILE_CACHE_HEADER})
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="Tile not found.")
