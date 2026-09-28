"""
DrishtiGIS — Private User Profile Persistence Service
======================================================
Provides thread-safe RLock persistence for user profile details.
Stored at data/governance/user_profiles.json.

PRIVACY REQUIREMENTS:
- Scoped strictly by authenticated user_id.
- Personal contact information (phone, address, PIN code) is private by default.
- Never exposed through public parcel endpoints or unauthenticated APIs.
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
PROFILES_FILE = GOVERNANCE_DIR / "user_profiles.json"

class UserProfileData(BaseModel):
    user_id: str
    full_name: Optional[str] = ""
    phone_number: Optional[str] = ""
    house_number: Optional[str] = ""
    street_locality: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    pincode: Optional[str] = ""
    organization: Optional[str] = ""
    show_name_publicly: bool = False
    show_address_publicly: bool = False
    show_phone_publicly: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserProfileStore:
    def __init__(self):
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.profiles: Dict[str, UserProfileData] = {}
        self._load()

    def _load(self):
        with self._lock:
            if PROFILES_FILE.exists():
                try:
                    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for uid, item in data.get("profiles", {}).items():
                            self.profiles[uid] = UserProfileData(**item)
                except Exception as e:
                    print(f"Warning: Failed to load user_profiles.json: {e}")

    def _save(self):
        with self._lock:
            tmp_file = PROFILES_FILE.with_suffix(".tmp")
            try:
                payload = {uid: prof.model_dump() for uid, prof in self.profiles.items()}
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump({"profiles": payload}, f, indent=2)
                os.replace(tmp_file, PROFILES_FILE)
            except Exception as e:
                if tmp_file.exists():
                    os.remove(tmp_file)
                print(f"Warning: Failed to save user_profiles.json: {e}")

    def get_profile(self, user_id: str, default_name: str = "", default_org: str = "", default_city: str = "", default_state: str = "") -> UserProfileData:
        """Fetch saved profile for specified user_id, initializing defaults if new."""
        with self._lock:
            profile = self.profiles.get(user_id)
            if not profile:
                now = datetime.now(timezone.utc).isoformat()
                profile = UserProfileData(
                    user_id=user_id,
                    full_name=default_name,
                    organization=default_org,
                    city=default_city,
                    state=default_state,
                    created_at=now,
                    updated_at=now
                )
                self.profiles[user_id] = profile
                self._save()
            return profile

    def save_profile(self, user_id: str, update_dict: Dict[str, Any]) -> UserProfileData:
        """Update profile for specified user_id."""
        with self._lock:
            existing = self.get_profile(user_id)
            now = datetime.now(timezone.utc).isoformat()

            updated_data = existing.model_dump()
            for key, val in update_dict.items():
                if key != "user_id" and val is not None:
                    updated_data[key] = val

            updated_data["updated_at"] = now
            profile = UserProfileData(**updated_data)
            self.profiles[user_id] = profile
            self._save()
            return profile

    def delete_profile(self, user_id: str) -> bool:
        """Delete profile for specified user_id."""
        with self._lock:
            if user_id in self.profiles:
                del self.profiles[user_id]
                self._save()
                return True
            return False

user_profile_store = UserProfileStore()
