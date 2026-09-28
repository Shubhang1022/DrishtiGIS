"""
Authentication Service, Password Hashing and JWT Session Token Engine for DrishtiGIS.
Uses PBKDF2-HMAC-SHA256 password hashing and HMAC-SHA256 JWT token signing.
"""

import os
import json
import hmac
import hashlib
import base64
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.auth.user_model import User, UserResponse, UserRole

SECRET_KEY = settings.SECRET_KEY.encode("utf-8")

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique salt."""
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100000
    )
    b64_hash = base64.b64encode(pwd_hash).decode("utf-8")
    return f"pbkdf2:sha256:100000${salt}${b64_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify raw password against stored PBKDF2 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected_hash = hashed_password
        calculated_hash = hash_password(password, salt=salt)
        return hmac.compare_digest(expected_hash, calculated_hash)
    except Exception:
        return False

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded)

def create_access_token(user: User, expires_in_seconds: int = 86400 * 7) -> str:
    """Create a signed JWT access token containing user identity and role."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "region_id": user.region_id,
        "allowed_datasets": user.allowed_datasets,
        "exp": int(time.time()) + expires_in_seconds,
        "iat": int(time.time())
    }

    header_b64 = _b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(SECRET_KEY, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT access token signature and expiration."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY, signing_input, hashlib.sha256).digest()
        actual_sig = _b64_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64_decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None
