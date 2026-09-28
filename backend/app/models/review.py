"""
DrishtiGIS — Review, Field Verification & Audit Trail Data Models
===================================================================
Phase 8: Surveyor Review, Ground-Truthing & Cadastral Geometry Editing
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    FIELD_VERIFICATION_REQUIRED = "FIELD_VERIFICATION_REQUIRED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class ReviewIssueType(str, Enum):
    BUILDING_CROSSES_PARCEL_BOUNDARY = "BUILDING_CROSSES_PARCEL_BOUNDARY"
    MULTIPLE_BUILDINGS_IN_PARCEL = "MULTIPLE_BUILDINGS_IN_PARCEL"
    NO_PARCEL_MATCH = "NO_PARCEL_MATCH"
    ACCESS_REVIEW_REQUIRED = "ACCESS_REVIEW_REQUIRED"
    NO_DETECTED_ACCESS_CORRIDOR = "NO_DETECTED_ACCESS_CORRIDOR"
    LAND_USE_REVIEW = "LAND_USE_REVIEW"
    HISTORICAL_CHANGE_REVIEW = "HISTORICAL_CHANGE_REVIEW"
    INVALID_OR_INCONSISTENT_GEOMETRY = "INVALID_OR_INCONSISTENT_GEOMETRY"
    OTHER_REVIEW = "OTHER_REVIEW"


class ReviewSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class VerificationMethod(str, Enum):
    ON_SITE = "ON_SITE"
    GNSS = "GNSS"
    CORS = "CORS"
    SURVEY_RECORD = "SURVEY_RECORD"
    FIELD_PHOTO = "FIELD_PHOTO"
    AUTHORITY_RECORD = "AUTHORITY_RECORD"
    OTHER = "OTHER"


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    SURVEYOR = "SURVEYOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class ReviewSource(str, Enum):
    AI_DERIVED_UAVPAL = "AI_DERIVED_UAVPAL"
    REFERENCE_GIS = "REFERENCE_GIS"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"
    REVIEWED_AI_GEOMETRY = "REVIEWED_AI_GEOMETRY"
    FIELD_VERIFIED = "FIELD_VERIFIED"
    TEST_FIXTURE = "TEST_FIXTURE"


class ReviewAuditTrail(BaseModel):
    audit_id: str
    review_id: str
    action: str  # STATUS_CHANGE, GEOMETRY_EDITED, NOTE_ADDED, FIELD_VERIFICATION_RECORDED
    previous_status: ReviewStatus
    new_status: ReviewStatus
    reviewer: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None
    geometry_changed: bool = False
    evidence_reference: Optional[Dict[str, Any]] = None


class FieldVerificationRecord(BaseModel):
    verification_id: str
    review_id: str
    location: Optional[Dict[str, float]] = None  # {latitude, longitude}
    verification_method: VerificationMethod
    observed_feature: str  # Observed boundary, Observed building, Observed access, etc.
    observation: str  # Neutral observation text
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewer: str
    notes: Optional[str] = None
    evidence_reference: Optional[Dict[str, Any]] = None
    photo_filename: Optional[str] = None


class ReviewItem(BaseModel):
    review_id: str
    entity_type: str  # PARCEL, AI_BUILDING, DISCREPANCY, ACCESS_CORRIDOR, LAND_USE
    entity_id: str
    parcel_id: Optional[str] = None
    region_id: str = "REGION-BPL-01"
    dataset_id: str = "DATASET-BHOPAL-UAV"
    epoch_id: Optional[str] = "EPOCH-BPL-2024-01"
    country: str = "India"
    state: str = "Madhya Pradesh"
    city: str = "Bhopal"
    issue_type: ReviewIssueType
    source: ReviewSource = ReviewSource.AI_DERIVED_UAVPAL
    severity: ReviewSeverity = ReviewSeverity.MEDIUM
    status: ReviewStatus = ReviewStatus.OPEN
    assigned_to: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewer_notes: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    original_geometry: Optional[Dict[str, Any]] = None
    reviewed_geometry: Optional[Dict[str, Any]] = None
    before_geometry: Optional[Dict[str, Any]] = None
    after_geometry: Optional[Dict[str, Any]] = None
    geometry_changed: bool = False
    verification_method: Optional[VerificationMethod] = None
    verification_timestamp: Optional[str] = None
    verification_status: Optional[str] = None


class ReviewStats(BaseModel):
    total_issues: int = 0
    open: int = 0
    in_review: int = 0
    field_verification_required: int = 0
    accepted: int = 0
    rejected: int = 0
    resolved: int = 0
    geometry_adjustments: int = 0
    field_verified: int = 0
    ai_accepted: int = 0
    ai_rejected: int = 0
