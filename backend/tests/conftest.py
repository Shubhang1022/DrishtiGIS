"""
Global Pytest Configuration and TestClient Authorization Interceptor for DrishtiGIS.
Ensures existing regression tests include valid default authentication headers
while allowing explicit security tests to test unauthenticated / unauthorized requests.
"""

import pytest
from starlette.testclient import TestClient

from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store

_DEFAULT_TEST_USER = User(
    user_id="usr-default-pytest-user",
    email="default-pytest@drishtigis.in",
    name="Pytest Default User",
    hashed_password=hash_password("Pytest123!"),
    role=UserRole.ADMIN,
    region_id="*",
    allowed_datasets=["*"]
)
user_store.users[_DEFAULT_TEST_USER.email.lower()] = _DEFAULT_TEST_USER
_DEFAULT_TOKEN = create_access_token(_DEFAULT_TEST_USER)

_orig_request = TestClient.request

def _patched_request(self, method, url, *args, **kwargs):
    # If headers was omitted or explicitly passed as None, inject default authenticated test token
    if kwargs.get("headers") is None:
        kwargs["headers"] = {"Authorization": f"Bearer {_DEFAULT_TOKEN}"}

    return _orig_request(self, method, url, *args, **kwargs)

TestClient.request = _patched_request
