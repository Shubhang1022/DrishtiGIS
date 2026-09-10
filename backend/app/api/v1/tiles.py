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
from fastapi.responses import FileResponse

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
    response_class=FileResponse,
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
) -> FileResponse:
    """
    Serve a single Bhopal UAV raster tile.

    Tiles are pre-generated PNG files from the Phase 2 raster pipeline.
    Only zoom levels 18–21 are available. Requests outside this range
    or for non-existent tiles return 404.

    The raw TIFF source files and COG are never exposed through this endpoint.
    """
    # Zoom range check
    if not (ZOOM_MIN <= z <= ZOOM_MAX):
        raise HTTPException(
            status_code=404,
            detail=f"Tile zoom {z} not available. Bhopal tiles exist for z{ZOOM_MIN}–z{ZOOM_MAX}.",
        )

    # Construct candidate path using only validated integers
    candidate = TILES_BASE / str(z) / str(x) / f"{y}.png"

    # Path traversal guard — resolve and confirm the path stays inside TILES_BASE
    try:
        resolved = candidate.resolve()
    except (OSError, ValueError):
        raise HTTPException(status_code=403, detail="Invalid tile path.")

    if not str(resolved).startswith(str(TILES_BASE)):
        raise HTTPException(status_code=403, detail="Path traversal detected.")

    # Tile existence check
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Tile not found.")

    return FileResponse(
        path=str(resolved),
        media_type="image/png",
        headers={"Cache-Control": _TILE_CACHE_HEADER},
    )
