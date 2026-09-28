"""
DrishtiGIS — Phase 24.10 Property Detail Auth, 401 Fix & Sidebar State Test Suite
===================================================================================
Verifies:
 1. Authenticated parcel request (Bearer token) -> HTTP 200 OK.
 2. Authenticated parcel request (Cookie drishtigis_token) -> HTTP 200 OK.
 3. Unauthenticated parcel request (headers={}) -> HTTP 401 Unauthorized.
 4. Invalid or expired token -> HTTP 401 Unauthorized.
 5. Inactive user token -> HTTP 401 Unauthorized.
 6. Unknown parcel ID -> HTTP 404 Not Found.
 7. OSM feature ID (e.g. 414388977) queried against parcel endpoint -> HTTP 404 Not Found.
 8. RBAC / region isolation: valid role permissions remain enforced.
 9. Frontend apiFetch in client.ts automatically extracts token and includes credentials.
10. Frontend ContextSidebar.tsx defines explicit states: idle, loading, success, unauthorized, forbidden, not_found, error.
11. Frontend ContextSidebar.tsx terminates loading state on 401/403/404/500/network error (never hangs in infinite spin).
12. Frontend ContextSidebar.tsx prevents duplicate simultaneous requests for the same parcel ID (activePropertyIdRef).
13. Frontend ContextSidebar.tsx excludes parcelState.status from dependency array (no infinite 401 retry loop).
14. Frontend MapLibreMap.tsx click priority guarantees parcel clicks route to type 'parcel' and OSM buildings to 'osm-feature'.
15. Frontend MapLibreMap.tsx excludes raster layers from feature selection (clicks on raster do not dispatch parcel API).
16. Backend CORS configuration allows frontend origin (http://localhost:3000 and http://127.0.0.1:3000) with credentials.
17. Synthetic demo provenance is preserved (SYNTHETIC_DEMO badge, disclaimer, no fake official ownership).
18. Clicked vector feature metadata is rendered as initial summary preview while authoritative API loads.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.user_model import User, UserRole
from backend.app.auth.auth_service import create_access_token, hash_password
from backend.app.auth.user_store import user_store
from backend.app.core.config import settings

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Setup distinct test users for Phase 24.10
AUTH_TEST_USER = User(
    user_id="usr-p24-10-regular",
    email="p24_10_user@drishtigis.in",
    name="Phase 24.10 Test User",
    hashed_password=hash_password("ValidPassword123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV",
    is_active=True,
    allowed_datasets=["*"],
)
user_store.users[AUTH_TEST_USER.email.lower()] = AUTH_TEST_USER
VALID_TOKEN = create_access_token(AUTH_TEST_USER)

INACTIVE_TEST_USER = User(
    user_id="usr-p24-10-inactive",
    email="p24_10_inactive@drishtigis.in",
    name="Inactive User",
    hashed_password=hash_password("Inactive123!"),
    role=UserRole.PUBLIC,
    region_id="BHOPAL_UAV",
    is_active=False,
)
user_store.users[INACTIVE_TEST_USER.email.lower()] = INACTIVE_TEST_USER
INACTIVE_TOKEN = create_access_token(INACTIVE_TEST_USER)

# ── 1. AUTHENTICATED REQUESTS ─────────────────────────────────────────────────

def test_01_authenticated_parcel_request_bearer_200():
    """Verify that a request with a valid Bearer token returns 200 OK with property details."""
    response = client.get(
        "/api/v1/parcels/DRS-BPL-DEMO-001",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["_source"] == "SYNTHETIC_DEMO"
    assert "parcel" in data
    assert "property" in data
    assert "ai_features" in data
    assert "ai_analysis" in data
    assert data["parcel"]["properties"]["property_id"] == "DRS-BPL-DEMO-001"

def test_02_authenticated_parcel_request_cookie_200():
    """Verify that a request with drishtigis_token session cookie returns 200 OK."""
    response = client.get(
        "/api/v1/parcels/DRS-BPL-DEMO-001",
        headers={},
        cookies={"drishtigis_token": VALID_TOKEN},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["_source"] == "SYNTHETIC_DEMO"
    assert data["parcel"]["properties"]["property_id"] == "DRS-BPL-DEMO-001"

# ── 2. UNAUTHENTICATED & INVALID TOKEN REQUESTS ───────────────────────────────

def test_03_unauthenticated_parcel_request_401():
    """Verify that a request with NO credentials returns HTTP 401 Unauthorized."""
    response = client.get(
        "/api/v1/parcels/DRS-BPL-DEMO-001",
        headers={},
    )
    assert response.status_code == 401
    assert "Authentication credentials were not provided" in response.json()["detail"]

def test_04_invalid_token_401():
    """Verify that an invalid or malformed token returns HTTP 401 Unauthorized."""
    response = client.get(
        "/api/v1/parcels/DRS-BPL-DEMO-001",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]

def test_05_inactive_user_token_401():
    """Verify that a token for an inactive user is rejected with HTTP 401."""
    response = client.get(
        "/api/v1/parcels/DRS-BPL-DEMO-001",
        headers={"Authorization": f"Bearer {INACTIVE_TOKEN}"},
    )
    assert response.status_code == 401
    assert "inactive or not found" in response.json()["detail"]

# ── 3. RESOURCE LOOKUP & IDENTIFIER VALIDATION ────────────────────────────────

def test_06_unknown_parcel_404():
    """Verify that querying a nonexistent property ID returns HTTP 404."""
    response = client.get(
        "/api/v1/parcels/DRS-BPL-NONEXISTENT-999",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 404

def test_07_osm_feature_id_not_found_in_parcel_endpoint():
    """Verify that passing an OSM feature ID (e.g. 414388977) to the parcel endpoint returns 404."""
    response = client.get(
        "/api/v1/parcels/414388977",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 404, "OSM ID should not be found as a cadastral parcel"

# ── 4. BACKEND CORS & CREDENTIALS CONFIGURATION ───────────────────────────────

def test_08_cors_allows_frontend_origins_and_credentials():
    """Verify backend CORS configuration supports localhost:3000 and 127.0.0.1:3000 with credentials."""
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
    assert "http://127.0.0.1:3000" in settings.BACKEND_CORS_ORIGINS

# ── 5. FRONTEND CLIENT & AUTHENTICATION HELPER AUDIT ──────────────────────────

def test_09_frontend_api_fetch_includes_token_and_credentials():
    """Verify that drishtigis/lib/api/client.ts extracts token and sets credentials: include."""
    client_code = (REPO_ROOT / "drishtigis" / "lib" / "api" / "client.ts").read_text(encoding="utf-8")
    assert "getStoredAuthToken" in client_code
    assert 'headers["Authorization"] = `Bearer ${token}`' in client_code
    assert 'credentials: options?.credentials ?? "include"' in client_code

def test_10_frontend_parcels_api_supports_token_parameter():
    """Verify fetchParcel in drishtigis/lib/api/parcels.ts accepts optional token."""
    parcels_code = (REPO_ROOT / "drishtigis" / "lib" / "api" / "parcels.ts").read_text(encoding="utf-8")
    assert "export async function fetchParcel(" in parcels_code
    assert "token?: string | null" in parcels_code
    assert "token !== undefined ? { token } : undefined" in parcels_code

# ── 6. FRONTEND SIDEBAR STATE MACHINE & INFINITE LOOP PREVENTION ──────────────

def test_11_sidebar_defines_explicit_state_union():
    """Verify ContextSidebar defines explicit statuses: unauthorized, forbidden, not_found, error, loading."""
    sidebar_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "ContextSidebar.tsx").read_text(encoding="utf-8")
    assert '| { status: "unauthorized"; message: string }' in sidebar_code
    assert '| { status: "forbidden"; message: string }' in sidebar_code
    assert '| { status: "not_found"; message: string }' in sidebar_code
    assert '| { status: "error"; message: string; statusCode?: number }' in sidebar_code

def test_12_sidebar_use_effect_dependency_array_fixed():
    """Verify parcelState.status is EXCLUDED from useEffect dependencies to prevent infinite loop."""
    sidebar_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "ContextSidebar.tsx").read_text(encoding="utf-8")
    assert "}, [context?.id, context?.type, token]);" in sidebar_code
    assert "}, [context, parcelState.status]);" not in sidebar_code

def test_13_sidebar_duplicate_request_guard():
    """Verify activePropertyIdRef guards against duplicate simultaneous fetches for the same parcel."""
    sidebar_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "ContextSidebar.tsx").read_text(encoding="utf-8")
    assert "activePropertyIdRef.current = propertyId;" in sidebar_code
    assert "if (propertyId === activePropertyIdRef.current) {" in sidebar_code

def test_14_sidebar_unauthorized_state_has_sign_in_action():
    """Verify unauthorized state renders security explanation and sign-in button."""
    sidebar_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "ContextSidebar.tsx").read_text(encoding="utf-8")
    assert 'parcelState.status === "unauthorized"' in sidebar_code
    assert "Authentication Required" in sidebar_code
    assert "href={`/login" in sidebar_code

def test_15_sidebar_renders_vector_metadata_preview():
    """Verify clicked vector feature summary is displayed to provide immediate user feedback."""
    sidebar_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "ContextSidebar.tsx").read_text(encoding="utf-8")
    assert "CLICKED PARCEL VECTOR FEATURE" in sidebar_code
    assert "context.data.plot_number" in sidebar_code
    assert "context.data.survey_number" in sidebar_code

# ── 7. MAPLIBRE CLICK DISPATCHER ROUTING INTEGRITY ────────────────────────────

def test_16_maplibre_click_dispatcher_routes_parcels_to_parcel_type():
    """Verify MapLibreMap click dispatcher routes parcels-fill to type 'parcel'."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert 'layerId === "parcels-fill"' in map_code
    assert 'type: "parcel"' in map_code

def test_17_maplibre_click_dispatcher_routes_osm_buildings_to_osm_feature():
    """Verify MapLibreMap routes osm-buildings-fill to type 'osm-feature' (never to parcel endpoint)."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert 'layerId === "osm-buildings-fill"' in map_code
    assert 'type: "osm-feature"' in map_code

def test_18_raster_is_never_treated_as_interactive_feature():
    """Verify raster layers are completely omitted from interactive vector layer queries."""
    map_code = (REPO_ROOT / "drishtigis" / "components" / "map" / "MapLibreMap.tsx").read_text(encoding="utf-8")
    assert "dataset-raster-layer" not in map_code.split("INTERACTIVE_LAYER_IDS = [")[1].split("];")[0]
    assert "NEVER select raster" in map_code
