"""
DrishtiGIS — Private User Property Persistence Service
========================================================
Provides thread-safe RLock persistence for user-registered property markers.
Stored at data/governance/user_properties.json.

PRIVACY REQUIREMENTS:
- Scoped strictly by authenticated user_id.
- Properties are PRIVATE by default unless explicitly configured as public.
- Never conflated with official cadastral records or synthetic demo parcels.
"""

import json
import os
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE_DIR = ROOT / "data" / "governance"
PROPERTIES_FILE = GOVERNANCE_DIR / "user_properties.json"

class UserProperty(BaseModel):
    id: str = Field(default_factory=lambda: f"UPRO-BHOPAL-{uuid.uuid4().hex[:8].upper()}")
    user_id: str
    title: str = "My Property"
    house_number: Optional[str] = ""
    street_locality: Optional[str] = ""
    city: Optional[str] = "Bhopal"
    state: Optional[str] = "Madhya Pradesh"
    pincode: Optional[str] = ""
    property_type: str = "house"  # house, building, vacant_plot, other
    description: Optional[str] = ""
    latitude: float
    longitude: float
    accuracy_m: Optional[float] = None
    is_user_adjusted: bool = False
    is_public: bool = False
    show_name_publicly: bool = False
    show_address_publicly: bool = False
    show_phone_publicly: bool = False
    phone_number: Optional[str] = ""
    owner_name: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserPropertyStore:
    def __init__(self):
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.properties: Dict[str, UserProperty] = {}
        self._load()

    def _load(self):
        with self._lock:
            if PROPERTIES_FILE.exists():
                try:
                    with open(PROPERTIES_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for pid, item in data.get("properties", {}).items():
                            self.properties[pid] = UserProperty(**item)
                except Exception as e:
                    print(f"Warning: Failed to load user_properties.json: {e}")

    def _save(self):
        with self._lock:
            tmp_file = PROPERTIES_FILE.with_suffix(".tmp")
            try:
                payload = {pid: prop.model_dump() for pid, prop in self.properties.items()}
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump({"properties": payload}, f, indent=2)
                os.replace(tmp_file, PROPERTIES_FILE)
            except Exception as e:
                if tmp_file.exists():
                    os.remove(tmp_file)
                print(f"Warning: Failed to save user_properties.json: {e}")

    def get_user_properties(self, user_id: str) -> List[UserProperty]:
        """Fetch all registered properties for a specific user_id."""
        with self._lock:
            return [p for p in self.properties.values() if p.user_id == user_id]

    def get_property(self, property_id: str) -> Optional[UserProperty]:
        """Fetch property by ID."""
        with self._lock:
            return self.properties.get(property_id)

    def create_property(self, prop_data: UserProperty) -> UserProperty:
        """Create a new user property."""
        with self._lock:
            self.properties[prop_data.id] = prop_data
            self._save()
            return prop_data

    def update_property(self, property_id: str, user_id: str, update_dict: Dict[str, Any]) -> Optional[UserProperty]:
        """Update property owned by specified user_id."""
        with self._lock:
            existing = self.properties.get(property_id)
            if not existing or existing.user_id != user_id:
                return None

            now = datetime.now(timezone.utc).isoformat()
            updated_data = existing.model_dump()
            for key, val in update_dict.items():
                if key not in ("id", "user_id") and val is not None:
                    updated_data[key] = val

            updated_data["updated_at"] = now
            prop = UserProperty(**updated_data)
            self.properties[property_id] = prop
            self._save()
            return prop

    def delete_property(self, property_id: str, user_id: str) -> bool:
        """Delete property owned by specified user_id."""
        with self._lock:
            existing = self.properties.get(property_id)
            if not existing or existing.user_id != user_id:
                return False
            del self.properties[property_id]
            self._save()
            return True

    def get_public_properties(self) -> List[Dict[str, Any]]:
        """Fetch all public property markers with strict privacy redaction."""
        with self._lock:
            public_list = []
            for prop in self.properties.values():
                if prop.is_public:
                    item = {
                        "id": prop.id,
                        "title": prop.title if prop.show_name_publicly else "Registered User Property",
                        "property_type": prop.property_type,
                        "latitude": prop.latitude,
                        "longitude": prop.longitude,
                        "is_user_adjusted": prop.is_user_adjusted,
                        "owner_name": prop.owner_name if prop.show_name_publicly else None,
                        "house_number": prop.house_number if prop.show_address_publicly else None,
                        "street_locality": prop.street_locality if prop.show_address_publicly else None,
                        "phone_number": prop.phone_number if prop.show_phone_publicly else None,
                        "disclaimer": "User-Submitted Property Marker — Not Official Cadastral Boundary"
                    }
                    public_list.append(item)
            return public_list

    def list_all_admin(self) -> List[UserProperty]:
        """Fetch all user properties for administrative inventory inspection."""
        with self._lock:
            return list(self.properties.values())

user_property_store = UserPropertyStore()
