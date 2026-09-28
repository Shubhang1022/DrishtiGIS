# DrishtiGIS — Production Deployment Runbook

**Version:** 1.0.0  
**Target Environment:** Staging & Production  
**Platform:** Ubuntu 22.04 LTS / Debian 12 / Docker / AWS EC2  
**Date:** 2026-09-27  

---

## 1. System Prerequisites

### 1.1 Hardware Specifications
- **CPU:** Minimum 2 vCPUs (x86_64), Recommended 4+ vCPUs
- **Memory:** Minimum 4 GB RAM, Recommended 8+ GB RAM (to handle GDAL raster reprojections and PyTorch tensor operations)
- **Disk:** Minimum 20 GB SSD persistent storage (Bhopal dataset consumes ~1.05 GB)
- **Network:** 100 Mbps uplink minimum, HTTPS (port 443) enabled

### 1.2 Software & Native Libraries
```bash
# Ubuntu / Debian native dependencies
sudo apt-get update && sudo apt-get install -y \
    python3.12 python3.12-venv python3-pip \
    gdal-bin libgdal-dev libgeos-dev libproj-dev \
    nodejs npm nginx certbot python3-certbot-nginx
```

---

## 2. Environment Variables Configuration

Copy `.env.example` to production `.env` (backend) and `drishtigis/.env.production` (frontend):

### 2.1 Backend Environment (`.env`)
```ini
# Cryptographic signing key (Generate via: openssl rand -hex 32)
SECRET_KEY=generate-a-strong-random-hex-string-for-production

# Database (PostgreSQL + PostGIS connection string)
DATABASE_URL=postgresql+asyncpg://drishti_user:secure_password@localhost:5432/drishtigis

# Production Security Gates
ENABLE_DEMO_ACCOUNTS=false
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
ENVIRONMENT=production
DEBUG=false

# Allowed Frontend Origins (Comma-separated)
BACKEND_CORS_ORIGINS=https://app.drishtigis.in,https://drishtigis.in

# Max Upload Size (MB)
MAX_UPLOAD_SIZE_MB=100
```

### 2.2 Frontend Environment (`drishtigis/.env.production`)
```ini
NEXT_PUBLIC_API_URL=https://api.drishtigis.in
NEXT_PUBLIC_BACKEND_URL=https://api.drishtigis.in
NEXT_PUBLIC_API_BASE=https://api.drishtigis.in/api/v1
NEXT_PUBLIC_SATELLITE_TILE_URL=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}
```

---

## 3. Build Commands

### 3.1 Backend Environment Setup
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3.2 Frontend Production Build
```bash
cd drishtigis
npm ci
npm run build
cd ..
```

---

## 4. Backend Start Command (Systemd / Supervisor)

### 4.1 Production Systemd Service (`/etc/systemd/system/drishtigis-backend.service`)
```ini
[Unit]
Description=DrishtiGIS FastAPI Backend Service
After=network.target

[Service]
User=drishti
Group=drishti
WorkingDirectory=/opt/drishtigis
EnvironmentFile=/opt/drishtigis/.env
ExecStart=/opt/drishtigis/venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.2 Start Command
```bash
sudo systemctl daemon-reload
sudo systemctl enable drishtigis-backend
sudo systemctl start drishtigis-backend
```

---

## 5. Frontend Start / Deploy Command

### 5.1 Production Systemd Service (`/etc/systemd/system/drishtigis-frontend.service`)
```ini
[Unit]
Description=DrishtiGIS Next.js Frontend Service
After=network.target

[Service]
User=drishti
Group=drishti
WorkingDirectory=/opt/drishtigis/drishtigis
EnvironmentFile=/opt/drishtigis/drishtigis/.env.production
ExecStart=/usr/bin/npm run start -- -p 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 5.2 Start Command
```bash
sudo systemctl daemon-reload
sudo systemctl enable drishtigis-frontend
sudo systemctl start drishtigis-frontend
```

---

## 6. Nginx & Reverse Proxy Configuration

Create `/etc/nginx/sites-available/drishtigis.conf`:
```nginx
# Frontend Web App
server {
    server_name app.drishtigis.in drishtigis.in;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend Geospatial API
server {
    server_name api.drishtigis.in;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 7. HTTPS Configuration (Certbot SSL)

```bash
sudo certbot --nginx -d drishtigis.in -d app.drishtigis.in -d api.drishtigis.in --non-interactive --agree-tos -m admin@drishtigis.in
```

---

## 8. Storage & Volume Configuration

Ensure the following directories are located on persistent storage (e.g., EBS volume mounted at `/opt/drishtigis/data`):
```bash
sudo mkdir -p /opt/drishtigis/data/{governance,uploads,processed,osm,ai_output,reviews}
sudo mkdir -p /opt/drishtigis/Dataset/geospatial-data/BHOPAL
sudo chown -R drishti:drishti /opt/drishtigis/data /opt/drishtigis/Dataset
```

---

## 9. Health Checks & Monitoring

Execute health check verification:
```bash
# Backend Health Check
curl -s -f https://api.drishtigis.in/api/v1/health | grep '"status":"ok"'

# Frontend Availability
curl -s -f -I https://app.drishtigis.in/ | grep "200 OK"
```

---

## 10. Rollback Procedure

In the event of a critical deployment failure:
1. **Revert Git Release**:
   ```bash
   git checkout <PREVIOUS_STABLE_TAG_OR_COMMIT>
   ```
2. **Rebuild Frontend Bundle**:
   ```bash
   cd drishtigis && npm ci && npm run build && cd ..
   ```
3. **Restart Services**:
   ```bash
   sudo systemctl restart drishtigis-backend
   sudo systemctl restart drishtigis-frontend
   ```
4. **Verify Health**:
   ```bash
   curl -s -f https://api.drishtigis.in/api/v1/health
   ```

---

## 11. Process Restart Procedure

```bash
# Orderly restart of both tiers
sudo systemctl restart drishtigis-backend
sudo systemctl restart drishtigis-frontend
sudo systemctl reload nginx
```

---

## 12. Backup & Recovery Procedure

### Daily Backup Script (`/opt/drishtigis/scripts/backup.sh`)
```bash
#!/usr/bin/env bash
set -e
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/backups/drishtigis

mkdir -p "$BACKUP_DIR"

# 1. Backup PostgreSQL Database
pg_dump -U drishti_user -h localhost drishtigis | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# 2. Backup Local Governance & Metadata JSON stores
tar -czf "$BACKUP_DIR/governance_$TIMESTAMP.tar.gz" -C /opt/drishtigis/data governance reviews

# 3. Rotate backups (Keep last 14 days)
find "$BACKUP_DIR" -type f -mtime +14 -delete
```

---

## 13. Smoke Test Checklist (Post-Deployment)

1. [ ] Navigate to `https://app.drishtigis.in/` — Landing page renders with branding.
2. [ ] Sign in with administrative or surveyor credentials — Redirects to map.
3. [ ] Refresh page on `https://app.drishtigis.in/app/map` — Session persists.
4. [ ] Zoom to zoom level 17+ on Bhopal — UAV raster tiles render sharp aerial imagery.
5. [ ] Click a cadastral property polygon — ContextSidebar opens with Property ID, Plot #, Owner, and DEMO badge.
6. [ ] Confirm loading spinner terminates immediately (no rolling/infinite loop).
7. [ ] Click 'Assistant' tab — Submit prompt; Grounded Tool Engine responds with spatial context.
8. [ ] Click 'Export' — Request GeoJSON export; valid file downloads.
9. [ ] Log out — Confirm session ends and direct access to `/api/v1/parcels/...` returns `401 Unauthorized`.

---

## 14. Security Checklist

- [ ] `SECRET_KEY` is externalized and NOT the default dev string.
- [ ] `ENABLE_DEMO_ACCOUNTS=false` is enforced in production.
- [ ] `COOKIE_SECURE=true` is set.
- [ ] HTTPS enforced on all domains (no mixed HTTP content).
- [ ] Backend CORS restricted to production frontend domains.
- [ ] File uploads validate extensions and reject path traversal / ZIP slip entries.
- [ ] Passwords hashed with PBKDF2-HMAC-SHA256 (100,000 rounds).
- [ ] No tokens or user coordinates logged to `audit_log.jsonl` or server stdout.
