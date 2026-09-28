import { API_BASE, ApiError } from "./client";

export interface DatasetItemData {
  dataset_id: string;
  job_id: string;
  name: string;
  filename: string;
  format: string;
  file_size_bytes: number;
  file_path?: string;
  state: string;
  city: string;
  region_id: string;
  uploaded_by: string;
  uploaded_at: string;
  processing_started_at?: string | null;
  last_updated_at: string;
  completed_at?: string | null;
  status: string;
  current_stage: string;
  progress_percent: number;
  completed_steps: string[];
  pending_steps: string[];
  failed_steps: string[];
  error_details?: string | null;
  crs?: string | null;
  bounds?: number[] | null;
  dimensions?: string | null;
  spatial_resolution_m?: number | null;
  feature_count?: number | null;
  layer_names: string[];
  outputs: Array<{ name: string; type: string; url: string }>;
  is_published: boolean;
  retry_eligible: boolean;
}

export interface DatasetUploadResponse {
  status: string;
  message: string;
  dataset_id: string;
  job_id: string;
  filename: string;
  size_bytes: number;
  max_allowed_mb: number;
  region_id: string;
  dataset?: DatasetItemData;
}

export interface AnalyticsSummaryData {
  total_datasets: number;
  active_processing_jobs: number;
  completed_datasets: number;
  failed_jobs: number;
  qa_required_count: number;
  published_datasets: number;
  total_ingested_size_bytes: number;
  total_mapped_features: number;
  by_status: Record<string, number>;
  by_format: Record<string, number>;
  by_region: Record<string, number>;
  last_refreshed_at: string;
}

export interface AdminPropertyItem {
  property_id: string;
  plot_number: string;
  survey_number: string;
  property_type: string;
  region_id: string;
  city: string;
  state: string;
  parcel_area_m2: number;
  owner_name: string;
  previous_owner_name: string;
  resident_count?: number | null;
  purchase_price_inr?: number | null;
  estimated_selling_price_inr?: number | null;
  ai_building_count: number;
  ai_detected_area_m2: number;
  coverage_ratio: number;
  discrepancy_count: number;
  review_status: string;
  data_source: string;
  disclaimer: string;
}

export async function uploadDataset(
  file: File,
  datasetName?: string,
  regionId: string = "bhopal_mp",
  stateName: string = "Madhya Pradesh",
  cityName: string = "Bhopal",
  datasetType: string = "uav_raster"
): Promise<DatasetUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (datasetName) formData.append("dataset_name", datasetName);
  formData.append("region_id", regionId);
  formData.append("state_name", stateName);
  formData.append("city_name", cityName);
  formData.append("dataset_type", datasetType);

  const res = await fetch(`${API_BASE}/api/v1/admin/datasets/upload`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    let detail = `Upload failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) detail = errorJson.detail;
    } catch (_) {}
    throw new ApiError(res.status, detail);
  }

  return res.json();
}

export async function listDatasets(params?: {
  status?: string;
  region_id?: string;
  format_type?: string;
  search?: string;
  sort_by?: string;
  ascending?: boolean;
}): Promise<{ total: number; datasets: DatasetItemData[] }> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.region_id) query.set("region_id", params.region_id);
  if (params?.format_type) query.set("format_type", params.format_type);
  if (params?.search) query.set("search", params.search);
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.ascending !== undefined) query.set("ascending", String(params.ascending));

  const res = await fetch(`${API_BASE}/api/v1/admin/datasets?${query.toString()}`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, "Failed to list datasets");
  }

  return res.json();
}

export async function getDatasetDetail(datasetId: string): Promise<DatasetItemData> {
  const res = await fetch(`${API_BASE}/api/v1/admin/datasets/${encodeURIComponent(datasetId)}`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, `Failed to fetch dataset ${datasetId}`);
  }

  return res.json();
}

export async function retryDatasetJob(datasetId: string): Promise<DatasetItemData> {
  const res = await fetch(`${API_BASE}/api/v1/admin/datasets/${encodeURIComponent(datasetId)}/retry`, {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, `Failed to retry dataset ${datasetId}`);
  }

  const data = await res.json();
  return data.dataset;
}

export async function cancelDatasetJob(datasetId: string): Promise<DatasetItemData> {
  const res = await fetch(`${API_BASE}/api/v1/admin/datasets/${encodeURIComponent(datasetId)}/cancel`, {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, `Failed to cancel dataset ${datasetId}`);
  }

  const data = await res.json();
  return data.dataset;
}

export async function publishDataset(datasetId: string): Promise<DatasetItemData> {
  const res = await fetch(`${API_BASE}/api/v1/admin/datasets/${encodeURIComponent(datasetId)}/publish`, {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, `Failed to publish dataset ${datasetId}`);
  }

  const data = await res.json();
  return data.dataset;
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummaryData> {
  const res = await fetch(`${API_BASE}/api/v1/admin/analytics/summary`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, "Failed to fetch analytics summary");
  }

  return res.json();
}

export async function fetchAdminProperties(params?: {
  search?: string;
  property_type?: string;
  region_id?: string;
}): Promise<{ total: number; properties: AdminPropertyItem[] }> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.property_type) query.set("property_type", params.property_type);
  if (params?.region_id) query.set("region_id", params.region_id);

  const res = await fetch(`${API_BASE}/api/v1/admin/properties?${query.toString()}`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new ApiError(res.status, "Failed to fetch admin property intelligence");
  }

  return res.json();
}

export interface PublishedDatasetItem {
  dataset_id: string;
  name: string;
  filename: string;
  format: string;
  state: string;
  city: string;
  region_id: string;
  crs: string;
  bounds: [number, number, number, number];
  minzoom: number;
  maxzoom: number;
  tilejson_url: string;
  tiles_url: string;
  uploaded_at: string;
  last_updated_at: string;
  is_published: boolean;
  feature_count: number;
  outputs: Array<{ name: string; type: string; url: string }>;
}

export async function fetchPublishedDatasets(): Promise<{ total: number; datasets: PublishedDatasetItem[] }> {
  const res = await fetch(`${API_BASE}/api/v1/datasets/published`);
  if (!res.ok) {
    throw new ApiError(res.status, "Failed to fetch published datasets");
  }
  return res.json();
}
