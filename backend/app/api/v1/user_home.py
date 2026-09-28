"""
DrishtiGIS — Private User HOME Location API Router
===================================================
Provides user-scoped API endpoints for viewing, saving, updating, and deleting
private HOME map markers.

STRICT PRIVACY GUARANTEES:
- Scoped strictly to authenticated current_user.user_id.
- Cannot view, manipulate, or discover another user's HOME location.
- Never logs raw lat/lon coordinates to audit logs or system outputs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.user_model import User
from backend.app.auth.dependencies import get_current_user
from backend.app.services.user_home_store import user_home_store, UserHomeLocation
from backend.app.auth.audit_logger import security_audit_logger

router = APIRouter()

class UserHomeRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in EPSG:4326 WGS84 coordinates")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in EPSG:4326 WGS84 coordinates")
    address_label: Optional[str] = Field("HOME", max_length=100, description="Label text")
    accuracy_m: Optional[float] = Field(None, ge=0.0, description="GPS device accuracy radius in meters")

@router.get("/home", summary="Get Current Authenticated User's HOME Location")
async def get_user_home(current_user: User = Depends(get_current_user)):
    """Fetch saved HOME location for current authenticated account."""
    home = user_home_store.get_home(current_user.user_id)
    if not home:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No private HOME location has been saved for this account."
        )
    return home

@router.post("/home", summary="Save or Update Current Authenticated User's HOME Location")
@router.put("/home", summary="Update Current Authenticated User's HOME Location")
async def set_user_home(
    req: UserHomeRequest,
    current_user: User = Depends(get_current_user)
):
    """Save or update private HOME location for current authenticated account."""
    home = user_home_store.save_home(
        user_id=current_user.user_id,
        latitude=req.latitude,
        longitude=req.longitude,
        address_label=req.address_label or "HOME",
        accuracy_m=req.accuracy_m
    )

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="HOME_LOCATION_UPDATED",
        resource_type="user_home",
        resource_id=current_user.user_id,
        region_id=current_user.region_id,
        details={"has_accuracy": req.accuracy_m is not None}  # Privacy: DO NOT log lat/lon coordinates
    )

    return home

@router.delete("/home", summary="Delete Current Authenticated User's HOME Location")
async def delete_user_home(current_user: User = Depends(get_current_user)):
    """Delete saved HOME location for current authenticated account."""
    deleted = user_home_store.delete_home(current_user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved HOME location found to delete."
        )

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="HOME_LOCATION_DELETED",
        resource_type="user_home",
        resource_id=current_user.user_id,
        region_id=current_user.region_id
    )

    return {"message": "Private HOME location deleted successfully."}
