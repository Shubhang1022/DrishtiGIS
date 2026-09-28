# DrishtiGIS — Phase 20 Authentication & Session Audit Report

## 1. Authentication Architecture
DrishtiGIS uses server-issued JWT tokens delivered via secure `HttpOnly` cookies (`drishtigis_token`) for all API requests and route navigation.

### Cookie Configuration:
- `key`: `drishtigis_token`
- `httponly`: `True` (prevents JavaScript token extraction via `document.cookie`)
- `samesite`: `lax` (protects against Cross-Site Request Forgery)
- `path`: `/`
- `max_age`: 604,800 seconds (7 days)

## 2. Route Protection & Redirect Controls
Next.js middleware (`drishtigis/middleware.ts`) enforces default-deny protection across all 11 private paths:
- `/app/*`
- `/admin/*`
- `/map`
- `/profile`
- `/dashboard`
- `/review`
- `/assistant`
- `/exports`
- `/reports`
- `/history`
- `/property/*`

### Unauthenticated Navigation Behavior:
- When an unauthenticated user attempts direct access to any private route, middleware intercepts the request and issues HTTP 307 to `/login?redirect=<safe_relative_path>`.
- Private page HTML content is never rendered to unauthenticated clients.

## 3. Session Restoration & Logout
- **Session Restoration**: On page refresh or browser restart, `AuthContext` queries `GET /api/v1/auth/me` with cookie credentials, populating user state (`user_id`, `email`, `name`, `role`, `region_id`).
- **Logout Execution**: Invoking `POST /api/v1/auth/logout` explicitly deletes the `drishtigis_token` cookie and logs a `LOGOUT` audit event.

## 4. Role-Based Access Control (RBAC) Verification
- **Roles Evaluated**: `ADMIN`, `SURVEYOR`, `PUBLIC`
- **Admin Verification**: Administrative routes (`/admin/*`) require `require_admin` dependency. Attempts by non-admin accounts return HTTP 403 `Forbidden`.
