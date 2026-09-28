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

from app.api.v1 import health, parcels, features, tiles, osm_layers, coverage, locations, historical, roads, landuse, reviews, exports, reports_router, assistant_router, auth_router, user_home, user_profile, user_properties, admin, published_datasets
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
app.include_router(health.router,           prefix="/health",           tags=["health"])
app.include_router(health.router,           prefix="/api/v1/health",    tags=["health"])
app.include_router(auth_router.router,        prefix="/api/v1/auth",      tags=["auth"])
app.include_router(parcels.router,          prefix="/api/v1/parcels",   tags=["parcels"])
app.include_router(features.router,         prefix="/api/v1/features",  tags=["features"])
app.include_router(tiles.router,            prefix="/api/v1/tiles",     tags=["tiles"])
app.include_router(published_datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(osm_layers.router,       prefix="/api/v1/osm",       tags=["osm"])
app.include_router(coverage.router,         prefix="/api/v1/coverage",  tags=["coverage"])
app.include_router(locations.router,        prefix="/api/v1/locations", tags=["locations"])
app.include_router(historical.router,       prefix="/api/v1/historical",tags=["historical"])
app.include_router(roads.router,            prefix="/api/v1/roads",     tags=["roads"])
app.include_router(landuse.router,          prefix="/api/v1/landuse",   tags=["landuse"])
app.include_router(reviews.router,          prefix="/api/v1/reviews",   tags=["reviews"])
app.include_router(exports.router,          prefix="/api/v1/exports",   tags=["exports"])
app.include_router(reports_router.router,   prefix="/api/v1/reports",   tags=["reports"])
app.include_router(assistant_router.router, prefix="/api/v1/assistant", tags=["assistant"])
app.include_router(user_home.router,        prefix="/api/v1/user",      tags=["user"])
app.include_router(user_profile.router,     prefix="/api/v1/user",      tags=["user"])
app.include_router(user_properties.router,  prefix="/api/v1/user",      tags=["user"])
app.include_router(admin.router,            prefix="/api/v1/admin",     tags=["admin"])






@app.on_event("startup")
async def on_startup_recovery():
    """Startup recovery handler to resume interrupted background dataset pipeline jobs."""
    try:
        import asyncio
        import os
        from backend.app.services.dataset_store import dataset_store
        from backend.app.services.dataset_pipeline import run_dataset_pipeline

        interrupted = dataset_store.get_interrupted_datasets()
        for ds in interrupted:
            if ds.file_path and os.path.exists(ds.file_path):
                dataset_store.update_dataset_status(
                    dataset_id=ds.dataset_id,
                    status="REGISTERED",
                    current_stage="Server Restart — Recovering Processing Job",
                    progress_percent=15
                )
                asyncio.create_task(run_dataset_pipeline(ds.dataset_id))
            else:
                dataset_store.update_dataset_status(
                    dataset_id=ds.dataset_id,
                    status="FAILED",
                    current_stage="Source File Missing on Restart",
                    progress_percent=ds.progress_percent,
                    error_details="Server restarted and source file was no longer available on disk."
                )
    except Exception as e:
        print(f"Warning: Dataset startup recovery failed: {e}")

@app.get("/", summary="Root")
async def root():
    """Root endpoint — confirms API is alive."""
    return {
        "message": "DrishtiGIS API",
        "version": settings.VERSION,
        "docs": "/docs",
    }
