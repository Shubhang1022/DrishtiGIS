/**
 * DrishtiGIS — Location Search API Client
 * =========================================
 */

import { apiFetch } from "./client";
import type { CoverageAvailability } from "@/lib/gis/coverage";
import { searchCityRegistry } from "@/lib/gis/india";

export interface LocationResult {
  name:        string;
  state:       string;
  country:     "India";
  center:      { lat: number; lon: number };
  zoom_level:  number;
  bounds?:     [[number, number], [number, number]];
  coverage:    CoverageAvailability;
}

export interface LocationSearchResponse {
  query:   string;
  country: string;
  results: LocationResult[];
  total:   number;
}

export async function searchLocations(q: string): Promise<LocationSearchResponse> {
  const norm = q.trim();
  if (!norm) {
    return { query: q, country: "India", results: [], total: 0 };
  }

  // 1. Query backend API if available
  try {
    const res = await apiFetch<LocationSearchResponse>(
      `/api/v1/locations/search?q=${encodeURIComponent(norm)}`
    );
    if (res && res.results && res.results.length > 0) {
      return res;
    }
  } catch {
    // Backend API unavailable — fallback to authoritative Indian City Registry
  }

  // 2. Query Authoritative Indian City Registry
  const matches = searchCityRegistry(norm);
  const results: LocationResult[] = matches.map((c) => ({
    name: c.name,
    state: c.state,
    country: "India",
    center: { lat: c.center.lat, lon: c.center.lon },
    zoom_level: c.zoom_level,
    bounds: c.bounds,
    coverage: c.coverage,
  }));

  return {
    query: q,
    country: "India",
    results,
    total: results.length,
  };
}
