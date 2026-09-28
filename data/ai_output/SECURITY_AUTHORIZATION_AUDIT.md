# DRISHTIGIS — SECURITY & AUTHORIZATION AUDIT REPORT
## Role-Based Access Control (RBAC), Token Validation, Region Scoping & API Input Security

### Executive Summary
Direct API security testing was conducted against DrishtiGIS FastAPI endpoints to verify Role-Based Access Control (RBAC) enforcement across all 4 user roles (`PUBLIC`, `SURVEYOR`, `REVIEWER`, `ADMIN`), regional jurisdiction scoping (`bhopal_mp`), token verification handling, and payload input sanitization.

---

### 1. Direct Backend API Security Test Matrix

| Test Scenario | Attempted Action | Actor Role | Expected Behavior | Actual API Response | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Admin Route Protection** | Access user management `/api/v1/admin/users` | `PUBLIC` / `SURVEYOR` / `REVIEWER` | `HTTP 403 Forbidden` | `HTTP 403 Forbidden` (`"Insufficient privileges"`) | **PASS** |
| **Review Approval Scoping** | Submit final review approval | `PUBLIC` / `SURVEYOR` | `HTTP 403 Forbidden` | `HTTP 403 Forbidden` (`"Role REVIEWER or ADMIN required"`) | **PASS** |
| **Surveyor Edit Scoping** | Submit geometry edit | `PUBLIC` | `HTTP 401 Unauthorized` | `HTTP 401 Unauthorized` (`"Authentication required"`) | **PASS** |
| **Cross-Region Access** | Access resource outside assigned region | `SURVEYOR` (`bhopal_mp` accessing `delhi_ncr`) | `HTTP 403 Forbidden` | `HTTP 403 Forbidden` (`"Region access denied"`) | **PASS** |
| **Invalid JWT Token** | Send malformed Bearer token in header | Any | `HTTP 401 Unauthorized` | `HTTP 401 Unauthorized` (`"Invalid authentication token"`) | **PASS** |
| **Expired JWT Token** | Send expired Bearer token in header | Any | `HTTP 401 Unauthorized` | `HTTP 401 Unauthorized` (`"Token expired"`) | **PASS** |
| **Path Traversal Protection** | Attempt `GET /api/v1/exports/../../.env` | Unauthenticated / Public | `HTTP 400 Bad Request` or 404 | `HTTP 400 Bad Request` (`"Invalid export filename"`) | **PASS** |
| **Oversized Payload Test** | Post 50MB malformed GeoJSON payload | Any | `HTTP 413 Payload Too Large` or 422 | `HTTP 422 Unprocessable Entity` | **PASS** |

---

### 2. Password & Credential Security Standards
- **Hashing Algorithm**: PBKDF2 with SHA-256 (100,000 iterations + unique salt per user).
- **No Plaintext Passwords**: Password fields are never logged or stored in plaintext.
- **Session Tokens**: Cryptographically signed HS256 JWT tokens containing `sub`, `role`, `region`, and `exp` claims.
