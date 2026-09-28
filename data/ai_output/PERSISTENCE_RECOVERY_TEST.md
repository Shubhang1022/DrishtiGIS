# DRISHTIGIS — PERSISTENCE & RESTART RECOVERY TEST REPORT
## State Storage Integrity, File Locking, Server Restart Recovery & Migration Path

### Executive Summary
This report documents the verification of state persistence across backend server restarts. DrishtiGIS uses a structured JSON file-store architecture for local demonstration state management, backing up users, surveyor reviews, field verifications, dataset metadata, and append-only security audit logs.

---

### 1. Persistence Verification Test Results

| Entity Store | File Path | Restart Test Procedure | Persistence Verification | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Review State Store** | `data/reviews/reviews.json` | Submit surveyor review edit &rarr; Restart server &rarr; Re-query `/api/v1/reviews` | Verified: Saved review edit state `SURVEYOR_EDITED` fully restored. | **PASS** |
| **Field Verification Store** | `data/reviews/verifications.json` | Attach GNSS evidence &rarr; Restart server &rarr; Re-query verification details | Verified: Attachment metadata & notes intact. | **PASS** |
| **Security Audit Log** | `data/reviews/audit_logs.json` | Trigger review action &rarr; Restart server &rarr; Inspect audit log | Verified: Append-only log entries preserved across restarts. | **PASS** |
| **User Account Store** | `data/seed/users.json` | Query user accounts &rarr; Restart server &rarr; Verify authentication | Verified: Passwords remain securely PBKDF2 hashed and active. | **PASS** |

---

### 2. Architecture Limitations of JSON File-Store & PostGIS Recommendation

1. **Atomicity & Locking**:
   - Current JSON file persistence uses file-level locking (`RLock`) to prevent write overlap.
   - *Limitation*: While robust for local multi-user evaluation (5-10 users), high-throughput enterprise write workloads (>1,000 writes/sec) could experience IO latency.
2. **Production Database Migration Path**:
   - For enterprise production deployment across multiple state survey departments, DrishtiGIS is architected to swap the JSON store service implementation with PostGIS / PostgreSQL without modifying the API contracts or frontend controllers.
