/**
 * DrishtiGIS — Demo Data Type Definitions
 * =========================================
 * Spec task: 4.1 (foundation-and-data-pipeline v0.2)
 *
 * These types define the shape of every demo data record used in the
 * DrishtiGIS prototype. Every record carrying one of these types MUST
 * include a `_source` field drawn from the DataSource enum.
 *
 * DATA INTEGRITY RULES (from CLAUDE.md §51, requirements.md §51):
 *   - All demo records are DEMO_DATA_PROTOTYPE_ONLY
 *   - AI feature records are AI_DERIVED_DEMO (not from a real model run)
 *   - city is a string literal 'Bhopal' — TypeScript enforces this
 *   - No record may claim to be official government cadastral data
 *   - No record may claim legal ownership or legal boundary validity
 */

// ---------------------------------------------------------------------------
// Data source classification (mirrors backend app/utils/data_source.py)
// ---------------------------------------------------------------------------

export enum DataSource {
  /** Authoritative government cadastral / survey data */
  OFFICIAL_REFERENCE = "OFFICIAL_REFERENCE",
  /** Output from a real AI model inference run */
  AI_DERIVED = "AI_DERIVED",
  /** From OpenStreetMap — supplementary context, NOT official cadastral data */
  OSM_OPENSTREETMAP = "OSM_OPENSTREETMAP",
  /** Created for demonstration — never authoritative, clearly labeled */
  DEMO_DATA_PROTOTYPE_ONLY = "DEMO_DATA_PROTOTYPE_ONLY",
  /** Original unprocessed UAV imagery */
  RAW_RASTER_UAV = "RAW_RASTER_UAV",
  /** Derived from RAW_RASTER_UAV via documented pipeline */
  PROCESSED_RASTER = "PROCESSED_RASTER",
    /** Demo placeholder AI output — NOT from a real model run */
  AI_DERIVED_DEMO = "AI_DERIVED_DEMO",
  /** Real AI output from the UAVPal U-Net ResNet18 pipeline (Phase 3–5) */
  AI_DERIVED_UAVPAL = "AI_DERIVED_UAVPAL",
  /** Synthetic prototype parcel/property data — explicitly NOT official cadastral data */
  SYNTHETIC_DEMO = "SYNTHETIC_DEMO",
}

// ---------------------------------------------------------------------------
// Shared disclaimer strings (use these verbatim in UI labels)
// ---------------------------------------------------------------------------

export const DEMO_DATA_DISCLAIMER =
  "This is prototype demonstration data. It is not derived from official " +
  "government cadastral records and has no legal status.";

export const AI_DERIVED_DISCLAIMER =
  "AI-derived observation from a prototype demonstration model. " +
  "This is not a legal or official determination. Requires field verification.";

export const DISCREPANCY_DISCLAIMER =
  "This potential discrepancy was detected by a demonstration AI model and " +
  "is not a legal determination. It should be verified by a qualified " +
  "surveyor before any action is taken.";

// ---------------------------------------------------------------------------
// Parcel types
// ---------------------------------------------------------------------------

export type LandType = "Residential" | "Commercial" | "Agricultural" | "Industrial";
export type ParcelStatus = "Verified" | "Pending" | "Disputed";

/** Properties shared by every demo parcel feature */
export interface DemoParcelProperties {
  id: string;
  /** Format: DRS-BPL-XXXXX */
  property_id: string;
  plot_number: string;
  survey_number: string;
  area_m2: number;
  land_type: LandType;
  status: ParcelStatus;
  /** Literal type — TypeScript enforces this can never be another city */
  city: "Bhopal";
  state: "Madhya Pradesh";
  country: "India";
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
  _disclaimer: string;
  _datasetLabel: "Prototype Dataset — Bhopal";
}

export interface DemoParcel {
  type: "Feature";
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  properties: DemoParcelProperties;
}

export interface DemoParcelCollection {
  type: "FeatureCollection";
  features: DemoParcel[];
  metadata: {
    _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
    description: string;
    coverageBounds: {
      minLon: number;
      maxLon: number;
      minLat: number;
      maxLat: number;
    };
  };
}

// ---------------------------------------------------------------------------
// AI feature types
// ---------------------------------------------------------------------------

export type AIFeatureType = "building" | "road" | "tree" | "water";

export interface DemoAIFeatureProperties {
  id: string;
  feature_type: AIFeatureType;
  /** Model confidence 0–1 */
  confidence: number;
  /** Computed from actual polygon geometry — not asserted */
  area_m2: number;
  model: string;
  model_version: string;
  dataset: string;
  /** The parcel this feature is spatially associated with (may be null if unassociated) */
  associated_parcel_id: string | null;
  _source: DataSource.AI_DERIVED_DEMO;
  _disclaimer: string;
}

export interface DemoAIFeature {
  type: "Feature";
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  properties: DemoAIFeatureProperties;
}

export interface DemoAIFeatureCollection {
  type: "FeatureCollection";
  features: DemoAIFeature[];
  metadata: {
    _source: DataSource.AI_DERIVED_DEMO;
    description: string;
  };
}

// ---------------------------------------------------------------------------
// Discrepancy types
// ---------------------------------------------------------------------------

export type DiscrepancyType =
  | "area_mismatch"
  | "boundary_mismatch"
  | "new_structure";

export type DiscrepancySeverity = "low" | "medium" | "high";

export interface DemoDiscrepancy {
  id: string;
  parcel_id: string;
  feature_id: string;
  type: DiscrepancyType;
  official_value: number;
  ai_value: number;
  difference: number;
  difference_pct: number;
  severity: DiscrepancySeverity;
  /** Always "pending_review" for demo — never auto-confirmed */
  status: "pending_review";
  /**
   * Spatial basis — explains that the discrepancy is geometric, not just numeric.
   * The AI polygon partially extends outside the parcel boundary.
   */
  spatial_basis: string;
  /**
   * Safe language as required by CLAUDE.md §26 and PRD §16.
   * MUST NOT contain "illegal", "fraud", "encroachment", "violation".
   */
  description: string;
  ui_label: string;
  /** Always null — never claim a legal status from demo data */
  legal_status: null;
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
  _disclaimer: string;
}

// ---------------------------------------------------------------------------
// Property types
// ---------------------------------------------------------------------------

export interface DemoProperty {
  id: string;
  parcel_id: string;
  property_id: string;
  address: string;
  /** Literal type — can never be another city */
  city: "Bhopal";
  state: "Madhya Pradesh";
  country: "India";
  land_type: LandType;
  property_type?: string;
  current_owner_name?: string;
  previous_owner_name?: string;
  resident_count?: number | null;
  purchase_price_inr?: number | null;
  estimated_selling_price_inr?: number | null;
  valuation_year?: number | null;
  status: string;
  record_status: "Demo record";
  last_updated: string;
  source_label: "Prototype Dataset — Bhopal";
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
  _disclaimer: string;
}

// ---------------------------------------------------------------------------
// Dataset record types
// ---------------------------------------------------------------------------

export interface DemoDataset {
  id: string;
  name: string;
  location: string;
  dataset_type: "orthomosaic" | "dsm" | "cadastral_gis" | "other";
  source: DataSource;
  crs: string;
  bounds: {
    minLon: number;
    maxLon: number;
    minLat: number;
    maxLat: number;
  };
  resolution_m: number;
  tile_count: number;
  status: "published";
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
  _disclaimer: string;
}

// ---------------------------------------------------------------------------
// AI building types — Phase 5 real UAVPal pipeline output
// ---------------------------------------------------------------------------

export type ParcelRelationship =
  | "FULLY_WITHIN"
  | "PARTIALLY_OVERLAPS"
  | "CROSSES_BOUNDARY"
  | "TOUCHES_BOUNDARY"
  | "NO_PARCEL_MATCH";

/** Properties on each feature in bhopal-building-parcel-associations.geojson */
export interface RealAIBuildingProperties {
  id:                   string;           // AI-BPL-FINAL-XXXXX
  source:               "AI_DERIVED_UAVPAL";
  model:                string;           // UNet-ResNet18-UAVPal
  model_version:        string;
  source_tile:          string;           // e.g. "00_10"
  source_class:         4;                // Building class ID — always 4
  source_class_name:    "Building";
  confidence:           number;           // mean softmax P(Building) over component
  confidence_median:    number;
  confidence_method:    string;
  area_m2:              number;           // metric area in EPSG:32643
  building_area_m2:     number;           // same value, for join compatibility
  perimeter_m:          number;
  centroid_lon:         number;
  centroid_lat:         number;
  crs_source:           "EPSG:32643";
  crs_output:           "EPSG:4326";
  pixel_area_px2:       number;
  was_watershed_split:  boolean;
  // Phase 5 parcel association fields
  primary_parcel_id:    string | null;
  primary_property_id:  string | null;    // e.g. "DRS-BPL-00101"
  secondary_parcel_ids: string[];
  intersection_area_m2: number;
  overlap_ratio:        number;           // intersection_area_m2 / building_area_m2
  parcel_relationship:  ParcelRelationship;
}

/** Summary of one building for the parcel ai_analysis section */
export interface AIBuildingSummary {
  id:                  string;
  area_m2:             number;
  confidence:          number | null;
  confidence_median:   number | null;
  relationship:        ParcelRelationship;
  overlap_ratio:       number;
  source_tile:         string;
  model:               string;
  model_version:       string;
  was_watershed_split: boolean;
}

/** Discrepancy record (Phase 5 real data, not demo) */
export interface AIDiscrepancy {
  id:            string;
  parcel_id:     string | null;
  building_id:   string;
  type:          string;
  severity:      "REVIEW" | "LOW" | "MEDIUM" | "HIGH";
  description:   string;
  spatial_basis: Record<string, unknown>;
  source:        "AI_DERIVED_UAVPAL";
  created_at:    string;
}

/** ai_analysis sub-object in ParcelDetailResponse */
export interface AIBuildingAnalysis {
  ai_available:           boolean;
  building_count:         number;
  total_detected_area_m2: number;
  average_confidence:     number | null;
  discrepancy_count:      number;
  buildings:              AIBuildingSummary[];
  discrepancies:          AIDiscrepancy[];
  parcel_area_m2:         number;
  coverage_ratio:         number | null;  // detected_area / parcel_area
  _source:                "AI_DERIVED_UAVPAL";
  _disclaimer:            string;
}

/** Response from GET /api/v1/features */
export interface AIFeaturesResponse {
  type:          "FeatureCollection";
  total:         number;
  features:      GeoJSON.Feature<GeoJSON.Polygon, RealAIBuildingProperties>[];
  _source:       "AI_DERIVED_UAVPAL";
  ai_available:  boolean;
  _disclaimer:   string;
  _coverage_note?: string;
}



// ---------------------------------------------------------------------------
// Synthetic parcel types — Phase 5.5
// ---------------------------------------------------------------------------

export type SyntheticParcelShape = "rect" | "L" | "irr";
export type SyntheticRecordStatus = "SYNTHETIC_DEMO";
export type SyntheticRow = "A" | "B";

/** Properties on each feature in bhopal-synthetic-parcels.geojson */
export interface SyntheticParcelProperties {
  id:                string;
  property_id:       string;
  plot_number:       string;
  survey_number:     string;
  owner_name:        string;
  land_use:          string;
  property_type:     string;
  area_m2:           number;
  status:            SyntheticRecordStatus;
  city:              "Bhopal";
  state:             "Madhya Pradesh";
  country:           "India";
  centroid_lon:      number;
  centroid_lat:      number;
  shape_type:        SyntheticParcelShape;
  row:               SyntheticRow;
  _source:           DataSource.SYNTHETIC_DEMO;
  _disclaimer:       string;
  _datasetLabel:     "Synthetic Demo Dataset — Bhopal";
}

/** Topology validation result for one parcel */
export interface TopologyValidationResult {
  parcel_id:          string;
  geometry_valid:     boolean;
  self_intersection:  boolean;
  zero_area:          boolean;
  overlap_detected:   boolean;
  duplicate_detected: boolean;
  status:             "VALID" | "REVIEW_REQUIRED";
}


/**
 * Historical snapshot stub for the prototype.
 * change_type is null because no real multi-temporal imagery exists.
 * Do NOT fabricate a change classification.
 */
export interface DemoHistoricalSnapshot {
  id: string;
  property_id: string;
  dataset_id: string;
  captured_at: string;
  imagery_source: string;
  /**
   * NULL = no historical change classification available.
   * Reason: no real multi-temporal imagery exists for the prototype dataset.
   */
  change_type: null;
  confidence: null;
  _source: DataSource.DEMO_DATA_PROTOTYPE_ONLY;
  _disclaimer: string;
}
