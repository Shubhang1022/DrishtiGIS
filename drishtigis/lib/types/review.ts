export type ReviewStatus =
  | 'OPEN'
  | 'IN_REVIEW'
  | 'FIELD_VERIFICATION_REQUIRED'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'RESOLVED';

export type ReviewIssueType =
  | 'BUILDING_CROSSES_PARCEL_BOUNDARY'
  | 'MULTIPLE_BUILDINGS_IN_PARCEL'
  | 'NO_PARCEL_MATCH'
  | 'ACCESS_REVIEW_REQUIRED'
  | 'NO_DETECTED_ACCESS_CORRIDOR'
  | 'LAND_USE_REVIEW'
  | 'HISTORICAL_CHANGE_REVIEW'
  | 'INVALID_OR_INCONSISTENT_GEOMETRY'
  | 'OTHER_REVIEW';

export type ReviewSeverity = 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type VerificationMethod =
  | 'ON_SITE'
  | 'GNSS'
  | 'CORS'
  | 'SURVEY_RECORD'
  | 'FIELD_PHOTO'
  | 'AUTHORITY_RECORD'
  | 'OTHER';

export type ReviewSource =
  | 'AI_DERIVED_UAVPAL'
  | 'REFERENCE_GIS'
  | 'SYNTHETIC_DEMO'
  | 'REVIEWED_AI_GEOMETRY'
  | 'FIELD_VERIFIED'
  | 'TEST_FIXTURE';

export interface ReviewAuditTrail {
  audit_id: string;
  review_id: string;
  action: string;
  previous_status: ReviewStatus;
  new_status: ReviewStatus;
  reviewer: string;
  timestamp: string;
  notes?: string | null;
  geometry_changed: boolean;
  evidence_reference?: Record<string, any> | null;
}

export interface FieldVerificationRecord {
  verification_id: string;
  review_id: string;
  location?: { latitude: number; longitude: number } | null;
  verification_method: VerificationMethod;
  observed_feature: string;
  observation: string;
  timestamp: string;
  reviewer: string;
  notes?: string | null;
  evidence_reference?: Record<string, any> | null;
  photo_filename?: string | null;
}

export interface ReviewItem {
  review_id: string;
  entity_type: string;
  entity_id: string;
  parcel_id?: string | null;
  region_id: string;
  dataset_id: string;
  epoch_id?: string | null;
  country: string;
  state: string;
  city: string;
  issue_type: ReviewIssueType;
  source: ReviewSource;
  severity: ReviewSeverity;
  status: ReviewStatus;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
  reviewer_notes?: string | null;
  evidence: Record<string, any>;
  original_geometry?: any | null;
  reviewed_geometry?: any | null;
  before_geometry?: any | null;
  after_geometry?: any | null;
  geometry_changed: boolean;
  verification_method?: VerificationMethod | null;
  verification_timestamp?: string | null;
  verification_status?: string | null;
}

export interface ReviewStats {
  total_issues: number;
  open: number;
  in_review: number;
  field_verification_required: number;
  accepted: number;
  rejected: number;
  resolved: number;
  geometry_adjustments: number;
  field_verified: number;
  ai_accepted: number;
  ai_rejected: number;
}
