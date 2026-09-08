/**
 * DrishtiGIS — Demo Data Barrel Export
 * ======================================
 * Spec task: 4.6 (foundation-and-data-pipeline v0.2)
 *
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  DEMO DATA — PROTOTYPE ONLY                                         ║
 * ║  None of this data represents official government records,          ║
 * ║  verified ownership, legal boundaries, or authoritative survey.     ║
 * ║  AI features are demo placeholders — NOT real model output.         ║
 * ║  All parcel geometries are within the Bhopal UAV prototype bounds.  ║
 * ║  City: Bhopal, Madhya Pradesh, India.                               ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 */

// Re-export all types and the DataSource enum
export {
  DataSource,
  DEMO_DATA_DISCLAIMER,
  AI_DERIVED_DISCLAIMER,
  DISCREPANCY_DISCLAIMER,
} from "./types";

export type {
  DemoParcel,
  DemoParcelCollection,
  DemoAIFeature,
  DemoAIFeatureCollection,
  DemoDiscrepancy,
  DemoProperty,
  DemoDataset,
  DemoHistoricalSnapshot,
  LandType,
  ParcelStatus,
  AIFeatureType,
  DiscrepancyType,
  DiscrepancySeverity,
} from "./types";

import { DataSource } from "./types";
import type {
  DemoParcelCollection,
  DemoAIFeatureCollection,
  DemoDiscrepancy,
  DemoProperty,
  DemoDataset,
  DemoHistoricalSnapshot,
} from "./types";

// Static imports — Next.js App Router / Turbopack handles JSON natively
import parcelsRaw from "./bhopal-parcels.geojson";
import featuresRaw from "./bhopal-ai-features.geojson";
import discRaw from "./bhopal-discrepancies.json";
import propsRaw from "./properties.json";

// ---------------------------------------------------------------------------
// Named constants consumed by the frontend
// ---------------------------------------------------------------------------

/** GeoJSON FeatureCollection of 3 demo parcels within Bhopal UAV bounds */
export const DEMO_PARCELS = parcelsRaw as unknown as DemoParcelCollection;

/** GeoJSON FeatureCollection of 2 demo AI building detections */
export const DEMO_AI_FEATURES = featuresRaw as unknown as DemoAIFeatureCollection;

/** Array of 2 demo discrepancy records */
export const DEMO_DISCREPANCIES = (discRaw as { discrepancies: DemoDiscrepancy[] }).discrepancies;

/** Array of 3 demo property records */
export const DEMO_PROPERTIES = (propsRaw as { properties: DemoProperty[] }).properties;

/** Demo dataset record */
export const DEMO_DATASET: DemoDataset = {
  id:           "dataset-bpl-prototype-001",
  name:         "Bhopal UAV Orthomosaic \u2014 Prototype",
  location:     "Bhopal, Madhya Pradesh, India",
  dataset_type: "orthomosaic",
  source:       DataSource.DEMO_DATA_PROTOTYPE_ONLY,
  crs:          "EPSG:32643 (WGS 84 / UTM Zone 43N)",
  bounds: {
    minLon: 77.41299311,
    maxLon: 77.42267457,
    minLat: 23.25573135,
    maxLat: 23.25667101,
  },
  resolution_m: 0.021713,
  tile_count:   30,
  status:       "published",
  _source:      DataSource.DEMO_DATA_PROTOTYPE_ONLY,
  _disclaimer:  "This dataset record describes the prototype Bhopal UAV imagery. Not a production entry.",
};

/** Demo historical snapshot stub — change_type is null: no multi-temporal imagery available */
export const DEMO_HISTORICAL_SNAPSHOT: DemoHistoricalSnapshot = {
  id:             "snap-bpl-001",
  property_id:    "prop-bpl-001",
  dataset_id:     "dataset-bpl-prototype-001",
  captured_at:    "2026-09-08T00:00:00Z",
  imagery_source: "Bhopal UAV Prototype (single epoch)",
  change_type:    null,  // No second epoch acquired — do NOT fabricate
  confidence:     null,
  _source:        DataSource.DEMO_DATA_PROTOTYPE_ONLY,
  _disclaimer:    "Historical imagery not available. No second time epoch has been acquired for the prototype dataset.",
};

// ---------------------------------------------------------------------------
// Lookup helpers
// ---------------------------------------------------------------------------

export function getDemoParcel(propertyId: string) {
  return DEMO_PARCELS.features.find(
    (f) => f.properties.property_id === propertyId
  ) ?? null;
}

export function getDemoProperty(propertyId: string) {
  return DEMO_PROPERTIES.find((p) => p.property_id === propertyId) ?? null;
}

export function getDemoAIFeatures(parcelId: string) {
  return DEMO_AI_FEATURES.features.filter(
    (f) => f.properties.associated_parcel_id === parcelId
  );
}

export function getDemoDiscrepancies(parcelId: string) {
  return DEMO_DISCREPANCIES.filter((d) => d.parcel_id === parcelId);
}
