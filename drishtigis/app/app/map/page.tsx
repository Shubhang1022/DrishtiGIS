/**
 * DrishtiGIS — Main WebGIS Map Page
 * ====================================
 * Route: /app/map
 * PRD section 9-12: Map-first. 75-85% of viewport. Not a dashboard.
 *
 * Server Component. The map itself is loaded via DynamicMap (Client Component)
 * which wraps MapLibreMap with next/dynamic { ssr: false }.
 */

import type { Metadata } from "next";
import { DynamicMap } from "@/components/map/DynamicMap";
import { BHOPAL_UAV_BOUNDS } from "@/lib/gis/bounds";

export const metadata: Metadata = {
  title: "Map \u2014 DrishtiGIS",
  description: "Interactive WebGIS map \u2014 Bhopal prototype dataset",
};

export default function MapPage() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100dvh",
        background: "var(--color-cream)",
        fontFamily: "var(--font-ui)",
      }}
    >
      {/* Minimal top bar */}
      <header
        style={{
          height: "3rem",
          display: "flex",
          alignItems: "center",
          padding: "0 1rem",
          borderBottom: "1px solid var(--color-beige)",
          background: "var(--color-cream-light)",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "1.125rem",
            color: "var(--color-forest)",
            fontWeight: 600,
          }}
        >
          DrishtiGIS
        </span>
        <span
          style={{
            marginLeft: "1rem",
            fontSize: "0.75rem",
            color: "var(--color-soft-gray)",
          }}
        >
          Prototype Dataset \u2014 Bhopal
        </span>
        <div
          style={{
            marginLeft: "auto",
            fontSize: "0.7rem",
            color: "var(--color-soft-gray)",
          }}
        >
          {BHOPAL_UAV_BOUNDS.tileCount} tiles &middot;{" "}
          {(BHOPAL_UAV_BOUNDS.resolutionM * 100).toFixed(2)} cm/px &middot;{" "}
          {BHOPAL_UAV_BOUNDS.epsgSource}
        </div>
      </header>

      {/* Map fills remaining height */}
      <main style={{ flex: 1, overflow: "hidden", position: "relative" }}>
        <DynamicMap height="100%" />
      </main>
    </div>
  );
}
