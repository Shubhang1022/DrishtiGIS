/**
 * DrishtiGIS — Coverage Availability Types
 * ==========================================
 * Mirrors the backend CoverageAvailability dataclass exactly.
 * Used for city coverage lookups and display of data availability state.
 *
 * Architecture principle:
 *   - Bhopal: imagery + parcels + AI analysis (prototype)
 *   - All other cities: map and OSM context only
 *   - historical_data_available is always false — never fabricate
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

/** Layer visibility state for the MapLibre layer control */
export interface LayerVisibility {
  uavImagery:    boolean;
  parcels:       boolean;
  aiFeatures:    boolean;
  osmBuildings:  boolean;
  osmRoads:      boolean;
  osmWaterways:  boolean;
  osmLanduse:    boolean;
}

/** Default layer visibility on first load */
export const DEFAULT_LAYER_VISIBILITY: LayerVisibility = {
  uavImagery:   true,
  parcels:      true,
  aiFeatures:   true,
  osmBuildings: false,   // dense at initial zoom — off by default
  osmRoads:     true,
  osmWaterways: true,
  osmLanduse:   false,   // polygon fills can overwhelm at low zoom
} as const;
