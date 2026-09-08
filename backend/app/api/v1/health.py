"""
DrishtiGIS — Health Check Endpoint
=====================================
GET /health  →  {"status": "ok", "version": "0.1.0", "database": "..."}
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("", summary="Health check")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {type(exc).__name__}"

    return {
        "status": "ok",
        "version": settings.VERSION,
        "app": settings.APP_NAME,
        "database": db_status,
    }
