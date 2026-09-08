/**
 * DrishtiGIS — Geospatial Constants
 * ====================================
 * Bhopal UAV coverage bounds computed from bhopal_validation_report.json
 * (produced by scripts/data_prep/01_validate_bhopal_tiffs.py)
 *
 * These are the authoritative bounds for the prototype dataset.
 * All demo parcel and AI feature coordinates must fall within UAV_BOUNDS.
 */

/** Bhopal UAV orthomosaic coverage bounds (WGS84, EPSG:4326) */
export const BHOPAL_UAV_BOUNDS = {
  minLon:    77.41299311,
  maxLon:    77.42267457,
  minLat:    23.25573135,
  maxLat:    23.25667101,
  centerLon: 77.41783386,
  centerLat: 23.25620125,
  /** Source CRS of the original imagery */
  epsgSource: "EPSG:32643",
  /** CRS used for storage and web display */
  epsgDisplay: "EPSG:4326",
  widthM:    992.63,
  heightM:   87.57,
  tileCount: 30,
  resolutionM: 0.021713,
  datasetLabel: "Prototype Dataset \u2014 Bhopal",
} as const;

/** Bhopal city centre (for initial map load before zooming to dataset) */
export const BHOPAL_CITY = {
  centerLon: 77.4126,
  centerLat: 23.2599,
  zoom: 12,
} as const;

/** MapLibre camera settings for the UAV dataset extent */
export const BHOPAL_MAP_CONFIG = {
  center:    [BHOPAL_UAV_BOUNDS.centerLon, BHOPAL_UAV_BOUNDS.centerLat] as [number, number],
  zoom:      17,
  minZoom:   14,
  maxZoom:   22,
  /** LngLatBoundsLike for fitBounds */
  bounds: [
    [BHOPAL_UAV_BOUNDS.minLon, BHOPAL_UAV_BOUNDS.minLat],
    [BHOPAL_UAV_BOUNDS.maxLon, BHOPAL_UAV_BOUNDS.maxLat],
  ] as [[number, number], [number, number]],
} as const;

/**
 * Verify a [lon, lat] coordinate falls within the Bhopal UAV bounds.
 * Used for runtime assertions in demo data loading.
 */
export function isWithinBhopalBounds(lon: number, lat: number): boolean {
  return (
    lon >= BHOPAL_UAV_BOUNDS.minLon &&
    lon <= BHOPAL_UAV_BOUNDS.maxLon &&
    lat >= BHOPAL_UAV_BOUNDS.minLat &&
    lat <= BHOPAL_UAV_BOUNDS.maxLat
  );
}
