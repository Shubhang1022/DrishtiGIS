/**
 * DrishtiGIS — Roads & Access Corridors API Client
 * ==================================================
 * Typed client functions for querying road features and parcel access corridor analysis.
 */

import { apiFetch } from "./client";

export interface RoadFeature {
  road_id: string;
  dataset_id: string;
  region_id: string;
  city: string;
  state: string;
  country: string;
  crs: string;
  source: string;
  source_type: "REFERENCE_GIS" | "AI_DERIVED" | "OFFICIAL_REFERENCE" | "SYNTHETIC_TEST" | "TEST_FIXTURE";
  road_class: "PRIMARY" | "SECONDARY" | "LOCAL" | "ACCESS" | "PATHWAY" | "UNKNOWN";
  name?: string;
  surface_type: string;
  estimated_width_m?: number;
  length_m: number;
  confidence?: number;
  acquisition_datetime?: string;
  geometry_geojson?: any;
  review_status: string;
  disclaimer: string;
}

export interface AccessCorridorSummary {
  parcel_id: string;
  dataset_id: string;
  region_id: string;
  access_status: "ACCESS_DETECTED" | "NO_DETECTED_ACCESS_CORRIDOR" | "ACCESS_REVIEW_REQUIRED";
  has_direct_access: boolean;
  nearest_road_id?: string;
  nearest_road_name?: string;
  nearest_road_class?: string;
  distance_to_road_m: number;
  nearby_road_count: number;
  disclaimer: string;
}

export async function fetchRoads(city?: string, roadClass?: string): Promise<RoadFeature[]> {
  const params = new URLSearchParams();
  if (city) params.append("city", city);
  if (roadClass) params.append("road_class", roadClass);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<RoadFeature[]>(`/api/v1/roads${query}`);
}

export async function fetchRoadDetail(roadId: string): Promise<RoadFeature> {
  return apiFetch<RoadFeature>(`/api/v1/roads/${encodeURIComponent(roadId)}`);
}

export async function fetchParcelAccess(parcelId: string): Promise<AccessCorridorSummary> {
  return apiFetch<AccessCorridorSummary>(`/api/v1/roads/access/${encodeURIComponent(parcelId)}`);
}
