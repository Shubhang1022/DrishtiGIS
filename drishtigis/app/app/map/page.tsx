/**
 * DrishtiGIS — India-Scale WebGIS Map Page
 * ==========================================
 * Route: /app/map
 * PRD section 9-12: Map-first. 75-85% of viewport. Not a dashboard.
 *
 * Architecture:
 *   - Server Component (this file) provides layout shell
 *   - MapCanvas (Client Component below) manages all interactive state
 *   - Map starts at India overview (zoom 5) — NOT hard-coded at Bhopal
 *   - Bhopal data layers load lazily when user navigates to the area
 */

import type { Metadata } from "next";
import { MapCanvas } from "./MapCanvas";

export const metadata: Metadata = {
  title:       "Map \u2014 DrishtiGIS",
  description: "India-scale interactive WebGIS map. Prototype intelligence data available for Bhopal.",
};

export default function MapPage() {
  return (
    <div
      style={{
        display:       "flex",
        flexDirection: "column",
        height:        "100dvh",
        background:    "var(--color-cream)",
        fontFamily:    "var(--font-ui)",
        overflow:      "hidden",
      }}
    >
      <MapCanvas />
    </div>
  );
}
