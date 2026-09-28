"""
DrishtiGIS — Private User HOME Location Persistence Service
=============================================================
Provides thread-safe RLock persistence for private, user-scoped HOME location markers.
Stored at data/governance/user_homes.json.

PRIVACY REQUIREMENTS:
- Scoped strictly by authenticated user_id.
- Never accessible to other users, public APIs, AI assistant, exports, or logs.
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE_DIR = ROOT / "data" / "governance"
HOMES_FILE = GOVERNANCE_DIR / "user_homes.json"

class UserHomeLocation(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address_label: Optional[str] = "HOME"
    accuracy_m: Optional[float] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserHomeStore:
    def __init__(self):
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.homes: Dict[str, UserHomeLocation] = {}
        self._load()

    def _load(self):
        with self._lock:
            if HOMES_FILE.exists():
                try:
                    with open(HOMES_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for uid, item in data.get("homes", {}).items():
                            self.homes[uid] = UserHomeLocation(**item)
                except Exception as e:
                    print(f"Warning: Failed to load user_homes.json: {e}")

    def _save(self):
        with self._lock:
            tmp_file = HOMES_FILE.with_suffix(".tmp")
            try:
                payload = {uid: loc.model_dump() for uid, loc in self.homes.items()}
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump({"homes": payload}, f, indent=2)
                os.replace(tmp_file, HOMES_FILE)
            except Exception as e:
                if tmp_file.exists():
                    os.remove(tmp_file)
                print(f"Warning: Failed to save user_homes.json: {e}")

    def get_home(self, user_id: str) -> Optional[UserHomeLocation]:
        """Fetch saved HOME location for specified authenticated user_id."""
        with self._lock:
            return self.homes.get(user_id)

    def save_home(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        address_label: str = "HOME",
        accuracy_m: Optional[float] = None
    ) -> UserHomeLocation:
        """Save or update HOME location for specified authenticated user_id."""
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            existing = self.homes.get(user_id)
            created_at = existing.created_at if existing else now

            home = UserHomeLocation(
                user_id=user_id,
                latitude=round(float(latitude), 6),
                longitude=round(float(longitude), 6),
                address_label=address_label or "HOME",
                accuracy_m=round(float(accuracy_m), 2) if accuracy_m is not None else None,
                created_at=created_at,
                updated_at=now
            )
            self.homes[user_id] = home
            self._save()
            return home

    def delete_home(self, user_id: str) -> bool:
        """Delete HOME location for specified authenticated user_id."""
        with self._lock:
            if user_id in self.homes:
                del self.homes[user_id]
                self._save()
                return True
            return False

user_home_store = UserHomeStore()
