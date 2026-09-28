/**
 * DrishtiGIS — Historical / Multi-Epoch API Client
 * ==================================================
 * Typed client functions for fetching capture epochs and temporal comparison results.
 */

import { apiFetch } from "./client";

export interface EpochMetadata {
  epoch_id: string;
  dataset_id: string;
  region_id: string;
  city: string;
  state: string;
  crs: string;
  acquisition_datetime: string;
  resolution_m: number;
  source_type: string;
  description?: string;
  building_count: number;
  is_baseline: boolean;
}

export interface BuildingChangeItem {
  change_id: string;
  change_type: "ADDED" | "REMOVED" | "MODIFIED" | "UNCHANGED";
  baseline_building_id?: string;
  target_building_id?: string;
  parcel_id?: string;
  area_baseline_m2?: number;
  area_target_m2?: number;
  area_delta_m2: number;
  iou_score: number;
  centroid_shift_m: number;
  confidence_score: number;
  geometry_geojson?: any;
  review_status: "UNREVIEWED" | "VERIFIED_CHANGE" | "DISCREPANCY_FLAGGED" | "REJECTED";
  disclaimer: string;
}

export interface ParcelChangeSummary {
  parcel_id: string;
  baseline_epoch_id: string;
  target_epoch_id: string;
  baseline_building_count: number;
  target_building_count: number;
  added_count: number;
  removed_count: number;
  modified_count: number;
  unchanged_count: number;
  total_area_change_m2: number;
  changes: BuildingChangeItem[];
  last_evaluated_at: string;
}

export async function fetchEpochs(city?: string): Promise<EpochMetadata[]> {
  const query = city ? `?city=${encodeURIComponent(city)}` : "";
  return apiFetch<EpochMetadata[]>(`/api/v1/historical/epochs${query}`);
}

export async function fetchHistoricalComparison(
  parcelId: string,
  baselineEpochId: string = "EPOCH-BPL-2024-01",
  targetEpochId: string = "EPOCH-BPL-2025-06"
): Promise<ParcelChangeSummary> {
  const params = new URLSearchParams({
    parcel_id: parcelId,
    baseline_epoch_id: baselineEpochId,
    target_epoch_id: targetEpochId,
  });
  return apiFetch<ParcelChangeSummary>(`/api/v1/historical/compare?${params.toString()}`);
}
