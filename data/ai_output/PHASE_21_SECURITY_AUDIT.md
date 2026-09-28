# DrishtiGIS — Phase 21 Security Audit Report

## 1. Authentication & RBAC Enforcement Audit
All Phase 21 administrative dataset, pipeline, inventory, analytics, and property intelligence endpoints enforce strict `require_admin` authorization.

### Protected Endpoints:
- `POST /api/v1/admin/datasets/upload` — Requires `ADMIN` role. Non-admin calls return HTTP 403 `Forbidden`.
- `GET /api/v1/admin/datasets` — Requires `ADMIN` role.
- `GET /api/v1/admin/datasets/{id}` — Requires `ADMIN` role.
- `POST /api/v1/admin/datasets/{id}/retry` — Requires `ADMIN` role.
- `POST /api/v1/admin/datasets/{id}/cancel` — Requires `ADMIN` role.
- `POST /api/v1/admin/datasets/{id}/publish` — Requires `ADMIN` role.
- `GET /api/v1/admin/analytics/summary` — Requires `ADMIN` role.
- `GET /api/v1/admin/properties` — Requires `ADMIN` role.

## 2. Ingestion & File Handling Protections
- **Streaming Byte Count Limit**: Enforces `MAX_UPLOAD_SIZE_MB=100` during streaming chunk consumption. Exceeding byte limit raises HTTP 413.
- **Path Traversal & Zip Bomb Defenses**: Rejects archives containing `..` path segments, exceeding 50 compressed entries, or exceeding 250 MB uncompressed threshold.
- **Sanitized Target Directories**: Saved uploaded files are isolated in `data/uploads/{dataset_id}/` using sanitized filenames.

## 3. Data Protection & Exposure Auditing
- Unauthenticated users attempting direct access to `/admin` or `/admin/*` routes are intercepted by Next.js middleware and redirected to `/login?redirect=...`.
- All administrative dataset upload, retry, publication, and region registration operations log audit events to `data/governance/audit_logs.json`.
