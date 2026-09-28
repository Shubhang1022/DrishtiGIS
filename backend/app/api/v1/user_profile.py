"""
DrishtiGIS — Private User Profile API Router
==============================================
Provides user-scoped endpoints to view and edit personal profile details.

PRIVACY REQUIREMENTS:
- Strictly scoped to current_user.user_id.
- User A cannot view, discover, or edit User B's profile.
- Phone number and address fields remain private unless explicit opt-in is configured.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.user_model import User
from backend.app.auth.dependencies import get_current_user
from backend.app.services.user_profile_store import user_profile_store, UserProfileData
from backend.app.auth.audit_logger import security_audit_logger

router = APIRouter()

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=30)
    house_number: Optional[str] = Field(None, max_length=50)
    street_locality: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    organization: Optional[str] = Field(None, max_length=150)
    show_name_publicly: Optional[bool] = Field(None)
    show_address_publicly: Optional[bool] = Field(None)
    show_phone_publicly: Optional[bool] = Field(None)

@router.get("/profile", summary="Get Current Authenticated User's Profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Fetch profile details for current authenticated account."""
    profile = user_profile_store.get_profile(
        user_id=current_user.user_id,
        default_name=current_user.name,
        default_org=current_user.organization or "",
        default_city=current_user.city or "",
        default_state=current_user.state or ""
    )
    return profile

@router.put("/profile", summary="Update Current Authenticated User's Profile")
@router.post("/profile", summary="Save Current Authenticated User's Profile")
async def update_user_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Save or update profile details for current authenticated account."""
    update_data = req.model_dump(exclude_unset=True)
    profile = user_profile_store.save_profile(
        user_id=current_user.user_id,
        update_dict=update_data
    )

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="USER_PROFILE_UPDATED",
        resource_type="user_profile",
        resource_id=current_user.user_id,
        region_id=current_user.region_id,
        details={"updated_fields": list(update_data.keys())}
    )

    return profile
