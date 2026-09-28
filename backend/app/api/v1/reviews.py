"""
DrishtiGIS — Surveyor Review & Field Verification API Router
==============================================================
Phase 8: Surveyor Review, Ground-Truthing & Cadastral Geometry Editing

Endpoints:
  GET    /api/v1/reviews
  GET    /api/v1/reviews/stats
  GET    /api/v1/reviews/export
  GET    /api/v1/reviews/{review_id}
  POST   /api/v1/reviews
  PATCH  /api/v1/reviews/{review_id}
  POST   /api/v1/reviews/{review_id}/geometry
  POST   /api/v1/reviews/{review_id}/verify
  GET    /api/v1/reviews/{review_id}/audit
  GET    /api/v1/parcels/{parcel_id}/review-history

DISCLAIMER: All review decisions represent surveyor/reviewer workflow states.
They do NOT constitute legal determinations of land title or property ownership.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.models.review import (
    ReviewItem,
    ReviewStatus,
    ReviewIssueType,
    ReviewSeverity,
    VerificationMethod,
    ReviewAuditTrail,
    FieldVerificationRecord,
    ReviewStats,
)
from backend.app.services.review_store import review_store

from backend.app.auth.user_model import User, UserRole
from backend.app.auth.roles import Permission, has_permission
from backend.app.auth.dependencies import get_optional_user, get_current_user, require_permission

router = APIRouter()


class StatusUpdateRequest(BaseModel):
    status: ReviewStatus
    reviewer: str = "Surveyor"
    notes: Optional[str] = None


class GeometryEditRequest(BaseModel):
    geometry: Dict[str, Any]
    reviewer: str = "Surveyor"
    notes: Optional[str] = None


class FieldVerificationRequest(BaseModel):
    verification_method: VerificationMethod
    observed_feature: str
    observation: str
    reviewer: str = "Surveyor"
    notes: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    evidence_reference: Optional[Dict[str, Any]] = None
    photo_filename: Optional[str] = None


@router.get("", summary="List review items with filters")
async def list_reviews(
    status: Optional[ReviewStatus] = None,
    issue_type: Optional[ReviewIssueType] = None,
    severity: Optional[ReviewSeverity] = None,
    region_id: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    dataset_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Lists review queue items matching specified spatial and status filters."""
    items = review_store.list_reviews(
        status=status,
        issue_type=issue_type,
        severity=severity,
        region_id=region_id,
        city=city,
        state=state,
        dataset_id=dataset_id,
        entity_type=entity_type,
        assigned_to=assigned_to,
    )

    return JSONResponse(content={
        "total": len(items),
        "items": [item.dict() for item in items],
        "_disclaimer": "Synthetic prototype parcel records — review workflow demo only.",
    })


@router.get("/stats", summary="Get review queue statistics")
async def get_review_stats(user: User = Depends(get_optional_user)) -> JSONResponse:
    """Returns workflow statistics for review items."""
    stats = review_store.get_stats()
    return JSONResponse(content=stats.dict())


@router.get("/export", summary="Export reviewed GIS geometry as GeoJSON")
async def export_reviewed_gis(city: Optional[str] = None, user: User = Depends(get_optional_user)) -> JSONResponse:
    """Exports reviewed features as GeoJSON with disclaimers and CRS metadata."""
    geojson_data = review_store.export_reviewed_geojson(city=city)
    return JSONResponse(content=geojson_data)


@router.get("/{review_id}", summary="Get review item by ID")
async def get_review(review_id: str, user: User = Depends(get_optional_user)) -> JSONResponse:
    """Returns single review item details, audit trail, and field verifications."""
    item = review_store.get_review(review_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item '{review_id}' not found."
        )

    audits = review_store.get_audit_trail(review_id)
    verifications = review_store.get_verifications(review_id)

    return JSONResponse(content={
        "item": item.dict(),
        "audit_trail": [a.dict() for a in audits],
        "field_verifications": [v.dict() for v in verifications],
        "_disclaimer": "Geometric observation review only — not official land title.",
    })


def check_mutation_permission(user: User, perm: Permission) -> bool:
    return has_permission(user.role, perm)


@router.post("", summary="Create a new review item")
async def create_review(
    item: ReviewItem, 
    reviewer: str = "System",
    user: User = Depends(get_optional_user)
) -> JSONResponse:
    """Creates a new review item."""
    if not check_mutation_permission(user, Permission.CREATE_REVIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role lacks CREATE_REVIEW permission."
        )

    created = review_store.create_review(item, reviewer=user.name or reviewer)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"item": created.dict()}
    )


@router.patch("/{review_id}", summary="Update review item status")
async def update_review_status(
    review_id: str, 
    req: StatusUpdateRequest,
    user: User = Depends(get_optional_user)
) -> JSONResponse:
    """Updates review status and appends an immutable audit log entry."""
    if req.status in [ReviewStatus.ACCEPTED, ReviewStatus.REJECTED]:
        if not check_mutation_permission(user, Permission.APPROVE_REVIEW):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role lacks APPROVE_REVIEW / REJECT_REVIEW permission."
            )
    else:
        if not check_mutation_permission(user, Permission.CREATE_REVIEW):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role lacks permission to update review status."
            )

    try:
        updated = review_store.update_review_status(
            review_id=review_id,
            new_status=req.status,
            reviewer=user.name or req.reviewer,
            notes=req.notes
        )
        return JSONResponse(content={"item": updated.dict()})
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{review_id}/geometry", summary="Submit geometry edit for review item")
async def update_review_geometry(
    review_id: str, 
    req: GeometryEditRequest,
    user: User = Depends(get_optional_user)
) -> JSONResponse:
    """
    Submits edited geometry. Runs topology validation and recomputes spatial relationships.
    Preserves original AI geometry intact; stores edited geometry as REVIEWED_AI_GEOMETRY.
    """
    if not check_mutation_permission(user, Permission.EDIT_REVIEW_GEOMETRY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role lacks EDIT_REVIEW_GEOMETRY permission."
        )

    try:
        updated_item, recomp_results = review_store.update_review_geometry(
            review_id=review_id,
            new_geometry=req.geometry,
            reviewer=user.name or req.reviewer,
            notes=req.notes
        )
        return JSONResponse(content={
            "item": updated_item.dict(),
            "recomputed_spatial_relationships": recomp_results,
            "message": "Geometry updated and validated successfully."
        })
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/{review_id}/verify", summary="Record field verification observation")
async def record_field_verification(
    review_id: str, 
    req: FieldVerificationRequest,
    user: User = Depends(get_optional_user)
) -> JSONResponse:
    """Records a ground-truthing field verification observation."""
    if not check_mutation_permission(user, Permission.SUBMIT_FIELD_VERIFICATION):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role lacks SUBMIT_FIELD_VERIFICATION permission."
        )

    import uuid
    from datetime import datetime, timezone

    record = FieldVerificationRecord(
        verification_id=f"VERIF-{uuid.uuid4().hex[:8]}",
        review_id=review_id,
        location=req.location,
        verification_method=req.verification_method,
        observed_feature=req.observed_feature,
        observation=req.observation,
        timestamp=datetime.now(timezone.utc).isoformat(),
        reviewer=user.name or req.reviewer,
        notes=req.notes,
        evidence_reference=req.evidence_reference,
        photo_filename=req.photo_filename,
    )

    try:
        saved_record = review_store.add_field_verification(review_id, record)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"verification": saved_record.dict(), "status": "FIELD_VERIFICATION_REQUIRED"}
        )
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))



@router.get("/{review_id}/audit", summary="Get audit trail for a review item")
async def get_review_audit_trail(review_id: str) -> JSONResponse:
    """Returns complete immutable audit log history for a review item."""
    audits = review_store.get_audit_trail(review_id)
    return JSONResponse(content={
        "review_id": review_id,
        "total": len(audits),
        "audit_trail": [a.dict() for a in audits]
    })


@router.get("/parcels/{parcel_id}/review-history", summary="Get parcel review history")
async def get_parcel_review_history(parcel_id: str) -> JSONResponse:
    """Returns review history for a parcel."""
    history = review_store.get_parcel_review_history(parcel_id)
    return JSONResponse(content={
        "parcel_id": parcel_id,
        "total": len(history),
        "reviews": [item.dict() for item in history]
    })
