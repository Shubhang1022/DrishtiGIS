/**
 * DrishtiGIS — Land-Use Intelligence API Client
 * ================================================
 * Typed client functions for querying land-use polygons and observed parcel land-use pattern analysis.
 */

import { apiFetch } from "./client";

export interface LandUseFeature {
  landuse_id: string;
  dataset_id: string;
  region_id: string;
  city: string;
  state: string;
  country: string;
  crs: string;
  source: string;
  source_type: "AI_DERIVED" | "REFERENCE_GIS" | "OFFICIAL_REFERENCE" | "SYNTHETIC_TEST" | "TEST_FIXTURE";
  classification: "RESIDENTIAL" | "COMMERCIAL" | "MIXED_USE" | "INSTITUTIONAL" | "OPEN_AREA" | "INDUSTRIAL" | "VEGETATION" | "WATER" | "UNKNOWN";
  area_m2: number;
  confidence?: number;
  evidence: string;
  acquisition_datetime?: string;
  geometry_geojson?: any;
  review_status: string;
  disclaimer: string;
}

export interface ParcelLandUseSummary {
  parcel_id: string;
  dataset_id: string;
  region_id: string;
  observed_land_use_pattern: string;
  source_type: string;
  confidence: number;
  building_density_ratio: number;
  overlapping_landuse_id?: string;
  disclaimer: string;
}

export async function fetchLandUseFeatures(city?: string, classification?: string): Promise<LandUseFeature[]> {
  const params = new URLSearchParams();
  if (city) params.append("city", city);
  if (classification) params.append("classification", classification);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<LandUseFeature[]>(`/api/v1/landuse${query}`);
}

export async function fetchLandUseDetail(landuseId: string): Promise<LandUseFeature> {
  return apiFetch<LandUseFeature>(`/api/v1/landuse/${encodeURIComponent(landuseId)}`);
}

export async function fetchParcelLandUse(parcelId: string): Promise<ParcelLandUseSummary> {
  return apiFetch<ParcelLandUseSummary>(`/api/v1/landuse/parcel/${encodeURIComponent(parcelId)}`);
}
