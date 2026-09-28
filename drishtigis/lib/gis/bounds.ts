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
  minLon:    77.41295100,
  maxLon:    77.42268900,
  minLat:    23.25429200,
  maxLat:    23.25667100,
  centerLon: 77.41782000,
  centerLat: 23.25548200,
  /** Source CRS of the original imagery */
  epsgSource: "EPSG:32643",
  /** CRS used for storage and web display */
  epsgDisplay: "EPSG:4326",
  widthM:    992.63,
  heightM:   264.44,
  tileCount: 121,
  resolutionM: 0.021713,
  datasetLabel: "Bhopal High-Res UAV Aerial Dataset",
} as const;

/** Bhopal city centre (for initial map load before zooming to dataset) */
export const BHOPAL_CITY = {
  centerLon: 77.417820,
  centerLat: 23.255482,
  zoom: 17,
} as const;

/** MapLibre camera settings for the UAV dataset extent */
export const BHOPAL_MAP_CONFIG = {
  center:    [BHOPAL_UAV_BOUNDS.centerLon, BHOPAL_UAV_BOUNDS.centerLat] as [number, number],
  zoom:      18,
  minZoom:   12,
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
