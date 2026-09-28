/**
 * DrishtiGIS — India-Scale Geographic Constants
 * ================================================
 * Core geographic reference values for India-wide navigation.
 *
 * The DrishtiGIS application is India-scale. Bhopal is the first
 * prototype intelligence area — the map starts at India overview,
 * not hard-coded at Bhopal.
 */

/** India national center — default map load position */
export const INDIA_CENTER = {
  lat:  20.5937,
  lon:  78.9629,
  zoom: 5,
} as const;

/** India geographic bounds (rough, for coverage checks) */
export const INDIA_BOUNDS = {
  minLon: 68.1,
  maxLon: 97.4,
  minLat: 6.7,
  maxLat: 37.1,
} as const;

/** Bhopal city center — used for city-level navigation and coverage checks */
export const BHOPAL_CITY_CENTER = {
  lat:  23.2599,
  lon:  77.4126,
  zoom: 12,
} as const;

/**
 * Distance threshold in km: if the map center is within this radius
 * of Bhopal city center, the coverage indicator is hidden (data available).
 * Beyond this radius, show "no detailed data" notice.
 */
export const COVERAGE_UNAVAILABLE_THRESHOLD_KM = 10;

/**
 * Haversine distance between two WGS84 points in kilometres.
 * Used for coverage availability radius checks.
 */
export function distanceKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth radius km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/** Returns true if the map center is close enough to Bhopal to show intelligence data */
export function isNearBhopal(lat: number, lon: number): boolean {
  return (
    distanceKm(lat, lon, BHOPAL_CITY_CENTER.lat, BHOPAL_CITY_CENTER.lon) <=
    COVERAGE_UNAVAILABLE_THRESHOLD_KM
  );
}

import { BHOPAL_UAV_BOUNDS } from "./bounds";
import type { CoverageAvailability } from "./coverage";

export interface CityRegistryEntry {
  name:        string;
  state:       string;
  country:     "India";
  center:      { lat: number; lon: number };
  zoom_level:  number;
  bounds?:     [[number, number], [number, number]];
  coverage:    CoverageAvailability;
}

/**
 * Authoritative Indian City & Coverage Registry (Single Source of Truth)
 * Bhopal currently has active prototype intelligence.
 * All other cities provide base map + OSM context until datasets are onboarded.
 */
export const INDIAN_CITIES_REGISTRY: CityRegistryEntry[] = [
  {
    name: "Bhopal",
    state: "Madhya Pradesh",
    country: "India",
    center: { lat: 23.2599, lon: 77.4126 },
    zoom_level: 16,
    bounds: [
      [BHOPAL_UAV_BOUNDS.minLon, BHOPAL_UAV_BOUNDS.minLat],
      [BHOPAL_UAV_BOUNDS.maxLon, BHOPAL_UAV_BOUNDS.maxLat],
    ],
    coverage: {
      city: "Bhopal",
      state: "Madhya Pradesh",
      country: "India",
      center_lat: 23.2599,
      center_lon: 77.4126,
      map_available: true,
      osm_available: true,
      imagery_available: true,
      parcel_data_available: true,
      ai_analysis_available: true,
      historical_data_available: false,
      coverage_source: "prototype",
      disclaimer: "Prototype intelligence area — High-res UAV imagery, parcel mapping & AI feature extraction active.",
      datasets: [
        {
          id: "bhopal_uav_2026",
          type: "uav_orthomosaic",
          name: "Bhopal High-Res UAV Imagery (0.02m)",
          source: "DrishtiGIS UAV Unit",
          bounds: [BHOPAL_UAV_BOUNDS.minLon, BHOPAL_UAV_BOUNDS.minLat, BHOPAL_UAV_BOUNDS.maxLon, BHOPAL_UAV_BOUNDS.maxLat]
        },
        {
          id: "bhopal_parcels_2026",
          type: "cadastral_parcels",
          name: "Bhopal Prototype Parcels",
          source: "DrishtiGIS Parcel Engine"
        },
        {
          id: "bhopal_ai_buildings_2026",
          type: "ai_extracted_buildings",
          name: "AI Building Extractions",
          source: "DrishtiGIS AI Vision Model"
        }
      ]
    }
  },
  {
    name: "Lucknow",
    state: "Uttar Pradesh",
    country: "India",
    center: { lat: 26.8467, lon: 80.9462 },
    zoom_level: 13,
    coverage: {
      city: "Lucknow",
      state: "Uttar Pradesh",
      country: "India",
      center_lat: 26.8467,
      center_lon: 80.9462,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "New Delhi",
    state: "Delhi",
    country: "India",
    center: { lat: 28.6139, lon: 77.2090 },
    zoom_level: 12,
    coverage: {
      city: "New Delhi",
      state: "Delhi",
      country: "India",
      center_lat: 28.6139,
      center_lon: 77.2090,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Mumbai",
    state: "Maharashtra",
    country: "India",
    center: { lat: 19.0760, lon: 72.8777 },
    zoom_level: 12,
    coverage: {
      city: "Mumbai",
      state: "Maharashtra",
      country: "India",
      center_lat: 19.0760,
      center_lon: 72.8777,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Bengaluru",
    state: "Karnataka",
    country: "India",
    center: { lat: 12.9716, lon: 77.5946 },
    zoom_level: 12,
    coverage: {
      city: "Bengaluru",
      state: "Karnataka",
      country: "India",
      center_lat: 12.9716,
      center_lon: 77.5946,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Ahmedabad",
    state: "Gujarat",
    country: "India",
    center: { lat: 23.0225, lon: 72.5714 },
    zoom_level: 12,
    coverage: {
      city: "Ahmedabad",
      state: "Gujarat",
      country: "India",
      center_lat: 23.0225,
      center_lon: 72.5714,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Chennai",
    state: "Tamil Nadu",
    country: "India",
    center: { lat: 13.0827, lon: 80.2707 },
    zoom_level: 12,
    coverage: {
      city: "Chennai",
      state: "Tamil Nadu",
      country: "India",
      center_lat: 13.0827,
      center_lon: 80.2707,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Kolkata",
    state: "West Bengal",
    country: "India",
    center: { lat: 22.5726, lon: 88.3639 },
    zoom_level: 12,
    coverage: {
      city: "Kolkata",
      state: "West Bengal",
      country: "India",
      center_lat: 22.5726,
      center_lon: 88.3639,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Hyderabad",
    state: "Telangana",
    country: "India",
    center: { lat: 17.3850, lon: 78.4867 },
    zoom_level: 12,
    coverage: {
      city: "Hyderabad",
      state: "Telangana",
      country: "India",
      center_lat: 17.3850,
      center_lon: 78.4867,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Pune",
    state: "Maharashtra",
    country: "India",
    center: { lat: 18.5204, lon: 73.8567 },
    zoom_level: 12,
    coverage: {
      city: "Pune",
      state: "Maharashtra",
      country: "India",
      center_lat: 18.5204,
      center_lon: 73.8567,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Jaipur",
    state: "Rajasthan",
    country: "India",
    center: { lat: 26.9124, lon: 75.7873 },
    zoom_level: 12,
    coverage: {
      city: "Jaipur",
      state: "Rajasthan",
      country: "India",
      center_lat: 26.9124,
      center_lon: 75.7873,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Patna",
    state: "Bihar",
    country: "India",
    center: { lat: 25.5941, lon: 85.1376 },
    zoom_level: 12,
    coverage: {
      city: "Patna",
      state: "Bihar",
      country: "India",
      center_lat: 25.5941,
      center_lon: 85.1376,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Jammu",
    state: "Jammu & Kashmir",
    country: "India",
    center: { lat: 32.7266, lon: 74.8570 },
    zoom_level: 12,
    coverage: {
      city: "Jammu",
      state: "Jammu & Kashmir",
      country: "India",
      center_lat: 32.7266,
      center_lon: 74.8570,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Ludhiana",
    state: "Punjab",
    country: "India",
    center: { lat: 30.9010, lon: 75.8573 },
    zoom_level: 12,
    coverage: {
      city: "Ludhiana",
      state: "Punjab",
      country: "India",
      center_lat: 30.9010,
      center_lon: 75.8573,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  },
  {
    name: "Latur",
    state: "Maharashtra",
    country: "India",
    center: { lat: 18.4088, lon: 76.5604 },
    zoom_level: 12,
    coverage: {
      city: "Latur",
      state: "Maharashtra",
      country: "India",
      center_lat: 18.4088,
      center_lon: 76.5604,
      map_available: true,
      osm_available: true,
      imagery_available: false,
      parcel_data_available: false,
      ai_analysis_available: false,
      historical_data_available: false,
      coverage_source: "none",
      disclaimer: "Map and OSM context active. Detailed AI property intelligence not yet onboarded."
    }
  }
];

/**
 * Searches the authoritative City Registry for query substring matches.
 * Case-insensitive, trims leading/trailing whitespace.
 */
export function searchCityRegistry(q: string): CityRegistryEntry[] {
  const norm = q.trim().toLowerCase();
  if (!norm) return [];

  // Filter matching cities
  const matches = INDIAN_CITIES_REGISTRY.filter(
    (c) =>
      c.name.toLowerCase().includes(norm) ||
      c.state.toLowerCase().includes(norm)
  );

  // Sort matches so prefix matches (e.g. "bho" -> "Bhopal") come first
  return matches.sort((a, b) => {
    const aStarts = a.name.toLowerCase().startsWith(norm);
    const bStarts = b.name.toLowerCase().startsWith(norm);
    if (aStarts && !bStarts) return -1;
    if (!aStarts && bStarts) return 1;
    return a.name.localeCompare(b.name);
  });
}

/**
 * Returns cities in the registry that have actual processed datasets.
 * ONLY cities with coverage_source !== 'none' or imagery_available === true.
 */
export function getActiveCoverageCities(): CityRegistryEntry[] {
  return INDIAN_CITIES_REGISTRY.filter(
    (c) => c.coverage.coverage_source !== "none" || c.coverage.imagery_available
  );
}

