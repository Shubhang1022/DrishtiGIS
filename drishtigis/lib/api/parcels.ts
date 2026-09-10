/**
 * DrishtiGIS — Parcel API Client
 * ================================
 * Typed wrappers for parcel endpoints.
 * All responses carry _source: DEMO_DATA_PROTOTYPE_ONLY.
 */

import { apiFetch } from "./client";

export interface ParcelListResponse {
  type:            "FeatureCollection";
  total:           number;
  features:        GeoJSON.Feature[];
  _source:         string;
  _disclaimer:     string;
  _coverage_note?: string;
}

export interface ParcelDetailResponse {
  parcel:          GeoJSON.Feature | null;
  property:        Record<string, unknown> | null;
  discrepancies:   unknown[];
  ai_features:     GeoJSON.Feature[];
  _source:         string;
  _disclaimer:     string;
}

export async function fetchParcels(city: string): Promise<ParcelListResponse> {
  return apiFetch<ParcelListResponse>(
    `/api/v1/parcels?city=${encodeURIComponent(city)}`
  );
}

export async function fetchParcel(
  propertyId: string
): Promise<ParcelDetailResponse> {
  return apiFetch<ParcelDetailResponse>(
    `/api/v1/parcels/${encodeURIComponent(propertyId)}`
  );
}
