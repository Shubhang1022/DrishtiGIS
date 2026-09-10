/**
 * DrishtiGIS — Coverage API Client
 * ==================================
 */

import { apiFetch } from "./client";
import type { CoverageAvailability } from "@/lib/gis/coverage";

export async function fetchCoverage(
  citySlug: string
): Promise<CoverageAvailability> {
  return apiFetch<CoverageAvailability>(`/api/v1/coverage/${encodeURIComponent(citySlug)}`);
}
