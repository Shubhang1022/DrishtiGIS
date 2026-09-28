/**
 * DrishtiGIS — Tile URL Builder
 * ==============================
 * Returns the MapLibre-compatible tile URL template for Bhopal UAV tiles.
 * Used directly as the `tiles` array in a MapLibre raster source definition.
 *
 * No fetch is needed — MapLibre fetches individual tiles itself.
 */

import { API_BASE } from "./client";

/** XYZ tile URL template for Bhopal UAV orthomosaic (z18–21) */
export function getBhopalTileUrl(): string {
  return "/api/v1/tiles/bhopal/{z}/{x}/{y}.png";
}

export const BHOPAL_TILE_ZOOM_MIN = 18;
export const BHOPAL_TILE_ZOOM_MAX = 21;
