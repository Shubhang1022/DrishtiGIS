"""
DrishtiGIS — FastAPI Application
==================================
Entry point for the backend API server.

Run with:
    uvicorn app.main:app --reload

Docs:
    http://localhost:8000/docs    (Swagger UI)
    http://localhost:8000/redoc   (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, parcels, features, tiles, osm_layers, coverage, locations
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered urban geospatial intelligence platform",
    debug=settings.DEBUG,
)

# CORS middleware — allow requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router,       prefix="/health",           tags=["health"])
app.include_router(parcels.router,      prefix="/api/v1/parcels",   tags=["parcels"])
app.include_router(features.router,     prefix="/api/v1/features",  tags=["features"])
app.include_router(tiles.router,        prefix="/api/v1/tiles",     tags=["tiles"])
app.include_router(osm_layers.router,   prefix="/api/v1/osm",       tags=["osm"])
app.include_router(coverage.router,     prefix="/api/v1/coverage",  tags=["coverage"])
app.include_router(locations.router,    prefix="/api/v1/locations", tags=["locations"])


@app.get("/", summary="Root")
async def root():
    """Root endpoint — confirms API is alive."""
    return {
        "message": "DrishtiGIS API",
        "version": settings.VERSION,
        "docs": "/docs",
    }
