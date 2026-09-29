"""
DrishtiGIS Authentication & Data Governance API Router.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.auth.user_model import User, UserCreate, UserResponse, UserUpdate, LoginRequest, AuthTokenResponse
from backend.app.auth.roles import Permission, UserRole
from backend.app.auth.auth_service import verify_password, create_access_token
from backend.app.auth.user_store import user_store
from backend.app.auth.dependencies import get_current_user, get_optional_user, require_permission
from backend.app.auth.audit_logger import security_audit_logger

router = APIRouter()

@router.post("/register", response_model=AuthTokenResponse, summary="Register User Account")
async def register(req: UserCreate, response: Response):
    try:
        user = user_store.create_user(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token(user)
    response.set_cookie(
        key="drishtigis_token",
        value=token,
        max_age=604800,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        httponly=True
    )

    security_audit_logger.log_event(
        user_id=user.user_id,
        user_email=user.email,
        role=user.role.value,
        action="REGISTER",
        resource_type="user",
        resource_id=user.user_id,
        region_id=user.region_id
    )

    user_resp = UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        role=user.role,
        organization=user.organization,
        country=user.country,
        state=user.state,
        city=user.city,
        region_id=user.region_id,
        allowed_datasets=user.allowed_datasets,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )

    return AuthTokenResponse(access_token=token, user=user_resp)

@router.post("/login", response_model=AuthTokenResponse, summary="Authenticate User Login")
async def login(req: LoginRequest, response: Response):
    user = user_store.get_by_email(req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your system administrator."
        )

    user.last_login = datetime.now(timezone.utc).isoformat()
    user_store._save_users()

    token = create_access_token(user)
    response.set_cookie(
        key="drishtigis_token",
        value=token,
        max_age=604800,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        httponly=True
    )

    security_audit_logger.log_event(
        user_id=user.user_id,
        user_email=user.email,
        role=user.role.value,
        action="LOGIN",
        resource_type="session",
        region_id=user.region_id
    )

    user_resp = UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        role=user.role,
        organization=user.organization,
        country=user.country,
        state=user.state,
        city=user.city,
        region_id=user.region_id,
        allowed_datasets=user.allowed_datasets,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )

    return AuthTokenResponse(access_token=token, user=user_resp)

@router.post("/logout", summary="Logout User Session")
async def logout(response: Response, current_user: User = Depends(get_optional_user)):
    response.delete_cookie(key="drishtigis_token", path="/")
    if current_user and current_user.user_id != "usr-anonymous-public":
        security_audit_logger.log_event(
            user_id=current_user.user_id,
            user_email=current_user.email,
            role=current_user.role.value,
            action="LOGOUT",
            resource_type="session",
            region_id=current_user.region_id
        )
    return {"message": "Logged out successfully."}

@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        organization=current_user.organization,
        country=current_user.country,
        state=current_user.state,
        city=current_user.city,
        region_id=current_user.region_id,
        allowed_datasets=current_user.allowed_datasets,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.get("/users", response_model=List[UserResponse], summary="List Registered Users (Admin)")
async def list_users(current_user: User = Depends(require_permission(Permission.MANAGE_USERS))):
    return user_store.list_users()

@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update User Role or Status (Admin)")
async def update_user(
    user_id: str,
    update_req: UserUpdate,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    updated = user_store.update_user(user_id, update_req)
    if not updated:
        raise HTTPException(status_code=404, detail=f"User ID '{user_id}' not found.")

    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="ROLE_CHANGED" if update_req.role else "USER_UPDATED",
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

@router.get("/regions", summary="List Registered Governance Regions")
async def list_regions(current_user: User = Depends(get_current_user)):
    return {"regions": user_store.regions}

@router.post("/regions", summary="Register Governance Region (Admin)")
async def create_region(
    region_data: Dict[str, Any],
    current_user: User = Depends(require_permission(Permission.MANAGE_REGIONS))
):
    res = user_store.add_region(region_data)
    security_audit_logger.log_event(
        user_id=current_user.user_id,
        user_email=current_user.email,
        role=current_user.role.value,
        action="REGION_REGISTERED",
        resource_type="region",
        resource_id=region_data.get("region_id"),
        details=region_data
    )
    return res

@router.get("/audit-logs", summary="View Security Audit Logs (Reviewer / Admin)")
async def get_audit_logs(
    limit: int = 100,
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOG))
):
    return {"logs": [l.model_dump() for l in security_audit_logger.get_logs(limit=limit)]}
