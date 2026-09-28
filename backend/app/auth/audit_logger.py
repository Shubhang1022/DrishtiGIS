"""
Security and Governance Audit Logger for DrishtiGIS.
Records security events, auth attempts, geometry edits, approvals, and administrative actions.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[4]
GOVERNANCE_DIR = ROOT / "data" / "governance"
AUDIT_LOG_FILE = GOVERNANCE_DIR / "security_audit_logs.json"

class SecurityAuditLog(BaseModel):
    audit_id: str
    user_id: str
    user_email: str
    role: str
    action: str  # LOGIN, LOGOUT, ROLE_CHANGED, GEOMETRY_EDITED, REVIEW_ACCEPTED, EXPORT_GENERATED, etc.
    resource_type: str  # parcel, building, review, dataset, region, user
    resource_id: Optional[str] = None
    timestamp: str
    region_id: Optional[str] = None
    dataset_id: Optional[str] = None
    details: Dict[str, Any] = {}

class SecurityAuditLogger:
    def __init__(self):
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        self.logs: List[SecurityAuditLog] = self._load_logs()

    def _load_logs(self) -> List[SecurityAuditLog]:
        if not AUDIT_LOG_FILE.exists():
            return []
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [SecurityAuditLog(**item) for item in data.get("logs", [])]
        except Exception:
            return []

    def _save_logs(self):
        try:
            with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump({"logs": [l.model_dump() for l in self.logs]}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to persist audit log: {e}")

    def log_event(
        self,
        user_id: str,
        user_email: str,
        role: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        region_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SecurityAuditLog:
        item = SecurityAuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            user_email=user_email,
            role=role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            region_id=region_id,
            dataset_id=dataset_id,
            details=details or {}
        )
        self.logs.append(item)
        self._save_logs()
        return item

    def get_logs(self, limit: int = 100, user_id: Optional[str] = None, action: Optional[str] = None) -> List[SecurityAuditLog]:
        results = self.logs
        if user_id:
            results = [l for l in results if l.user_id == user_id]
        if action:
            results = [l for l in results if l.action.upper() == action.upper()]
        return results[-limit:]

security_audit_logger = SecurityAuditLogger()
