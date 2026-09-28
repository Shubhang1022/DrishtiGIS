"""
DrishtiGIS — Administrative API Router & Authoritative Dataset Engine
=============================================================================
Enforces strict ADMIN authorization for governance, user management, region management,
dataset ingestion, background pipeline execution, inventory search, and analytics.

SECURITY REQUIREMENTS:
- Strict ADMIN role authorization on all routes via require_admin dependency.
- Authoritative MAX_UPLOAD_SIZE_MB streaming enforcement (HTTP 413 on exceed).
- Path traversal sanitization, extension validation, zip bomb extraction safeguards.
"""

import os
import json
import shutil
import zipfile
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, Query, BackgroundTasks, status

from backend.app.core.config import settings
from backend.app.auth.user_model import User, UserResponse, UserUpdate, UserRole
from backend.app.auth.dependencies import require_admin
from backend.app.auth.user_store import user_store
from backend.app.auth.audit_logger import security_audit_logger

from backend.app.services.dataset_store import dataset_store, DatasetItem, UPLOADS_DIR
from backend.app.services.dataset_pipeline import run_dataset_pipeline
from backend.app.services.user_property_store import user_property_store

router = APIRouter()

ALLOWED_EXTENSIONS = {".tiff", ".tif", ".geojson", ".gpkg", ".zip"}
MAX_UNCOMPRESSED_ZIP_SIZE = 250 * 1024 * 1024  # 250 MB
MAX_ZIP_FILE_COUNT = 50

ROOT = Path(__file__).resolve().parents[4]
SYNTHETIC_PROPS_FILE = ROOT / "data" / "synthetic" / "bhopal-synthetic-properties.json"

# ── Admin Users Management ────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse], summary="List All Registered Users (Admin)")
async def admin_list_users(admin_user: User = Depends(require_admin)):
    return user_store.list_users()

@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update User Role / Status (Admin)")
async def admin_update_user(
    user_id: str,
    update_req: UserUpdate,
    admin_user: User = Depends(require_admin)
):
    updated = user_store.update_user(user_id, update_req)
    if not updated:
        raise HTTPException(status_code=404, detail=f"User ID '{user_id}' not found.")

    security_audit_logger.log_event(
        user_id=admin_user.user_id,
        user_email=admin_user.email,
        role=admin_user.role.value,
        action="ADMIN_USER_UPDATED",
        resource_type="user",
        resource_id=user_id,
        details=update_req.model_dump(exclude_unset=True)
    )
    return UserResponse(
        user_id=updated.user_id,
        email=updated.email,
        name=updated.name,
        role=updated.role,
        organization=updated.organization,
        country=updated.country,
        state=updated.state,
        city=updated.city,
        region_id=updated.region_id,
        allowed_datasets=updated.allowed_datasets,
        is_active=updated.is_active,
        created_at=updated.created_at,
        last_login=updated.last_login
    )

# ── Admin Regions Management ──────────────────────────────────────────────────

@router.get("/regions", summary="List All Governance Regions (Admin)")
async def admin_list_regions(admin_user: User = Depends(require_admin)):
    return {"regions": user_store.regions}

@router.post("/regions", summary="Register Governance Region (Admin)")
async def admin_create_region(
    region_data: Dict[str, Any],
    admin_user: User = Depends(require_admin)
):
    res = user_store.add_region(region_data)
    security_audit_logger.log_event(
        user_id=admin_user.user_id,
        user_email=admin_user.email,
        role=admin_user.role.value,
        action="ADMIN_REGION_REGISTERED",
        resource_type="region",
        resource_id=region_data.get("region_id"),
        details=region_data
    )
    return res

# ── Admin Dataset Ingestion & Pipeline Jobs ───────────────────────────────────

@router.post("/datasets/upload", summary="Ingest Geospatial Dataset & Enqueue Pipeline (Admin)")
async def admin_upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(None),
    region_id: Optional[str] = Form("bhopal_mp"),
    state_name: Optional[str] = Form("Madhya Pradesh"),
    city_name: Optional[str] = Form("Bhopal"),
    dataset_type: Optional[str] = Form("uav_raster"),
    content_length: Optional[int] = Header(None, alias="Content-Length"),
    admin_user: User = Depends(require_admin)
):
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # 1. Content-Length Header Check
    if content_length and content_length > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # 2. Filename & Extension Sanitization
    safe_filename = os.path.basename(file.filename or "upload.tmp")
    ext = os.path.splitext(safe_filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 3. Dedicated Storage & Streaming Upload Byte Count
    ds_temp_id = f"DS-INGEST-{os.path.splitext(safe_filename)[0].upper().replace(' ', '_')}"
    ds_dir = UPLOADS_DIR / ds_temp_id
    ds_dir.mkdir(parents=True, exist_ok=True)
    target_file_path = ds_dir / safe_filename

    total_bytes = 0
    try:
        with open(target_file_path, "wb") as f_out:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_MB} MB."
                    )
                f_out.write(chunk)

        # 4. ZIP Inspection & Path Traversal Check
        if ext == ".zip":
            try:
                with zipfile.ZipFile(target_file_path, "r") as zf:
                    infolist = zf.infolist()
                    if len(infolist) > MAX_ZIP_FILE_COUNT:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Archive contains too many files ({len(infolist)}). Max allowed: {MAX_ZIP_FILE_COUNT}."
                        )
                    if sum(z.file_size for z in infolist) > MAX_UNCOMPRESSED_ZIP_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Decompressed archive exceeds 250 MB safety threshold."
                        )
                    for z in infolist:
                        normalized = os.path.normpath(z.filename)
                        if normalized.startswith("..") or os.path.isabs(normalized):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Unsafe path traversal in archive."
                            )
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail="Corrupted or invalid ZIP file.")

        # 5. Register Dataset in Store
        ds_item = dataset_store.register_dataset(
            name=dataset_name or safe_filename,
            filename=safe_filename,
            format_type=dataset_type or "uav_raster",
            file_size_bytes=total_bytes,
            file_path=str(target_file_path),
            state=state_name or "Madhya Pradesh",
            city=city_name or "Bhopal",
            region_id=region_id or "bhopal_mp",
            uploaded_by=admin_user.email
        )

        # 6. Enqueue Background Processing Pipeline
        asyncio.create_task(run_dataset_pipeline(ds_item.dataset_id))

        security_audit_logger.log_event(
            user_id=admin_user.user_id,
            user_email=admin_user.email,
            role=admin_user.role.value,
            action="DATASET_UPLOADED",
            resource_type="dataset",
            resource_id=ds_item.dataset_id,
            region_id=region_id,
            details={"filename": safe_filename, "size_bytes": total_bytes}
        )

        return {
            "status": "SUCCESS",
            "message": "Upload successful — dataset registered. Processing has been queued in background.",
            "dataset_id": ds_item.dataset_id,
            "job_id": ds_item.job_id,
            "filename": safe_filename,
            "size_bytes": total_bytes,
            "max_allowed_mb": settings.MAX_UPLOAD_SIZE_MB,
            "region_id": ds_item.region_id,
            "dataset": ds_item.model_dump()
        }

    except Exception as e:
        if os.path.exists(ds_dir):
            shutil.rmtree(ds_dir, ignore_errors=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Upload processing error: {str(e)}")

@router.get("/datasets", summary="List All Ingested Geospatial Datasets (Admin)")
async def admin_list_datasets(
    status: Optional[str] = Query("ALL"),
    region_id: Optional[str] = Query("ALL"),
    format_type: Optional[str] = Query("ALL"),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("uploaded_at"),
    ascending: Optional[bool] = Query(False),
    admin_user: User = Depends(require_admin)
):
    items = dataset_store.list_datasets(
        status=status,
        region_id=region_id,
        format_type=format_type,
        search=search,
        sort_by=sort_by or "uploaded_at",
        ascending=bool(ascending) if isinstance(ascending, bool) else False
    )
    return {
        "total": len(items),
        "datasets": [d.model_dump() for d in items]
    }

@router.get("/datasets/{dataset_id}", summary="Get Dataset Details & Processing Status (Admin)")
async def admin_get_dataset_detail(
    dataset_id: str,
    admin_user: User = Depends(require_admin)
):
    ds = dataset_store.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset ID '{dataset_id}' not found.")
    return ds.model_dump()

@router.post("/datasets/{dataset_id}/retry", summary="Retry Failed Dataset Processing Job (Admin)")
async def admin_retry_dataset_job(
    dataset_id: str,
    admin_user: User = Depends(require_admin)
):
    try:
        ds_updated = dataset_store.retry_dataset(dataset_id)
        asyncio.create_task(run_dataset_pipeline(dataset_id))

        security_audit_logger.log_event(
            user_id=admin_user.user_id,
            user_email=admin_user.email,
            role=admin_user.role.value,
            action="DATASET_RETRY_INITIATED",
            resource_type="dataset",
            resource_id=dataset_id
        )
        return {"message": "Dataset pipeline retry enqueued successfully.", "dataset": ds_updated.model_dump()}
    except ValueError as val_err:
        err_msg = str(val_err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)

@router.post("/datasets/{dataset_id}/cancel", summary="Cancel Queued or In-Progress Dataset Job (Admin)")
async def admin_cancel_dataset_job(
    dataset_id: str,
    admin_user: User = Depends(require_admin)
):
    try:
        ds_updated = dataset_store.cancel_dataset(dataset_id)
        security_audit_logger.log_event(
            user_id=admin_user.user_id,
            user_email=admin_user.email,
            role=admin_user.role.value,
            action="DATASET_CANCELLED",
            resource_type="dataset",
            resource_id=dataset_id
        )
        return {"message": "Dataset job cancelled.", "dataset": ds_updated.model_dump()}
    except ValueError as val_err:
        err_msg = str(val_err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)

@router.post("/datasets/{dataset_id}/publish", summary="Approve & Publish Dataset to WebGIS (Admin)")
async def admin_publish_dataset(
    dataset_id: str,
    admin_user: User = Depends(require_admin)
):
    try:
        ds = dataset_store.publish_dataset(dataset_id)
        security_audit_logger.log_event(
            user_id=admin_user.user_id,
            user_email=admin_user.email,
            role=admin_user.role.value,
            action="DATASET_PUBLISHED",
            resource_type="dataset",
            resource_id=dataset_id
        )
        return {"message": "Dataset published successfully to public WebGIS endpoints.", "dataset": ds.model_dump()}
    except ValueError as val_err:
        err_msg = str(val_err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)

# ── Admin Operations & GIS Analytics Dashboard ────────────────────────────────

@router.get("/analytics/summary", summary="Get Operational GIS Analytics Summary (Admin)")
async def admin_get_analytics_summary(admin_user: User = Depends(require_admin)):
    return dataset_store.get_analytics_summary()

# ── Admin Property & Cadastral Intelligence Table ─────────────────────────────

@router.get("/properties", summary="List Property & Cadastral Intelligence (Admin)")
async def admin_get_properties_table(
    search: Optional[str] = Query(None),
    property_type: Optional[str] = Query("ALL"),
    region_id: Optional[str] = Query("ALL"),
    admin_user: User = Depends(require_admin)
):
    """
    Returns aggregated property & parcel intelligence records from synthetic demo dataset
    and registered user property markers with strict privacy compliance.
    """
    records = []

    # 1. Load Synthetic Demo Parcels
    if SYNTHETIC_PROPS_FILE.exists():
        try:
            with open(SYNTHETIC_PROPS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("properties", []):
                    records.append({
                        "property_id": item.get("property_id"),
                        "plot_number": item.get("plot_number") or item.get("property_id"),
                        "survey_number": item.get("survey_number") or "SUR-BPL-2024",
                        "property_type": item.get("land_use", "residential").lower(),
                        "region_id": "bhopal_mp",
                        "city": "Bhopal",
                        "state": "Madhya Pradesh",
                        "parcel_area_m2": item.get("built_up_area_sqft", 1500) * 0.092903,
                        "owner_name": item.get("owner_name", "Synthetic Demo Owner"),
                        "previous_owner_name": item.get("previous_owner", "N/A"),
                        "resident_count": item.get("resident_count", 4),
                        "purchase_price_inr": item.get("property_tax_inr", 5000) * 50,
                        "estimated_selling_price_inr": item.get("property_tax_inr", 5000) * 65,
                        "ai_building_count": 1,
                        "ai_detected_area_m2": item.get("built_up_area_sqft", 1500) * 0.092903 * 0.95,
                        "coverage_ratio": 0.85,
                        "discrepancy_count": 0,
                        "review_status": "APPROVED",
                        "data_source": "SYNTHETIC_DEMO",
                        "disclaimer": "Synthetic prototype data — not an official legal land record."
                    })
        except Exception as e:
            print(f"Warning: Failed to load synthetic properties: {e}")

    # 2. Add Registered User Properties
    all_user_props = user_property_store.list_all_admin()
    for up in all_user_props:
        records.append({
            "property_id": up.id,
            "plot_number": up.house_number or "H.No. N/A",
            "survey_number": "USER-REG-MARKER",
            "property_type": up.property_type,
            "region_id": "bhopal_mp",
            "city": up.city or "Bhopal",
            "state": up.state or "Madhya Pradesh",
            "parcel_area_m2": 120.0,
            "owner_name": up.owner_name if up.show_name_publicly else "[PRIVATE — Opt-in OFF]",
            "previous_owner_name": "N/A",
            "resident_count": None if up.property_type == "vacant_plot" else 3,
            "purchase_price_inr": None,
            "estimated_selling_price_inr": None,
            "ai_building_count": 1,
            "ai_detected_area_m2": 110.0,
            "coverage_ratio": 0.91,
            "discrepancy_count": 0,
            "review_status": "USER_SUBMITTED",
            "data_source": "USER_REGISTERED",
            "disclaimer": "User-submitted marker — not an official cadastral title record."
        })

    # Filtering
    if property_type and property_type.upper() != "ALL":
        records = [r for r in records if r["property_type"].lower() == property_type.lower()]
    if search:
        q = search.lower().strip()
        records = [
            r for r in records
            if q in r["property_id"].lower() or q in r["plot_number"].lower() or q in str(r["owner_name"]).lower()
        ]

    return {
        "total": len(records),
        "properties": records
    }
