/**
 * DrishtiGIS — Parcel + AI Features + Synthetic Parcel API Client
 * ================================================================
 * Typed wrappers for parcel, synthetic parcel, and AI building endpoints.
 *
 * Phase 5.5: ParcelDetailResponse now covers both synthetic (DRS-BPL-DEMO-XXX)
 * and legacy demo (DRS-BPL-00101) parcels.
 */

import { apiFetch } from "./client";
import type {
  AIBuildingAnalysis,
  AIFeaturesResponse,
  RealAIBuildingProperties,
  SyntheticParcelProperties,
} from "@/lib/demo-data/types";

export interface ParcelListResponse {
  type:             "FeatureCollection";
  total:            number;
  /** Features may be SyntheticParcelProperties (Phase 5.5) or legacy demo properties */
  features:         GeoJSON.Feature<GeoJSON.Polygon, SyntheticParcelProperties | Record<string, unknown>>[];
  _source:          string;
  _disclaimer:      string;
  _coverage_note?:  string;
}

export interface ParcelDetailResponse {
  parcel:          GeoJSON.Feature | null;
  property:        Record<string, unknown> | null;
  /** Real AI buildings with parcel associations (Phase 5) */
  ai_features:     GeoJSON.Feature<GeoJSON.Polygon, RealAIBuildingProperties>[];
  /** Structured AI analysis sub-object (Phase 5) */
  ai_analysis:     AIBuildingAnalysis | null;
  /** Real geometric discrepancy records (Phase 5) */
  discrepancies:   unknown[];
  _source:         string;
  _ai_source?:     string;
  _disclaimer:     string;
}

// ── Parcel endpoints ─────────────────────────────────────────────────────────

export async function fetchParcels(
  city: string,
  token?: string | null
): Promise<ParcelListResponse> {
  return apiFetch<ParcelListResponse>(
    `/api/v1/parcels?city=${encodeURIComponent(city)}`,
    token !== undefined ? { token } : undefined
  );
}

export async function fetchParcel(
  propertyId: string,
  token?: string | null
): Promise<ParcelDetailResponse> {
  return apiFetch<ParcelDetailResponse>(
    `/api/v1/parcels/${encodeURIComponent(propertyId)}`,
    token !== undefined ? { token } : undefined
  );
}

// ── AI building endpoints ─────────────────────────────────────────────────────

export interface FetchAIBuildingsOptions {
  /** Filter by primary_parcel_id */
  parcelId?:  string;
  /** Filter by city — only "bhopal" has real data */
  city?:      string;
  /** Filter by source_tile (e.g. "00_10") */
  tile?:      string;
}

/**
 * Fetch real AI-derived building footprints.
 * Returns all 834 buildings when no filter is applied.
 * Returns empty FeatureCollection with ai_available: false for non-Bhopal cities.
 */
export async function fetchAIBuildings(
  options: FetchAIBuildingsOptions = {}
): Promise<AIFeaturesResponse> {
  const params = new URLSearchParams();
  if (options.parcelId) params.set("parcel_id", options.parcelId);
  if (options.city)     params.set("city",      options.city);
  if (options.tile)     params.set("tile",       options.tile);

  const qs = params.toString();
  return apiFetch<AIFeaturesResponse>(
    `/api/v1/features${qs ? `?${qs}` : ""}`
  );
}

// ── Synthetic parcel helpers ──────────────────────────────────────────────────

/**
 * Fetch synthetic demo parcels for Bhopal.
 * Equivalent to fetchParcels("Bhopal") but explicitly typed for synthetic data.
 */
export async function fetchSyntheticParcels(): Promise<ParcelListResponse> {
  return apiFetch<ParcelListResponse>("/api/v1/parcels?city=Bhopal");
}

export type { SyntheticParcelProperties };
