/**
 * DrishtiGIS — OSM Layer API Client
 * ===================================
 * Fetches pre-extracted Bhopal OSM thematic GeoJSON layers from the backend.
 *
 * Available layers: buildings (26,577), roads (2,933), waterways (31), landuse (98)
 * Source classification: OSM_OPENSTREETMAP
 *
 * The 1.7 GB India PBF is never involved at runtime.
 * All GeoJSON was pre-extracted in Phase 3.
 */

import { API_BASE } from "./client";

export type OsmLayer = "buildings" | "roads" | "waterways" | "landuse";

/** Returns the URL for a Bhopal OSM layer (used for MapLibre source data URL) */
export function getBhopalOsmLayerUrl(layer: OsmLayer): string {
  return `${API_BASE}/api/v1/osm/bhopal/${layer}`;
}

/** Fetch a Bhopal OSM layer as parsed GeoJSON */
export async function fetchOsmLayer(
  layer: OsmLayer
): Promise<GeoJSON.FeatureCollection> {
  const res = await fetch(getBhopalOsmLayerUrl(layer));
  if (!res.ok) {
    throw new Error(`OSM layer '${layer}' fetch failed: ${res.status}`);
  }
  return res.json() as Promise<GeoJSON.FeatureCollection>;
}
