"use client";

/**
 * DrishtiGIS — India-Scale MapLibre Map Component
 * =================================================
 * Client-only. Always consumed via DynamicMap (next/dynamic, ssr:false).
 *
 * India-scale: default center is India overview (zoom 5).
 * Bhopal data layers load lazily when the user zooms into the Bhopal area.
 *
 * Layer stack (back → front):
 *   Base map style
 *   OSM landuse fill
 *   UAV raster tiles (zoom 17+)
 *   OSM buildings fill + outline (zoom 16+)
 *   OSM roads (zoom 13+)
 *   OSM waterways (zoom 13+)
 *   Parcel fills + outlines (zoom 15+)
 *   AI feature fills + outlines (zoom 15+)
 *   Bhopal bounds indicator (always)
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { BHOPAL_UAV_BOUNDS } from "@/lib/gis/bounds";
import { INDIA_CENTER, BHOPAL_CITY_CENTER, distanceKm } from "@/lib/gis/india";
import { getBhopalTileUrl } from "@/lib/api/tiles";
import { getBhopalOsmLayerUrl } from "@/lib/api/osm";
import { API_BASE } from "@/lib/api/client";
import type { LayerVisibility } from "@/lib/gis/coverage";
import { DEFAULT_LAYER_VISIBILITY } from "@/lib/gis/coverage";

const FREE_STYLE_URL = "https://tiles.openfreemap.org/styles/bright";

// Thresholds for lazy source loading
const ZOOM_LOAD_OSM     = 13;
const ZOOM_LOAD_PARCELS = 15;
const BHOPAL_LOAD_RADIUS_KM = 50;  // km from Bhopal city center to load sources

export interface MapLibreMapProps {
  center?:         [number, number];   // default: India center
  zoom?:           number;             // default: 5
  styleUrl?:       string;
  height?:         string;
  onLoad?:         () => void;
  onParcelClick?:  (propertyId: string) => void;
  onNearBhopalChange?: (near: boolean) => void;
  initialLayers?:  LayerVisibility;
}

export function MapLibreMap({
  center        = [INDIA_CENTER.lon, INDIA_CENTER.lat],
  zoom          = INDIA_CENTER.zoom,
  styleUrl      = FREE_STYLE_URL,
  height        = "100%",
  onLoad,
  onParcelClick,
  onNearBhopalChange,
  initialLayers = DEFAULT_LAYER_VISIBILITY,
}: MapLibreMapProps) {
  const containerRef  = useRef<HTMLDivElement>(null);
  const mapRef        = useRef<unknown>(null);
  const layersRef     = useRef<LayerVisibility>(initialLayers);
  const osmLoadedRef  = useRef(false);
  const parcelLoadRef = useRef(false);

  const [isLoaded,  setIsLoaded]  = useState(false);
  const [mapError,  setMapError]  = useState<string | null>(null);

  // Keep layersRef in sync with prop changes
  useEffect(() => {
    layersRef.current = initialLayers;
  }, [initialLayers]);

  // Apply a layer visibility change to the live map
  const applyLayerVisibility = useCallback((
    map: { getLayer: (id: string) => unknown; setLayoutProperty: (id: string, prop: string, val: string) => void },
    layer: keyof LayerVisibility,
    visible: boolean
  ) => {
    const layerIds: Record<keyof LayerVisibility, string[]> = {
      uavImagery:   ["uav-tiles"],
      parcels:      ["parcels-fill", "parcels-line"],
      aiFeatures:   ["ai-features-fill", "ai-features-line"],
      osmBuildings: ["osm-buildings-fill", "osm-buildings-line"],
      osmRoads:     ["osm-roads"],
      osmWaterways: ["osm-waterways"],
      osmLanduse:   ["osm-landuse-fill"],
    };
    for (const id of layerIds[layer]) {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
      }
    }
  }, []);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    let cancelled = false;

    (async () => {
      try {
        const maplibre = await import("maplibre-gl");

        if (!document.getElementById("maplibre-css")) {
          const link = document.createElement("link");
          link.id   = "maplibre-css";
          link.rel  = "stylesheet";
          link.href = "https://unpkg.com/maplibre-gl@6/dist/maplibre-gl.css";
          document.head.appendChild(link);
        }

        if (cancelled || !containerRef.current) return;

        const map = new maplibre.Map({
          container: containerRef.current,
          style:     styleUrl,
          center:    center,
          zoom:      zoom,
          minZoom:   3,
          maxZoom:   22,
        });

        mapRef.current = map;
        map.addControl(new maplibre.NavigationControl(), "top-right");

        // ── Helper: add all Bhopal data sources + layers ──────────────────
        const addOsmSources = () => {
          if (osmLoadedRef.current) return;
          osmLoadedRef.current = true;

          // OSM Landuse
          if (!map.getSource("osm-landuse")) {
            map.addSource("osm-landuse", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("landuse"),
            });
            map.addLayer({
              id: "osm-landuse-fill", type: "fill", source: "osm-landuse",
              minzoom: 14,
              paint: { "fill-color": "#6B7C45", "fill-opacity": 0.12 },
              layout: { visibility: layersRef.current.osmLanduse ? "visible" : "none" },
            });
          }

          // OSM Buildings
          if (!map.getSource("osm-buildings")) {
            map.addSource("osm-buildings", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("buildings"),
            });
            map.addLayer({
              id: "osm-buildings-fill", type: "fill", source: "osm-buildings",
              minzoom: 16,
              paint: { "fill-color": "#EDE8DE", "fill-opacity": 0.6 },
              layout: { visibility: layersRef.current.osmBuildings ? "visible" : "none" },
            });
            map.addLayer({
              id: "osm-buildings-line", type: "line", source: "osm-buildings",
              minzoom: 16,
              paint: { "line-color": "#8A8A8A", "line-width": 0.5 },
              layout: { visibility: layersRef.current.osmBuildings ? "visible" : "none" },
            });
          }

          // OSM Roads
          if (!map.getSource("osm-roads")) {
            map.addSource("osm-roads", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("roads"),
            });
            map.addLayer({
              id: "osm-roads", type: "line", source: "osm-roads",
              minzoom: 13,
              paint: {
                "line-color": "#C4922A",
                "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.5, 17, 2],
              },
              layout: { visibility: layersRef.current.osmRoads ? "visible" : "none" },
            });
          }

          // OSM Waterways
          if (!map.getSource("osm-waterways")) {
            map.addSource("osm-waterways", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("waterways"),
            });
            map.addLayer({
              id: "osm-waterways", type: "line", source: "osm-waterways",
              minzoom: 13,
              paint: { "line-color": "#3A6B1E", "line-width": 1.5 },
              layout: { visibility: layersRef.current.osmWaterways ? "visible" : "none" },
            });
          }
        };

        const addParcelSources = () => {
          if (parcelLoadRef.current) return;
          parcelLoadRef.current = true;

          // UAV Raster Tiles
          if (!map.getSource("uav-tiles")) {
            map.addSource("uav-tiles", {
              type:   "raster",
              tiles:  [getBhopalTileUrl()],
              tileSize: 256,
              minzoom: 18,
              maxzoom: 21,
            });
            map.addLayer({
              id: "uav-tiles", type: "raster", source: "uav-tiles",
              minzoom: 17,
              maxzoom: 22,
              paint: { "raster-opacity": 0.9 },
              layout: { visibility: layersRef.current.uavImagery ? "visible" : "none" },
            });
          }

          // Demo Parcels
          if (!map.getSource("parcels-bhopal")) {
            map.addSource("parcels-bhopal", {
              type: "geojson",
              data: `${API_BASE}/api/v1/parcels?city=Bhopal`,
            });
            map.addLayer({
              id: "parcels-fill", type: "fill", source: "parcels-bhopal",
              minzoom: 15,
              paint: { "fill-color": "#D4A017", "fill-opacity": 0.25 },
              layout: { visibility: layersRef.current.parcels ? "visible" : "none" },
            });
            map.addLayer({
              id: "parcels-line", type: "line", source: "parcels-bhopal",
              minzoom: 15,
              paint: { "line-color": "#2D5016", "line-width": 1.5 },
              layout: { visibility: layersRef.current.parcels ? "visible" : "none" },
            });

            // Parcel click handler
            map.on("click", "parcels-fill", (e) => {
              const feature = e.features?.[0];
              const propertyId = feature?.properties?.property_id as string | undefined;
              if (propertyId && onParcelClick) {
                onParcelClick(propertyId);
              }
            });
            map.on("mouseenter", "parcels-fill", () => {
              map.getCanvas().style.cursor = "pointer";
            });
            map.on("mouseleave", "parcels-fill", () => {
              map.getCanvas().style.cursor = "";
            });
          }

          // AI Features
          if (!map.getSource("ai-features-bhopal")) {
            map.addSource("ai-features-bhopal", {
              type: "geojson",
              data: `${API_BASE}/api/v1/features`,
            });
            map.addLayer({
              id: "ai-features-fill", type: "fill", source: "ai-features-bhopal",
              minzoom: 15,
              paint: { "fill-color": "#C4922A", "fill-opacity": 0.35 },
              layout: { visibility: layersRef.current.aiFeatures ? "visible" : "none" },
            });
            map.addLayer({
              id: "ai-features-line", type: "line", source: "ai-features-bhopal",
              minzoom: 15,
              paint: { "line-color": "#A67820", "line-width": 1 },
              layout: { visibility: layersRef.current.aiFeatures ? "visible" : "none" },
            });
          }
        };

        // ── Map load handler ──────────────────────────────────────────────
        map.on("load", () => {
          if (cancelled) return;
          setIsLoaded(true);
          onLoad?.();

          // Always add Bhopal coverage bounds indicator
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
                properties: { name: "Bhopal UAV Dataset Coverage" },
              },
            });
            map.addLayer({
              id: "bhopal-bounds-fill", type: "fill", source: "bhopal-bounds",
              paint: { "fill-color": "#2D5016", "fill-opacity": 0.08 },
            });
            map.addLayer({
              id: "bhopal-bounds-line", type: "line", source: "bhopal-bounds",
              paint: {
                "line-color": "#2D5016", "line-width": 2,
                "line-dasharray": [4, 2], "line-opacity": 0.6,
              },
            });
          }
        });

        // ── moveend: lazy-load sources when near Bhopal ───────────────────
        map.on("moveend", () => {
          const ctr   = map.getCenter();
          const zm    = map.getZoom();
          const kmToBhopal = distanceKm(
            ctr.lat, ctr.lng,
            BHOPAL_CITY_CENTER.lat, BHOPAL_CITY_CENTER.lon
          );
          const nearBhopal = kmToBhopal <= BHOPAL_LOAD_RADIUS_KM;

          onNearBhopalChange?.(nearBhopal);

          if (nearBhopal && zm >= ZOOM_LOAD_OSM && !osmLoadedRef.current) {
            addOsmSources();
          }
          if (nearBhopal && zm >= ZOOM_LOAD_PARCELS && !parcelLoadRef.current) {
            addParcelSources();
          }
        });

        map.on("error", (e) => { console.warn("MapLibre error:", e); });

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
      osmLoadedRef.current  = false;
      parcelLoadRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Expose layer visibility control to parent ─────────────────────────
  // When initialLayers changes (from LayerControl), update live map layers
  useEffect(() => {
    const map = mapRef.current as {
      getLayer: (id: string) => unknown;
      setLayoutProperty: (id: string, prop: string, val: string) => void;
    } | null;
    if (!map || !isLoaded) return;
    const lv = initialLayers;
    (Object.keys(lv) as (keyof LayerVisibility)[]).forEach((layer) => {
      applyLayerVisibility(map, layer, lv[layer]);
    });
  }, [initialLayers, isLoaded, applyLayerVisibility]);

  return (
    <div style={{ position: "relative", width: "100%", height }}>
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%" }}
        role="application"
        aria-label="Interactive map — DrishtiGIS India"
      />

      {/* Loading */}
      {!isLoaded && !mapError && (
        <div
          style={{
            position: "absolute", inset: 0, display: "flex",
            alignItems: "center", justifyContent: "center",
            background: "var(--color-cream)", zIndex: 10,
          }}
          aria-live="polite"
          aria-label="Map loading"
        >
          <div style={{ textAlign: "center", color: "var(--color-soft-gray)" }}>
            <div style={{ fontSize: "0.875rem" }}>Loading map…</div>
          </div>
        </div>
      )}

      {/* Error */}
      {mapError && (
        <div
          style={{
            position: "absolute", inset: 0, display: "flex",
            alignItems: "center", justifyContent: "center",
            background: "var(--color-cream)", zIndex: 10, padding: "1rem",
          }}
          role="alert"
        >
          <p style={{ color: "var(--color-charcoal)", fontSize: "0.875rem" }}>
            {mapError}
          </p>
        </div>
      )}

      {/* Dataset label */}
      {isLoaded && (
        <div
          style={{
            position: "absolute", bottom: "1.5rem", left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(247,243,236,0.92)",
            border: "1px solid var(--color-beige)",
            borderRadius: "var(--radius)", padding: "0.25rem 0.75rem",
            fontSize: "0.75rem", color: "var(--color-charcoal-light)",
            pointerEvents: "none", whiteSpace: "nowrap", zIndex: 5,
          }}
          aria-label="Dataset label"
        >
          Prototype Dataset \u2014 Bhopal
        </div>
      )}
    </div>
  );
}
