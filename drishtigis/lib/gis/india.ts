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
