"""
DrishtiGIS — Private User Property API Router
================================================
Provides user-scoped API endpoints for viewing, registering, editing, and deleting
user property locations and details.

PRIVACY & SECURITY GUARANTEES:
- Scoped strictly to authenticated current_user.user_id.
- Account A cannot view, edit, or delete Account B's private properties.
- Public endpoint returns only user-opted-in public markers with strict field redaction.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.user_model import User
from backend.app.auth.dependencies import get_current_user
from backend.app.services.user_property_store import user_property_store, UserProperty
from backend.app.auth.audit_logger import security_audit_logger

router = APIRouter()

class CreatePropertyRequest(BaseModel):
    title: str = Field(..., max_length=150)
    house_number: Optional[str] = Field("", max_length=50)
    street_locality: Optional[str] = Field("", max_length=200)
    city: Optional[str] = Field("Bhopal", max_length=100)
    state: Optional[str] = Field("Madhya Pradesh", max_length=100)
    pincode: Optional[str] = Field("", max_length=20)
    property_type: str = Field("house", description="house, building, vacant_plot, other")
    description: Optional[str] = Field("", max_length=500)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy_m: Optional[float] = Field(None, ge=0.0)
    is_user_adjusted: bool = False
    is_public: bool = False
    show_name_publicly: bool = False
    show_address_publicly: bool = False
    show_phone_publicly: bool = False
    phone_number: Optional[str] = Field("", max_length=30)

class UpdatePropertyRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    house_number: Optional[str] = Field(None, max_length=50)
    street_locality: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    property_type: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    accuracy_m: Optional[float] = Field(None, ge=0.0)
    is_user_adjusted: Optional[bool] = None
    is_public: Optional[bool] = None
    show_name_publicly: Optional[bool] = None
    show_address_publicly: Optional[bool] = None
    show_phone_publicly: Optional[bool] = None
    phone_number: Optional[str] = Field(None, max_length=30)

@router.get("/properties", summary="Get Current Authenticated User's Properties")
async def get_my_properties(current_user: User = Depends(get_current_user)):
    """Fetch all registered properties owned by current authenticated user."""
    return user_property_store.get_user_properties(current_user.user_id)

@router.post("/properties", summary="Register New User Property")
async def create_user_property(
    req: CreatePropertyRequest,
    current_user: User = Depends(get_current_user)
):
    """Register a new user property with GPS or manual map location."""
    prop = UserProperty(
        user_id=current_user.user_id,
        owner_name=current_user.name,
        title=req.title,
        house_number=req.house_number or "",
        street_locality=req.street_locality or "",
        city=req.city or "Bhopal",
        state=req.state or "Madhya Pradesh",
        pincode=req.pincode or "",
        property_type=req.property_type,
        description=req.description or "",
        latitude=round(req.latitude, 6),
        longitude=round(req.longitude, 6),
        accuracy_m=round(req.accuracy_m, 2) if req.accuracy_m is not None else None,
        is_user_adjusted=req.is_user_adjusted,
        is_public=req.is_public,
        show_name_publicly=req.show_name_publicly,
        show_address_publicly=req.show_address_publicly,
        show_phone_publicly=req.show_phone_publicly,
        phone_number=req.phone_number or ""
    )

    saved = user_property_store.create_property(prop)

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="USER_PROPERTY_CREATED",
        resource_type="user_property",
        resource_id=saved.id,
        region_id=current_user.region_id
    )

    return saved

@router.put("/properties/{property_id}", summary="Update User Property")
async def update_user_property(
    property_id: str,
    req: UpdatePropertyRequest,
    current_user: User = Depends(get_current_user)
):
    """Update details or location of a property owned by current authenticated user."""
    update_data = req.model_dump(exclude_unset=True)
    updated = user_property_store.update_property(property_id, current_user.user_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or you do not have permission to modify it."
        )

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="USER_PROPERTY_UPDATED",
        resource_type="user_property",
        resource_id=property_id,
        region_id=current_user.region_id
    )

    return updated

@router.delete("/properties/{property_id}", summary="Delete User Property")
async def delete_user_property(
    property_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a property owned by current authenticated user."""
    deleted = user_property_store.delete_property(property_id, current_user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or you do not have permission to delete it."
        )

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="USER_PROPERTY_DELETED",
        resource_type="user_property",
        resource_id=property_id,
        region_id=current_user.region_id
    )

    return {"message": "User property deleted successfully."}

@router.get("/properties/public", summary="Get Public User Property Markers")
async def get_public_properties():
    """Fetch public user property markers for map view with strict field redactions."""
    return user_property_store.get_public_properties()
