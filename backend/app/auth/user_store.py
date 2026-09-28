"""
User Store and Region Governance Service for DrishtiGIS.
Persists users to data/governance/users.json with pre-seeded development demo accounts.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.app.auth.user_model import User, UserRole, UserCreate, UserResponse, UserUpdate
from backend.app.auth.auth_service import hash_password
from backend.app.core.config import settings

ROOT = Path(__file__).resolve().parents[4]
GOVERNANCE_DIR = ROOT / "data" / "governance"
USERS_FILE = GOVERNANCE_DIR / "users.json"
REGIONS_FILE = GOVERNANCE_DIR / "regions.json"

class UserStore:
    def __init__(self):
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        self.users: Dict[str, User] = {}
        self.regions: List[Dict[str, Any]] = []
        self._load_users()
        self._load_regions()

    def _load_users(self):
        if USERS_FILE.exists():
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("users", []):
                        u = User(**item)
                        self.users[u.email.lower()] = u
            except Exception as e:
                print(f"Warning: Failed to load users.json: {e}")

        if not self.users:
            self._seed_default_users()

        # In production environments with ENABLE_DEMO_ACCOUNTS=False, deactivate demo accounts
        if not settings.ENABLE_DEMO_ACCOUNTS:
            for email, u in self.users.items():
                if email.startswith("demo-"):
                    u.is_active = False

    def _seed_default_users(self):
        """Seed default role accounts for SIH26012 evaluation."""
        if not settings.ENABLE_DEMO_ACCOUNTS:
            return
        now = datetime.now(timezone.utc).isoformat()
        seeds = [
            User(
                user_id="usr-public-001",
                email="demo-public@drishtigis.in",
                name="Public Citizen User",
                hashed_password=hash_password("Public123!"),
                role=UserRole.PUBLIC,
                organization="General Public",
                country="India",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="bhopal_mp",
                allowed_datasets=["uavpal_bhopal", "bhopal_synthetic_parcels"],
                is_active=True,
                created_at=now
            ),
            User(
                user_id="usr-surveyor-001",
                email="demo-surveyor@drishtigis.in",
                name="Vikram Singh (Surveyor)",
                hashed_password=hash_password("Surveyor123!"),
                role=UserRole.SURVEYOR,
                organization="State Survey Department",
                country="India",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="bhopal_mp",
                allowed_datasets=["uavpal_bhopal", "bhopal_synthetic_parcels"],
                is_active=True,
                created_at=now
            ),
            User(
                user_id="usr-reviewer-001",
                email="demo-reviewer@drishtigis.in",
                name="Ananya Sharma (Reviewer)",
                hashed_password=hash_password("Reviewer123!"),
                role=UserRole.REVIEWER,
                organization="Department of Land Resources",
                country="India",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="bhopal_mp",
                allowed_datasets=["uavpal_bhopal", "bhopal_synthetic_parcels"],
                is_active=True,
                created_at=now
            ),
            User(
                user_id="usr-admin-001",
                email="demo-admin@drishtigis.in",
                name="DrishtiGIS System Administrator",
                hashed_password=hash_password("Admin123!"),
                role=UserRole.ADMIN,
                organization="Ministry of Rural Development / MoRD",
                country="India",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="*",
                allowed_datasets=["*"],
                is_active=True,
                created_at=now
            ),
        ]
        for u in seeds:
            self.users[u.email.lower()] = u
        self._save_users()

    def _save_users(self):
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                payload = [u.model_dump() for u in self.users.values()]
                json.dump({"users": payload}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save users: {e}")

    def _load_regions(self):
        if REGIONS_FILE.exists():
            try:
                with open(REGIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.regions = data.get("regions", [])
            except Exception:
                pass

        if not self.regions:
            self.regions = [
                {
                    "region_id": "bhopal_mp",
                    "name": "Bhopal Prototype Region",
                    "city": "Bhopal",
                    "state": "Madhya Pradesh",
                    "country": "India",
                    "status": "ACTIVE",
                    "dataset_count": 3,
                    "bounding_box": [77.35, 23.20, 77.45, 23.30]
                },
                {
                    "region_id": "lucknow_up",
                    "name": "Lucknow Demonstration Region",
                    "city": "Lucknow",
                    "state": "Uttar Pradesh",
                    "country": "India",
                    "status": "ACTIVE",
                    "dataset_count": 1,
                    "bounding_box": [80.85, 26.80, 80.95, 26.90]
                }
            ]
            self._save_regions()

    def _save_regions(self):
        try:
            with open(REGIONS_FILE, "w", encoding="utf-8") as f:
                json.dump({"regions": self.regions}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save regions: {e}")

    def get_by_email(self, email: str) -> Optional[User]:
        return self.users.get(email.lower().strip())

    def get_by_id(self, user_id: str) -> Optional[User]:
        return next((u for u in self.users.values() if u.user_id == user_id), None)

    def create_user(self, create_req: UserCreate) -> User:
        email = create_req.email.lower().strip()
        if email in self.users:
            raise ValueError(f"User with email '{email}' already exists.")

        now = datetime.now(timezone.utc).isoformat()
        u = User(
            user_id=f"usr-{uuid.uuid4().hex[:8]}",
            email=email,
            name=create_req.name,
            hashed_password=hash_password(create_req.password),
            role=create_req.role,
            organization=create_req.organization or "DrishtiGIS Organization",
            country=create_req.country or "India",
            state=create_req.state or "Madhya Pradesh",
            city=create_req.city or "Bhopal",
            region_id=create_req.region_id or "bhopal_mp",
            allowed_datasets=["uavpal_bhopal", "bhopal_synthetic_parcels"],
            is_active=True,
            created_at=now,
            updated_at=now
        )
        self.users[email] = u
        self._save_users()
        return u

    def update_user(self, user_id: str, update_req: UserUpdate) -> Optional[User]:
        u = self.get_by_id(user_id)
        if not u:
            return None

        if update_req.name is not None:
            u.name = update_req.name
        if update_req.role is not None:
            u.role = update_req.role
        if update_req.organization is not None:
            u.organization = update_req.organization
        if update_req.state is not None:
            u.state = update_req.state
        if update_req.city is not None:
            u.city = update_req.city
        if update_req.region_id is not None:
            u.region_id = update_req.region_id
        if update_req.allowed_datasets is not None:
            u.allowed_datasets = update_req.allowed_datasets
        if update_req.is_active is not None:
            u.is_active = update_req.is_active

        u.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_users()
        return u

    def list_users(self) -> List[UserResponse]:
        return [
            UserResponse(
                user_id=u.user_id,
                email=u.email,
                name=u.name,
                role=u.role,
                organization=u.organization,
                country=u.country,
                state=u.state,
                city=u.city,
                region_id=u.region_id,
                allowed_datasets=u.allowed_datasets,
                is_active=u.is_active,
                created_at=u.created_at,
                last_login=u.last_login
            )
            for u in self.users.values()
        ]

    def add_region(self, region_data: Dict[str, Any]) -> Dict[str, Any]:
        self.regions.append(region_data)
        self._save_regions()
        return region_data

user_store = UserStore()
