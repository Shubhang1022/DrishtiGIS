"use client";

/**
 * DynamicMap — Client Component wrapper for MapLibreMap
 * =======================================================
 * next/dynamic with { ssr: false } must live in a Client Component (Next.js 16+).
 * This wrapper is the correct location for the dynamic import.
 * Import this component from Server Components instead of MapLibreMap directly.
 */

import dynamic from "next/dynamic";
import type { MapLibreMapProps } from "./MapLibreMap";

function MapSkeleton() {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "var(--color-cream)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: "0.75rem",
      }}
      role="status"
      aria-label="Loading map"
    >
      <div
        style={{
          width: "2.5rem",
          height: "2.5rem",
          borderRadius: "50%",
          border: "3px solid var(--color-beige)",
          borderTopColor: "var(--color-forest)",
          animation: "spin 0.9s linear infinite",
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem" }}>
        Loading map\u2026
      </p>
    </div>
  );
}

const MapLibreMapDynamic = dynamic(
  () => import("./MapLibreMap").then((mod) => mod.MapLibreMap),
  {
    ssr: false,
    loading: () => <MapSkeleton />,
  }
);

export function DynamicMap(props: MapLibreMapProps) {
  return <MapLibreMapDynamic {...props} />;
}
