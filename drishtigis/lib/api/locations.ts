/**
 * DrishtiGIS — Location Search API Client
 * =========================================
 */

import { apiFetch } from "./client";
import type { CoverageAvailability } from "@/lib/gis/coverage";

export interface LocationResult {
  name:        string;
  state:       string;
  country:     "India";
  center:      { lat: number; lon: number };
  zoom_level:  number;
  coverage:    CoverageAvailability;
}

export interface LocationSearchResponse {
  query:   string;
  country: string;
  results: LocationResult[];
  total:   number;
}

export async function searchLocations(q: string): Promise<LocationSearchResponse> {
  return apiFetch<LocationSearchResponse>(
    `/api/v1/locations/search?q=${encodeURIComponent(q)}`
  );
}
