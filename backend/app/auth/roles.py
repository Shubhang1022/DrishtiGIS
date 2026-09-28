"""
Role-Based Access Control (RBAC) definitions and permission mappings for DrishtiGIS.
"""

from enum import Enum
from typing import Set, Dict

class UserRole(str, Enum):
    PUBLIC = "PUBLIC"
    SURVEYOR = "SURVEYOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"
    DATA_MANAGER = "DATA_MANAGER"

class Permission(str, Enum):
    # Public / Read Permissions
    VIEW_MAP = "VIEW_MAP"
    VIEW_PARCEL = "VIEW_PARCEL"
    VIEW_BUILDING = "VIEW_BUILDING"
    VIEW_ROAD = "VIEW_ROAD"
    VIEW_LANDUSE = "VIEW_LANDUSE"
    USE_AI_ASSISTANT = "USE_AI_ASSISTANT"
    
    # Surveyor Permissions
    CREATE_REVIEW = "CREATE_REVIEW"
    EDIT_REVIEW_GEOMETRY = "EDIT_REVIEW_GEOMETRY"
    SUBMIT_FIELD_VERIFICATION = "SUBMIT_FIELD_VERIFICATION"
    
    # Reviewer / Approval Permissions
    APPROVE_REVIEW = "APPROVE_REVIEW"
    REJECT_REVIEW = "REJECT_REVIEW"
    
    # Export & Report Permissions
    EXPORT_DATA = "EXPORT_DATA"
    EXPORT_REPORT = "EXPORT_REPORT"
    
    # Data Management & Admin Permissions
    UPLOAD_DATASET = "UPLOAD_DATASET"
    PROCESS_DATASET = "PROCESS_DATASET"
    PUBLISH_DATASET = "PUBLISH_DATASET"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_REGIONS = "MANAGE_REGIONS"
    MANAGE_DATASETS = "MANAGE_DATASETS"
    VIEW_AUDIT_LOG = "VIEW_AUDIT_LOG"

ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.PUBLIC: {
        Permission.VIEW_MAP,
        Permission.VIEW_PARCEL,
        Permission.VIEW_BUILDING,
        Permission.VIEW_ROAD,
        Permission.VIEW_LANDUSE,
        Permission.USE_AI_ASSISTANT,
        Permission.EXPORT_REPORT,
    },
    UserRole.SURVEYOR: {
        Permission.VIEW_MAP,
        Permission.VIEW_PARCEL,
        Permission.VIEW_BUILDING,
        Permission.VIEW_ROAD,
        Permission.VIEW_LANDUSE,
        Permission.USE_AI_ASSISTANT,
        Permission.CREATE_REVIEW,
        Permission.EDIT_REVIEW_GEOMETRY,
        Permission.SUBMIT_FIELD_VERIFICATION,
        Permission.EXPORT_DATA,
        Permission.EXPORT_REPORT,
    },
    UserRole.REVIEWER: {
        Permission.VIEW_MAP,
        Permission.VIEW_PARCEL,
        Permission.VIEW_BUILDING,
        Permission.VIEW_ROAD,
        Permission.VIEW_LANDUSE,
        Permission.USE_AI_ASSISTANT,
        Permission.CREATE_REVIEW,
        Permission.EDIT_REVIEW_GEOMETRY,
        Permission.SUBMIT_FIELD_VERIFICATION,
        Permission.APPROVE_REVIEW,
        Permission.REJECT_REVIEW,
        Permission.EXPORT_DATA,
        Permission.EXPORT_REPORT,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.DATA_MANAGER: {
        Permission.VIEW_MAP,
        Permission.VIEW_PARCEL,
        Permission.VIEW_BUILDING,
        Permission.VIEW_ROAD,
        Permission.VIEW_LANDUSE,
        Permission.USE_AI_ASSISTANT,
        Permission.EXPORT_DATA,
        Permission.EXPORT_REPORT,
        Permission.UPLOAD_DATASET,
        Permission.PROCESS_DATASET,
        Permission.PUBLISH_DATASET,
        Permission.MANAGE_DATASETS,
        Permission.MANAGE_REGIONS,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.ADMIN: set(Permission)  # All permissions
}

def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role possesses a specific permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms
