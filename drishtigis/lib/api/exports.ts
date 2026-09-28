/**
 * DrishtiGIS — GIS Export & Report API Client
 * ============================================
 * Typed wrappers for GIS exports, dynamic reports, and evidence packages.
 */

import { apiFetch, API_BASE } from "./client";
import type {
  ExportFormatsResponse,
  ExportRequestPayload,
} from "@/lib/types/export";

/**
 * Fetch supported export formats, layers, and CRSs.
 */
export async function getExportFormats(): Promise<ExportFormatsResponse> {
  return apiFetch<ExportFormatsResponse>("/api/v1/exports/formats");
}

/**
 * Trigger binary file download for GIS Export (GeoJSON, GeoPackage, ZIP).
 */
export async function downloadGISExport(payload: ExportRequestPayload): Promise<void> {
  const url = `${API_BASE}/api/v1/exports`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Export download failed with status ${response.status}`);
  }

  const disposition = response.headers.get("Content-Disposition");
  let filename = `DrishtiGIS_Export_${payload.output_format.toLowerCase()}`;
  if (disposition && disposition.includes("filename=")) {
    filename = disposition.split("filename=")[1].replace(/"/g, "").trim();
  } else {
    filename += payload.output_format.toUpperCase() === "GEOPACKAGE" ? ".gpkg" : (payload.output_format.toUpperCase() === "ZIP" ? ".zip" : ".geojson");
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(blobUrl);
}

/**
 * Fetch dynamic Parcel Intelligence Report.
 */
export async function fetchParcelReport(parcelId: string): Promise<Record<string, any>> {
  return apiFetch<Record<string, any>>(`/api/v1/reports/parcel/${parcelId}`, {
    method: "POST",
  });
}

/**
 * Fetch dynamic Surveyor Review Report.
 */
export async function fetchSurveyorReport(reviewId: string): Promise<Record<string, any>> {
  return apiFetch<Record<string, any>>(`/api/v1/reports/review/${reviewId}`, {
    method: "POST",
  });
}

/**
 * Fetch dynamic Area Intelligence Report.
 */
export async function fetchAreaReport(city: string = "Bhopal"): Promise<Record<string, any>> {
  return apiFetch<Record<string, any>>(`/api/v1/reports/region?city=${encodeURIComponent(city)}`);
}

/**
 * Download complete Evidence Package ZIP.
 */
export async function downloadEvidencePackage(city: string = "Bhopal"): Promise<void> {
  const url = `${API_BASE}/api/v1/reports/evidence-package?city=${encodeURIComponent(city)}`;
  const response = await fetch(url, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Evidence package download failed with status ${response.status}`);
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = `DrishtiGIS_EvidencePackage_Bhopal.zip`;
  a.click();
  URL.revokeObjectURL(blobUrl);
}
