# DrishtiGIS — Production Dependency & Architecture Inventory

**Document Version:** 1.0.0  
**Phase:** 25 Production Deployment Readiness Audit  
**Date:** 2026-09-27  
**Platform:** DrishtiGIS (SIH26012 Evaluation Platform)

---

## 1. System Runtime & Core Frameworks

| Component | Framework / Tool | Version | Production Role |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Next.js (App Router, Turbopack) | `16.3.4` | Server-rendered UI, API route proxies, static page prerendering |
| **Frontend Runtime** | React / React DOM | `19.2.8` | Client component hydration, UI state management |
| **Frontend Map Client** | MapLibre GL JS | `6.8.0` | Geospatial canvas, vector tile rendering, WebGL raster rendering |
| **Frontend Styling** | Tailwind CSS / Lucide React | `4.x` / `1.42.0` | Production utility-first CSS design system |
| **Backend Framework** | FastAPI / Starlette | `0.123.0` / `0.41.3` | High-performance ASGI asynchronous geospatial REST API |
| **Backend Server** | Uvicorn | `0.38.0` | Production ASGI web server |
| **Python Runtime** | CPython | `3.12.0` | Backend execution environment |
| **Node.js Runtime** | Node.js / npm | `v24.11.0` / `11.12.1` | Frontend build engine and production SSR runner |

---

## 2. Build & Production Start Commands

### 2.1 Frontend Build & Start
```bash
# Directory: drishtigis/
# 1. Install production dependencies
npm ci

# 2. Compile and optimize production build
npm run build

# 3. Start production SSR server (Port 3000)
npm run start -- -p 3000
```

### 2.2 Backend Build & Start
```bash
# Directory: root (e:\Shubhang\projects\DrishtiGIS(SIH))
# 1. Install dependencies into virtual environment
pip install -r backend/requirements.txt

# 2. Run database migrations (when PostgreSQL is configured)
alembic upgrade head

# 3. Start production ASGI server (Port 8000, 2-4 workers)
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --workers 2
```

---

## 3. Environment Variables & Secret Inventory

| Variable Name | Classification | Default / Dev Fallback | Production Purpose |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | **REQUIRED_SECRET** | `dev-insecure-key-...` | HMAC-SHA256 signature key for JWT session tokens |
| `DATABASE_URL` | **REQUIRED_SECRET** | `sqlite+aiosqlite:///...` | PostgreSQL + PostGIS connection string |
| `NEXT_PUBLIC_API_URL` | **REQUIRED_PUBLIC** | `http://localhost:8000` | Public backend URL consumed by browser client |
| `NEXT_PUBLIC_BACKEND_URL`| **REQUIRED_PUBLIC** | `http://localhost:8000` | Alternative public backend URL identifier |
| `NEXT_PUBLIC_API_BASE` | **REQUIRED_PUBLIC** | `http://localhost:8000/api/v1` | Versioned API base route |
| `BACKEND_CORS_ORIGINS` | **REQUIRED_SECRET** | `http://localhost:3000` | Allowed frontend domains (CSV or JSON array) |
| `ENABLE_DEMO_ACCOUNTS` | **REQUIRED_SECRET** | `true` | Gate to disable pre-seeded privileged accounts in prod |
| `COOKIE_SECURE` | **REQUIRED_SECRET** | `false` | Sets `Secure` flag on `drishtigis_token` cookies for HTTPS |
| `COOKIE_SAMESITE` | **REQUIRED_SECRET** | `lax` | SameSite cookie attribute (`lax` or `none` for cross-site) |
| `NEXT_PUBLIC_SATELLITE_TILE_URL` | **REQUIRED_PUBLIC** | ArcGIS World Imagery | XYZ raster satellite basemap template |
| `OPENROUTER_API_KEY` | **OPTIONAL** | `""` | Key for external LLM generative assistant (OpenRouter) |
| `GEMINI_API_KEY` | **OPTIONAL** | `""` | Key for external Google Gemini AI model |
| `SUPABASE_URL` | **OPTIONAL** | `""` | Hosted Supabase PostGIS endpoint |
| `SUPABASE_SERVICE_KEY` | **OPTIONAL** | `""` | Hosted Supabase service role key |
| `MAX_UPLOAD_SIZE_MB` | **OPTIONAL** | `100` | Ingestion limit for raw drone rasters/archives |

---

## 4. Authentication & JWT Architecture

- **Token Standard:** JSON Web Token (JWT) signed via HMAC-SHA256 (`HS256`).
- **Token Claims:** `sub` (User ID), `email`, `name`, `role`, `region_id`, `allowed_datasets`, `iat`, `exp`.
- **Token Validity:** 7 days (`604,800` seconds).
- **Transport Mechanism (Dual-Mode):**
  1. `Authorization: Bearer <token>` attached via centralized `apiFetch` in client.
  2. `Set-Cookie: drishtigis_token=<token>; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800` sent with `credentials: "include"`.
- **Session Termination:** Handled by `POST /api/v1/auth/logout` which logs audit event, clears client tokens, and issues `Set-Cookie: drishtigis_token=; Max-Age=0; Path=/`.

---

## 5. Geospatial & Machine Learning Dependencies

| Library | Version | Purpose in DrishtiGIS |
| :--- | :--- | :--- |
| `rasterio` | `1.3.10` | GeoTIFF reading, dynamic windowed tile extraction, raster metadata |
| `shapely` | `2.1.1` | Vector geometry predicates, intersection, boundary overlap calculation |
| `pyproj` | `3.7.0` | Coordinate Reference System transformations (`EPSG:32643` ↔ `EPSG:4326` ↔ `EPSG:3857`) |
| `affine` | `3.0.1` | GeoTIFF affine matrix pixel-to-geographic transformations |
| `geopandas` | `1.0.1` | Spatial GeoDataFrame operations and spatial indexing |
| `pyogrio` | `0.13.0` | Fast C-based vector I/O for GeoJSON and GeoPackage |
| `pillow` | `12.3.0` | High-quality image resampling (Bicubic) and RGBA PNG tile generation |
| `numpy` | `2.4.6` | Numerical raster array manipulation, mask operations |
| `torch` | `2.5.1+cpu` | Neural network forward pass for building footprint inference on CPU |
| `torchvision` | `0.20.1+cpu` | Pretrained ResNet18 encoder feature extraction backbone |
| `scipy` / `scikit-image` | `1.15.3` / `0.25.2` | Watershed segmentation, polygonization contour tracing |

---

## 6. Filesystem & Persistence Classification

| Storage Path | Content | Current Mechanism | Production Classification | Durability / Migration Path |
| :--- | :--- | :--- | :--- | :--- |
| `data/governance/users.json` | User accounts, hashed passwords, roles | File JSON | **SHOULD BE DATABASE** | Ephemeral on unmounted containers. Migrate to PostgreSQL `users` table. |
| `data/governance/datasets.json`| Ingested dataset registry, stages, outputs | File JSON | **SHOULD BE DATABASE** | Ephemeral on unmounted containers. Migrate to PostgreSQL `datasets` table. |
| `data/governance/regions.json` | Administrative governance jurisdictions | File JSON | **SHOULD BE DATABASE** | Migrate to PostgreSQL `regions` table. |
| `data/governance/audit_log.jsonl`| Security audit logs (login, review, admin) | Append JSONL | **CENTRALIZED LOGGING** | Stream to CloudWatch, Elasticsearch, or Datadog. |
| `data/reviews/reviews.json` | Surveyor discrepancy review queue | File JSON | **SHOULD BE DATABASE** | Migrate to PostgreSQL `reviews` table. |
| `data/synthetic/` | Synthetic prototype parcels and properties | File JSON/GeoJSON | **DATABASE / READ-ONLY** | Prototype evaluation data. |
| `data/uploads/{dataset_id}/` | Raw uploaded ZIPs, GeoTIFFs, outputs | Local Filesystem | **SHOULD BE OBJECT STORAGE** | Ephemeral staging. Migrate to S3 / Cloudflare R2 bucket. |
| `Dataset/geospatial-data/BHOPAL` | Authoritative 30 UAV GeoTIFF tiles (~835MB) | Local Filesystem | **PERSISTENT VOLUME / OBJECT STORAGE** | Mount via AWS EFS / persistent disk volume. |
| `data/processed/tiles/` | Dynamically generated XYZ tile PNG cache | Local Filesystem | **TILE CDN CACHE** | CloudFront / Cloudflare Edge Cache. |
| `data/ai_models/uavpal/` | PyTorch checkpoint `best_model.pth` (57.4MB) | Local Filesystem | **PERSISTENT MODEL REGISTRY** | Immutable model asset bundled in container image. |

---

## 7. Background Worker & Asynchronous Jobs

- **Worker Mechanism:** In-process asynchronous task execution via `asyncio.create_task(run_dataset_pipeline(dataset_id))`.
- **Concurrency Control:** Thread-safe `threading.RLock()` and in-memory set `_active_workers`.
- **Restart Recovery:** Startup recovery handler `@app.on_event("startup")` scans for interrupted jobs in states `["REGISTERED", "VALIDATING", "PROCESSING"]` and re-queues them.
- **Horizontal Scaling Constraint:** **Single-node / Single-process only**. Multi-worker Uvicorn (`--workers > 1`) or multi-container clusters require Redis or Celery distributed locks to avoid duplicate pipeline execution.

---

## 8. External Network APIs & Third-Party Dependencies

1. **OpenFreeMap Vector Tiles**: `https://tiles.openfreemap.org/styles/bright` (Basemap style and glyphs; public free service, no API key required).
2. **ArcGIS Satellite Basemap**: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` (Satellite layer fallback; public free service).
3. **OpenStreetMap Data**: Pre-downloaded and baked into `data/osm/` (Offline self-contained; no live external network dependency required during normal operation).
4. **LLM Provider (Optional)**: OpenRouter (`https://openrouter.ai/api/v1/chat/completions`) or Google Gemini API. DrishtiGIS does **not** fail if this is unreachable; it switches automatically to the offline Grounded Tool Engine.

---

## 9. Hardware & Resource Sizing

| Metric | Minimum (Evaluation / Staging) | Recommended (Production City-Scale) |
| :--- | :--- | :--- |
| **CPU** | 2 vCPUs (x86_64) | 4–8 vCPUs |
| **RAM** | 4 GB | 8–16 GB (to buffer multi-tile raster warps and PyTorch tensors) |
| **Disk Space** | 10 GB persistent storage | 50–100 GB SSD (or persistent network volume) |
| **Network** | 100 Mbps uplink | 1 Gbps uplink (with CDN in front for XYZ raster tiles) |
| **GPU Acceleration** | Not required (CPU inference supported) | Optional (NVIDIA T4 / A10G for real-time high-throughput inference) |
