"""
DrishtiGIS — GIS Export API Router
====================================
Phase 9: GIS-Ready Outputs, Reports & Evidence Packaging

Endpoints:
  GET  /api/v1/exports/formats
  POST /api/v1/exports
  GET  /api/v1/exports/{export_id}/download
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response, status, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from backend.app.gis.export_engine import build_gis_export, validate_export
from backend.app.auth.user_model import User
from backend.app.auth.dependencies import get_current_user

router = APIRouter()


class ExportRequest(BaseModel):
    dataset_id: str = "DATASET-BHOPAL-UAV"
    region_id: str = "REGION-BPL-01"
    layers: List[str] = Field(default_factory=lambda: ["parcels", "buildings", "roads", "landuse", "discrepancies", "reviews"])
    output_format: str = "GeoJSON"  # GeoJSON | GeoPackage | ZIP
    output_crs: str = "EPSG:4326"    # EPSG:4326 | EPSG:3857 | EPSG:32643
    city: str = "Bhopal"
    state: str = "Madhya Pradesh"
    country: str = "India"


@router.get("/formats", summary="Get supported export formats and layers")
async def get_export_formats(current_user: User = Depends(get_current_user)) -> JSONResponse:
    """Returns supported formats, layers, and coordinate reference systems."""
    return JSONResponse(content={
        "supported_formats": [
            {"id": "GeoJSON", "name": "GeoJSON FeatureCollection", "extension": ".geojson", "status": "Mandatory Support"},
            {"id": "GeoPackage", "name": "OGC GeoPackage", "extension": ".gpkg", "status": "Production Support"},
            {"id": "ZIP", "name": "Multi-Layer GeoJSON ZIP Package", "extension": ".zip", "status": "Production Support"},
        ],
        "supported_layers": [
            {"id": "parcels", "name": "Demonstration Parcels", "source": "SYNTHETIC_DEMO"},
            {"id": "buildings", "name": "AI Building Footprints", "source": "AI_DERIVED_UAVPAL"},
            {"id": "roads", "name": "Road Transport Network", "source": "REFERENCE_GIS"},
            {"id": "landuse", "name": "Observed Land-Use Patterns", "source": "REFERENCE_GIS"},
            {"id": "discrepancies", "name": "Spatial Discrepancies", "source": "AI_DERIVED_UAVPAL"},
            {"id": "reviews", "name": "Reviewed Geometry & Verifications", "source": "REVIEWED_AI_GEOMETRY"},
        ],
        "supported_crss": [
            {"crs": "EPSG:4326", "name": "WGS 84 Geographic", "type": "Geographic"},
            {"crs": "EPSG:32643", "name": "UTM Zone 43N (Bhopal)", "type": "Projected"},
            {"crs": "EPSG:3857", "name": "Web Mercator", "type": "Projected"},
        ],
        "_disclaimer": "Synthetic prototype parcel data — not an official land record.",
    })


@router.post("", summary="Generate GIS export file")
async def generate_export(req: ExportRequest, current_user: User = Depends(get_current_user)) -> Response:
    """Generates GIS export binary file in GeoJSON, GeoPackage, or ZIP format."""
    try:
        file_bytes, filename, metadata = build_gis_export(
            dataset_id=req.dataset_id,
            region_id=req.region_id,
            layers=req.layers,
            output_format=req.output_format,
            output_crs=req.output_crs,
            city=req.city,
            state=req.state,
            country=req.country,
        )

        media_type = "application/json"
        if req.output_format.upper() == "GEOPACKAGE":
            media_type = "application/geopackage+sqlite3"
        elif req.output_format.upper() == "ZIP":
            media_type = "application/zip"

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Export-ID": metadata["export_id"],
                "X-Feature-Count": str(metadata["feature_count"]),
            }
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export validation failed. {str(err)}"
        )
