"""
User and governance schemas for DrishtiGIS.
"""

from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.auth.roles import UserRole

class User(BaseModel):
    user_id: str
    email: str
    name: str
    hashed_password: str
    role: UserRole = UserRole.PUBLIC
    organization: Optional[str] = "DrishtiGIS Public"
    country: str = "India"
    state: Optional[str] = "Madhya Pradesh"
    city: Optional[str] = "Bhopal"
    region_id: Optional[str] = "bhopal_mp"  # Scoped region access ('*' for all)
    allowed_datasets: List[str] = Field(default_factory=lambda: ["*"])  # Allowed dataset IDs
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: UserRole = UserRole.PUBLIC
    organization: Optional[str] = None
    country: Optional[str] = "India"
    state: Optional[str] = "Madhya Pradesh"
    city: Optional[str] = "Bhopal"
    region_id: Optional[str] = "bhopal_mp"

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: UserRole
    organization: Optional[str] = None
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    region_id: Optional[str] = None
    allowed_datasets: List[str] = Field(default_factory=list)
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    organization: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    region_id: Optional[str] = None
    allowed_datasets: Optional[List[str]] = None
    is_active: Optional[bool] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
