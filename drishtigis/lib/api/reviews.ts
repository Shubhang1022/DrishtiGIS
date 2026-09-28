/**
 * DrishtiGIS — Surveyor Review API Client
 * =========================================
 * Typed wrappers for review queue, audit trail, geometry editing,
 * field verification, and GIS export endpoints.
 */

import { apiFetch } from "./client";
import type {
  ReviewItem,
  ReviewAuditTrail,
  FieldVerificationRecord,
  ReviewStats,
  ReviewStatus,
  ReviewIssueType,
  ReviewSeverity,
  VerificationMethod,
} from "@/lib/types/review";

export interface ReviewListResponse {
  total: number;
  items: ReviewItem[];
  _disclaimer: string;
}

export interface ReviewDetailResponse {
  item: ReviewItem;
  audit_trail: ReviewAuditTrail[];
  field_verifications: FieldVerificationRecord[];
  _disclaimer: string;
}

export interface GeometryEditResponse {
  item: ReviewItem;
  recomputed_spatial_relationships: Record<string, any>;
  message: string;
}

/**
 * Fetch review items matching filters.
 */
export async function getReviewQueue(params?: {
  status?: ReviewStatus;
  issue_type?: ReviewIssueType;
  severity?: ReviewSeverity;
  city?: string;
  assigned_to?: string;
}): Promise<ReviewListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.issue_type) query.set("issue_type", params.issue_type);
  if (params?.severity) query.set("severity", params.severity);
  if (params?.city) query.set("city", params.city);
  if (params?.assigned_to) query.set("assigned_to", params.assigned_to);

  const url = `/api/v1/reviews${query.toString() ? `?${query.toString()}` : ""}`;
  return apiFetch<ReviewListResponse>(url);
}

/**
 * Fetch review queue statistics.
 */
export async function getReviewStats(): Promise<ReviewStats> {
  return apiFetch<ReviewStats>("/api/v1/reviews/stats");
}

/**
 * Fetch single review item by ID.
 */
export async function getReviewDetail(reviewId: string): Promise<ReviewDetailResponse> {
  return apiFetch<ReviewDetailResponse>(`/api/v1/reviews/${reviewId}`);
}

/**
 * Update review item status and append audit log.
 */
export async function updateReviewStatus(
  reviewId: string,
  status: ReviewStatus,
  reviewer: string = "Surveyor",
  notes?: string
): Promise<{ item: ReviewItem }> {
  return apiFetch<{ item: ReviewItem }>(`/api/v1/reviews/${reviewId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, reviewer, notes }),
  });
}

/**
 * Submit edited geometry for a review item.
 */
export async function submitGeometryEdit(
  reviewId: string,
  geometry: any,
  reviewer: string = "Surveyor",
  notes?: string
): Promise<GeometryEditResponse> {
  return apiFetch<GeometryEditResponse>(`/api/v1/reviews/${reviewId}/geometry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ geometry, reviewer, notes }),
  });
}

/**
 * Record a field verification observation.
 */
export async function recordFieldVerification(
  reviewId: string,
  verification: {
    verification_method: VerificationMethod;
    observed_feature: string;
    observation: string;
    reviewer?: string;
    notes?: string;
    location?: { latitude: number; longitude: number };
    photo_filename?: string;
  }
): Promise<{ verification: FieldVerificationRecord; status: string }> {
  return apiFetch<{ verification: FieldVerificationRecord; status: string }>(
    `/api/v1/reviews/${reviewId}/verify`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewer: "Surveyor", ...verification }),
    }
  );
}

/**
 * Export reviewed features as GeoJSON.
 */
export async function exportReviewedGeoJSON(city?: string): Promise<GeoJSON.FeatureCollection> {
  const url = city ? `/api/v1/reviews/export?city=${encodeURIComponent(city)}` : "/api/v1/reviews/export";
  return apiFetch<GeoJSON.FeatureCollection>(url);
}
