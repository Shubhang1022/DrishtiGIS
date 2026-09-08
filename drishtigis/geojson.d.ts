/**
 * Module declaration for .geojson files.
 * Allows importing GeoJSON files as typed JSON modules.
 */
declare module "*.geojson" {
  const value: {
    type: string;
    features?: unknown[];
    [key: string]: unknown;
  };
  export default value;
}
