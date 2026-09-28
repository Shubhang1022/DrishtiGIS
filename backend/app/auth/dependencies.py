"""
FastAPI Authentication & Authorization Dependencies for DrishtiGIS.
Enforces Token Verification, Role Permissions, Region Isolation, and Dataset Scoping.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.auth.user_model import User, UserRole
from backend.app.auth.roles import Permission, has_permission
from backend.app.auth.auth_service import verify_access_token
from backend.app.auth.user_store import user_store

security_scheme = HTTPBearer(auto_error=False)

def extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    request: Request
) -> Optional[str]:
    if credentials and credentials.credentials:
        return credentials.credentials
    if request:
        return request.cookies.get("drishtigis_token")
    return None

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> User:
    """Validate Bearer token or HttpOnly session cookie and return active authenticated user."""
    raw_token = extract_token(credentials, request)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_store.get_by_id(payload.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> User:
    """Return authenticated user if valid token/cookie present, otherwise default PUBLIC user."""
    raw_token = extract_token(credentials, request)
    if raw_token:
        payload = verify_access_token(raw_token)
        if payload:
            user = user_store.get_by_id(payload.get("sub", ""))
            if user and user.is_active:
                return user

    # Default public user fallback for unauthenticated public routes
    return User(
        user_id="usr-anonymous-public",
        email="anonymous@drishtigis.in",
        name="Anonymous Public User",
        hashed_password="",
        role=UserRole.PUBLIC,
        organization="Public",
        region_id="bhopal_mp",
        allowed_datasets=["uavpal_bhopal", "bhopal_synthetic_parcels"],
        is_active=True
    )

def require_permission(permission: Permission):
    """Dependency factory enforcing explicit RBAC permission."""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted. Required permission: '{permission.value}' is not assigned to your role ({current_user.role.value})."
            )
        return current_user
    return permission_checker

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency enforcing that current user has ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted. Administrative privileges required."
        )
    return current_user

def check_region_access(user: User, target_region_id: Optional[str]) -> bool:
    """Check if user has access to target region_id."""
    if not target_region_id or user.region_id == "*":
        return True
    return user.region_id.lower() == target_region_id.lower()

def check_dataset_access(user: User, dataset_id: Optional[str]) -> bool:
    """Check if user has access to target dataset_id."""
    if not dataset_id or "*" in user.allowed_datasets:
        return True
    return dataset_id in user.allowed_datasets
