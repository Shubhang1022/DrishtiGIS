"""
DrishtiGIS — Dynamic Reports & Evidence Packaging API Router
==============================================================
Phase 9: GIS-Ready Outputs, Reports & Evidence Packaging

Endpoints:
  POST /api/v1/reports/parcel/{parcel_id}
  POST /api/v1/reports/review/{review_id}
  GET  /api/v1/reports/region
  POST /api/v1/reports/evidence-package
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse, Response

from backend.app.reports.report_engine import (
    generate_parcel_report,
    generate_surveyor_report,
    generate_area_report,
)
from backend.app.reports.evidence_packager import create_evidence_package

router = APIRouter()


@router.post("/parcel/{parcel_id}", summary="Generate parcel intelligence dossier")
async def get_parcel_report(parcel_id: str) -> JSONResponse:
    """Generates parcel intelligence dossier with live calculated metrics."""
    try:
        report = generate_parcel_report(parcel_id)
        return JSONResponse(content=report)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/review/{review_id}", summary="Generate surveyor review report")
async def get_surveyor_report(review_id: str) -> JSONResponse:
    """Generates surveyor review report with original/reviewed geometry comparison and field observations."""
    try:
        report = generate_surveyor_report(review_id)
        return JSONResponse(content=report)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.get("/region", summary="Generate area intelligence report")
async def get_area_report(city: str = "Bhopal", region_id: str = "REGION-BPL-01") -> JSONResponse:
    """Generates area-level intelligence report with dynamically calculated statistics."""
    report = generate_area_report(city=city, region_id=region_id)
    return JSONResponse(content=report)


@router.post("/evidence-package", summary="Generate Evidence Package ZIP archive")
async def generate_evidence_package(
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01",
    city: str = "Bhopal"
) -> Response:
    """Generates and streams structured Evidence Package ZIP containing metadata, layers, reports, and README."""
    zip_bytes, filename = create_evidence_package(dataset_id=dataset_id, region_id=region_id, city=city)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        }
    )
