"use client";

/**
 * DrishtiGIS — Base MapLibre Map Component
 * ==========================================
 * Client-only. Never imported server-side.
 * Always consumed via next/dynamic with { ssr: false }.
 *
 * MapLibre GL JS v6 is ESM-only and references browser globals (window, document).
 * This component uses a dynamic import inside useEffect to guarantee it only
 * executes in the browser.
 */

import { useEffect, useRef, useState } from "react";
import { BHOPAL_MAP_CONFIG, BHOPAL_UAV_BOUNDS } from "@/lib/gis/bounds";

// Free raster tile style — no API key required.
// OpenFreeMap "bright" style: https://openfreemap.org
const FREE_STYLE_URL =
  "https://tiles.openfreemap.org/styles/bright";

export interface MapLibreMapProps {
  /** Initial center [lng, lat] — defaults to Bhopal UAV coverage center */
  center?: [number, number];
  /** Initial zoom level */
  zoom?: number;
  /** MapLibre style URL */
  styleUrl?: string;
  /** CSS height of the map container */
  height?: string;
  /** Called when map finishes loading */
  onLoad?: () => void;
}

export function MapLibreMap({
  center = BHOPAL_MAP_CONFIG.center,
  zoom = BHOPAL_MAP_CONFIG.zoom,
  styleUrl = FREE_STYLE_URL,
  height = "100%",
  onLoad,
}: MapLibreMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // Use unknown to avoid importing maplibre-gl types at module scope
  // (which would fail during SSR)
  const mapRef = useRef<unknown>(null);
  const [mapError, setMapError] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    let cancelled = false;

    (async () => {
      try {
        // Dynamic import — browser only
        const maplibre = await import("maplibre-gl");

        // MapLibre CSS — inject once via link tag to avoid Turbopack CSS import issues
        if (!document.getElementById("maplibre-css")) {
          const link = document.createElement("link");
          link.id   = "maplibre-css";
          link.rel  = "stylesheet";
          link.href = "https://unpkg.com/maplibre-gl@6/dist/maplibre-gl.css";
          document.head.appendChild(link);
        }

        if (cancelled || !containerRef.current) return;

        const map = new maplibre.Map({
          container:   containerRef.current,
          style:       styleUrl,
          center:      center,
          zoom:        zoom,
          minZoom:     BHOPAL_MAP_CONFIG.minZoom,
          maxZoom:     BHOPAL_MAP_CONFIG.maxZoom,
        });

        mapRef.current = map;

        map.addControl(new maplibre.NavigationControl(), "top-right");

        map.on("load", () => {
          if (cancelled) return;
          setIsLoaded(true);
          onLoad?.();

          // Add coverage bounds indicator
          if (!map.getSource("bhopal-bounds")) {
            map.addSource("bhopal-bounds", {
              type: "geojson",
              data: {
                type: "Feature",
                geometry: {
                  type: "Polygon",
                  coordinates: [[
                    [BHOPAL_UAV_BOUNDS.minLon, BHOPAL_UAV_BOUNDS.maxLat],
                    [BHOPAL_UAV_BOUNDS.maxLon, BHOPAL_UAV_BOUNDS.maxLat],
                    [BHOPAL_UAV_BOUNDS.maxLon, BHOPAL_UAV_BOUNDS.minLat],
                    [BHOPAL_UAV_BOUNDS.minLon, BHOPAL_UAV_BOUNDS.minLat],
                    [BHOPAL_UAV_BOUNDS.minLon, BHOPAL_UAV_BOUNDS.maxLat],
                  ]],
                },
                properties: {
                  name: "Bhopal UAV Dataset Coverage",
                },
              },
            });
            map.addLayer({
              id:     "bhopal-bounds-fill",
              type:   "fill",
              source: "bhopal-bounds",
              paint: {
                "fill-color":   "#2D5016",
                "fill-opacity": 0.08,
              },
            });
            map.addLayer({
              id:     "bhopal-bounds-line",
              type:   "line",
              source: "bhopal-bounds",
              paint: {
                "line-color":   "#2D5016",
                "line-width":   2,
                "line-dasharray": [4, 2],
                "line-opacity": 0.6,
              },
            });
          }
        });

        map.on("error", (e) => {
          console.warn("MapLibre error:", e);
        });
      } catch (err) {
        if (!cancelled) {
          console.error("MapLibre load failed:", err);
          setMapError("Map failed to load. Please refresh the page.");
        }
      }
    })();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        (mapRef.current as { remove: () => void }).remove();
        mapRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height }}>
      {/* Map container */}
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%" }}
        role="application"
        aria-label="Interactive map — Bhopal prototype dataset"
      />

      {/* Loading state */}
      {!isLoaded && !mapError && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "var(--color-cream)",
            zIndex: 10,
          }}
          aria-live="polite"
          aria-label="Map loading"
        >
          <div style={{ textAlign: "center", color: "var(--color-soft-gray)" }}>
            <div style={{ fontSize: "0.875rem" }}>Loading map\u2026</div>
          </div>
        </div>
      )}

      {/* Error state */}
      {mapError && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "var(--color-cream)",
            zIndex: 10,
            padding: "1rem",
          }}
          role="alert"
        >
          <p style={{ color: "var(--color-charcoal)", fontSize: "0.875rem" }}>
            {mapError}
          </p>
        </div>
      )}

      {/* Dataset label overlay — PRD requirement: always labeled "Prototype Dataset - Bhopal" */}
      {isLoaded && (
        <div
          style={{
            position: "absolute",
            bottom: "1.5rem",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(247,243,236,0.92)",
            border: "1px solid var(--color-beige)",
            borderRadius: "var(--radius)",
            padding: "0.25rem 0.75rem",
            fontSize: "0.75rem",
            color: "var(--color-charcoal-light)",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            zIndex: 5,
          }}
          aria-label="Dataset label"
        >
          Prototype Dataset \u2014 Bhopal
        </div>
      )}
    </div>
  );
}
