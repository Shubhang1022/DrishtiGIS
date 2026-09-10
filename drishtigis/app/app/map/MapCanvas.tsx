"use client";

/**
 * DrishtiGIS — Map Canvas (Client Component)
 * ============================================
 * Holds all interactive map state:
 *   - layer visibility (from LayerControl)
 *   - selected parcel (from map click → PropertyPanel)
 *   - nearBhopal flag (from MapLibreMap moveend → CoverageIndicator)
 *   - location search (navigates the map)
 *
 * Composed of:
 *   DynamicMap (SSR-safe MapLibre wrapper)
 *   LayerControl (layer toggle panel)
 *   PropertyPanel (property detail on parcel click)
 *   CoverageIndicator (shows "no data" notice outside Bhopal)
 *   LocationSearch (city search input)
 */

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import type { MapLibreMapProps } from "@/components/map/MapLibreMap";
import { LayerControl } from "@/components/map/LayerControl";
import { PropertyPanel } from "@/components/map/PropertyPanel";
import { CoverageIndicator } from "@/components/map/CoverageIndicator";
import { LocationSearch } from "./LocationSearch";
import type { LayerVisibility } from "@/lib/gis/coverage";
import { DEFAULT_LAYER_VISIBILITY } from "@/lib/gis/coverage";
import { INDIA_CENTER } from "@/lib/gis/india";

// SSR-safe dynamic import of MapLibreMap
function MapSkeleton() {
  return (
    <div
      style={{
        width: "100%", height: "100%",
        background: "var(--color-cream)",
        display: "flex", alignItems: "center", justifyContent: "center",
        flexDirection: "column", gap: "0.75rem",
      }}
      role="status"
      aria-label="Loading map"
    >
      <div
        style={{
          width: "2.5rem", height: "2.5rem", borderRadius: "50%",
          border: "3px solid var(--color-beige)",
          borderTopColor: "var(--color-forest)",
          animation: "spin 0.9s linear infinite",
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem" }}>
        Loading map…
      </p>
    </div>
  );
}

const MapLibreMapDynamic = dynamic(
  () => import("@/components/map/MapLibreMap").then((m) => m.MapLibreMap),
  { ssr: false, loading: () => <MapSkeleton /> }
) as React.ComponentType<MapLibreMapProps>;

export function MapCanvas() {
  const [layers,      setLayers]      = useState<LayerVisibility>(DEFAULT_LAYER_VISIBILITY);
  const [selectedId,  setSelectedId]  = useState<string | null>(null);
  const [nearBhopal,  setNearBhopal]  = useState(false);

  // Fly-to target set by LocationSearch
  const [flyTo, setFlyTo] = useState<{ center: [number, number]; zoom: number } | null>(null);

  const handleLayerChange = useCallback(
    (layer: keyof LayerVisibility, visible: boolean) => {
      setLayers((prev) => ({ ...prev, [layer]: visible }));
    },
    []
  );

  const handleParcelClick = useCallback((propertyId: string) => {
    setSelectedId(propertyId);
  }, []);

  const handleCitySelect = useCallback(
    (lat: number, lon: number, zoom: number) => {
      setFlyTo({ center: [lon, lat], zoom });
    },
    []
  );

  return (
    <>
      {/* ── Top bar ───────────────────────────────────────────────────── */}
      <header
        style={{
          height:       "3rem",
          display:      "flex",
          alignItems:   "center",
          padding:      "0 1rem",
          borderBottom: "1px solid var(--color-beige)",
          background:   "var(--color-cream-light)",
          flexShrink:   0,
          gap:          "0.75rem",
          zIndex:       30,
        }}
      >
        {/* Brand */}
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize:   "1.125rem",
            color:      "var(--color-forest)",
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          DrishtiGIS
        </span>

        {/* Location search — replaces static "Prototype Dataset — Bhopal" label */}
        <LocationSearch onSelect={handleCitySelect} />

        <div style={{ marginLeft: "auto", fontSize: "0.7rem", color: "var(--color-soft-gray)", flexShrink: 0 }}>
          India
        </div>
      </header>

      {/* ── Map area ──────────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflow: "hidden", position: "relative" }}>
        {/* The actual MapLibre map */}
        <MapLibreMapDynamic
          center={flyTo?.center ?? [INDIA_CENTER.lon, INDIA_CENTER.lat] as [number, number]}
          zoom={flyTo?.zoom ?? INDIA_CENTER.zoom}
          height="100%"
          onParcelClick={handleParcelClick}
          onNearBhopalChange={setNearBhopal}
          initialLayers={layers}
        />

        {/* Layer control — absolute positioned over map */}
        <LayerControl visibility={layers} onChange={handleLayerChange} />

        {/* Property panel — slides in when a parcel is selected */}
        <PropertyPanel
          propertyId={selectedId}
          onClose={() => setSelectedId(null)}
        />

        {/* Coverage indicator — shown when outside Bhopal area */}
        <CoverageIndicator nearBhopal={nearBhopal} />
      </main>
    </>
  );
}
