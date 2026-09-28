/**
 * DrishtiGIS — Coverage Availability Types
 * ==========================================
 * Mirrors the backend CoverageAvailability dataclass exactly.
 * Used for city coverage lookups and display of data availability state.
 */

export type CoverageSource = "prototype" | "production" | "none";

export interface CoverageAvailability {
  city:                      string;
  state:                     string;
  country:                   "India";
  center_lat:                number;
  center_lon:                number;
  map_available:             boolean;
  osm_available:             boolean;
  imagery_available:         boolean;
  parcel_data_available:     boolean;
  ai_analysis_available:     boolean;
  historical_data_available: boolean;  // always false for prototype
  coverage_source:           CoverageSource;
  disclaimer?:               string | null;
  datasets?:                 CoverageDataset[];
}

export interface CoverageDataset {
  id:               string;
  type:             string;
  name:             string;
  tile_url_template?: string;
  zoom_min?:        number;
  zoom_max?:        number;
  bounds?:          [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  resolution_m?:    number;
  tile_count?:      number;
  extraction_bbox?: [number, number, number, number];
  layers?:          string[];
  source:           string;
  _disclaimer?:     string;
  _attribution?:    string;
}

export type BasemapType = "standard" | "satellite";
export type BuildingSourceType = "ai" | "osm";

/** Layer visibility state for the MapLibre layer control */
export interface LayerVisibility {
  basemap:        BasemapType;
  uavImagery:     boolean;
  parcels:        boolean;
  buildings:      boolean;              // Single consolidated building layer toggle
  buildingSource: BuildingSourceType;   // Active building footprint data source ("ai" or "osm")
  aiFeatures:     boolean;              // Legacy compatibility
  osmBuildings:   boolean;              // Legacy compatibility
  osmRoads:       boolean;
  osmWaterways:   boolean;
  osmLanduse:     boolean;
  userProperties: boolean;              // User registered properties layer
}

/** Default layer visibility on first load */
export const DEFAULT_LAYER_VISIBILITY: LayerVisibility = {
  basemap:        "standard",
  uavImagery:     true,
  parcels:        true,
  buildings:      true,
  buildingSource: "ai",
  aiFeatures:     true,
  osmBuildings:   false,
  osmRoads:       true,
  osmWaterways:   true,
  osmLanduse:     false,
  userProperties: true,
} as const;
