/**
 * DrishtiGIS — API Client Barrel Export
 */
export { API_BASE, apiFetch, ApiError } from "./client";
export { getBhopalTileUrl, BHOPAL_TILE_ZOOM_MIN, BHOPAL_TILE_ZOOM_MAX } from "./tiles";
export { getBhopalOsmLayerUrl, fetchOsmLayer } from "./osm";
export type { OsmLayer } from "./osm";
export { fetchParcels, fetchParcel, fetchAIBuildings, fetchSyntheticParcels } from "./parcels";
export type { ParcelListResponse, ParcelDetailResponse, FetchAIBuildingsOptions, SyntheticParcelProperties } from "./parcels";
export { fetchCoverage } from "./coverage";
export { searchLocations } from "./locations";
export type { LocationResult, LocationSearchResponse } from "./locations";
