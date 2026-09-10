"""
DrishtiGIS — OSM Thematic Layer Endpoints
==========================================
GET /api/v1/osm/bhopal/{layer}

Serves pre-extracted Bhopal OSM GeoJSON files produced by Phase 3
(data/osm/bhopal-extract/bhopal-{layer}.geojson).

Available layers: buildings, roads, waterways, landuse

Security controls:
  - Strict allowlist: only the 4 known layer names are served
  - No dynamic file path construction from user input beyond the allowlist
  - Internal files (_bbox_nodes.json, extraction_report.json) return 404
  - The 1.7 GB India PBF is NEVER accessed or served through any endpoint

Attribution (REQ-OSM-03):
  Every response carries:
    Header: X-OSM-Attribution: © OpenStreetMap contributors, ODbL
    Body field: _source: OSM_OPENSTREETMAP (embedded in the GeoJSON file)

Performance note:
  FileResponse uses OS-level sendfile — does NOT load the 27 MB buildings
  file into Python process memory. Safe for large responses.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

# ── Path constants ─────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[4]
OSM_BASE   = (_REPO_ROOT / "data" / "osm" / "bhopal-extract").resolve()

# Strict allowlist — ONLY these four layer names may be served
ALLOWED_LAYERS: frozenset[str] = frozenset(["buildings", "roads", "waterways", "landuse"])

_OSM_HEADERS = {
    "X-OSM-Attribution": "(c) OpenStreetMap contributors, ODbL",
    "X-Data-Source":     "OSM_OPENSTREETMAP",
    "Cache-Control":     "public, max-age=1800",  # 30 min — stable extracted data
}


@router.get(
    "/bhopal/{layer}",
    summary="Bhopal OSM thematic layer (GeoJSON)",
    response_class=FileResponse,
    responses={
        200: {"content": {"application/geo+json": {}}, "description": "GeoJSON FeatureCollection"},
        404: {"description": "Layer not available"},
    },
    tags=["osm"],
)
async def get_bhopal_osm_layer(layer: str) -> FileResponse:
    """
    Return a pre-extracted Bhopal OSM thematic layer as GeoJSON.

    Available layers: buildings (26,577 features), roads (2,933),
    waterways (31), landuse (98).

    Data source: OpenStreetMap (ODbL license).
    Extraction bbox: W=77.38° S=23.24° E=77.44° N=23.27°.

    The 1.7 GB India PBF is never accessed at runtime — all GeoJSON was
    pre-extracted in Phase 3 and stored on disk.

    OSM data is supplementary geographic context only.
    It is NOT authoritative cadastral data.
    """
    # Strict allowlist check — must precede any file path construction
    if layer not in ALLOWED_LAYERS:
        raise HTTPException(
            status_code=404,
            detail=f"Layer '{layer}' is not available. Valid layers: {sorted(ALLOWED_LAYERS)}.",
        )

    file_path = OSM_BASE / f"bhopal-{layer}.geojson"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Layer '{layer}' data file not found on disk. "
                "Run the Phase 3 extraction script: scripts/data_prep/06_extract_osm_bhopal.py"
            ),
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/geo+json",
        headers=_OSM_HEADERS,
    )
