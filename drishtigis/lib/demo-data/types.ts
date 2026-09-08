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
// Historical snapshot stub type
// ---------------------------------------------------------------------------

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
