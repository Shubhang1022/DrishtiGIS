"""
DrishtiGIS — Health Check Endpoint
=====================================
GET /health and GET /api/v1/health  →  {"status": "ok", "version": "0.1.0", "environment": "..."}
"""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("", summary="System Health Check")
async def health_check() -> dict:
    """Returns safe platform health and status metadata."""
    return {
        "status": "ok",
        "version": settings.VERSION,
        "app": settings.APP_NAME,
        "environment": getattr(settings, "ENVIRONMENT", "production"),
        "geospatial_engine": "active",
        "provenance_tracking": "enabled"
    }

