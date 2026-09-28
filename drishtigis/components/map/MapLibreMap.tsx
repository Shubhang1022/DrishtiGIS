"use client";

/**
 * DrishtiGIS — India-Scale MapLibre Map Component
 * =================================================
 * Client-only. Always consumed via DynamicMap (next/dynamic, ssr:false).
 *
 * Layer stack (back → front):
 *   Satellite raster basemap (when active)
 *   Base map style (OpenFreeMap vector)
 *   UAV High-Res raster tiles (Bhopal orthomosaic, z17+)
 *   OSM landuse fill
 *   OSM buildings fill + outline
 *   OSM roads
 *   OSM waterways
 *   Parcel fills + outlines (synthetic demo property records)
 *   AI feature fills + outlines (real UAVPal inference)
 *   Bhopal bounds indicator
 *   Data Coverage navigation points
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { BHOPAL_UAV_BOUNDS, BHOPAL_MAP_CONFIG } from "@/lib/gis/bounds";
import { INDIA_CENTER, BHOPAL_CITY_CENTER, distanceKm, getActiveCoverageCities } from "@/lib/gis/india";
import { getBhopalOsmLayerUrl } from "@/lib/api/osm";
import { API_BASE, getStoredAuthToken } from "@/lib/api/client";
import type { PublishedDatasetItem } from "@/lib/api/datasets";
import type { LayerVisibility, BasemapType } from "@/lib/gis/coverage";
import { DEFAULT_LAYER_VISIBILITY } from "@/lib/gis/coverage";
import type { MapContextState } from "./ContextSidebar";

const FREE_STYLE_URL = "https://tiles.openfreemap.org/styles/bright";

const SATELLITE_TILE_URL =
  process.env.NEXT_PUBLIC_SATELLITE_TILE_URL ||
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

const BHOPAL_LOAD_RADIUS_KM = 50;

export interface MapLibreMapProps {
  center?:         [number, number];   // default: India center
  zoom?:           number;             // default: 5
  styleUrl?:       string;
  height?:         string;
  onLoad?:         () => void;
  onSelectContext?: (ctx: MapContextState) => void;
  onNearBhopalChange?: (near: boolean) => void;
  initialLayers?:  LayerVisibility;
  flyToLocation?:  { center: [number, number]; zoom: number; bounds?: [[number, number], [number, number]] } | null;
  selectedContext?: MapContextState | null;
  userHomeLocation?: { latitude: number; longitude: number; address_label?: string; accuracy_m?: number | null } | null;
  currentLocation?:  { latitude: number; longitude: number; accuracy?: number } | null;
  userProperties?: any[];
  draggableMarkerLocation?: { latitude: number; longitude: number; label?: string } | null;
  onDraggableMarkerMove?: (coords: { latitude: number; longitude: number }) => void;
  publishedDatasets?: PublishedDatasetItem[];
  activePublishedDatasetIds?: string[];
  onRegisteredLayersChange?: (sources: string[], layers: string[]) => void;
}

export function MapLibreMap({
  center        = [INDIA_CENTER.lon, INDIA_CENTER.lat],
  zoom          = INDIA_CENTER.zoom,
  styleUrl      = FREE_STYLE_URL,
  height        = "100%",
  onLoad,
  onSelectContext,
  onNearBhopalChange,
  initialLayers = DEFAULT_LAYER_VISIBILITY,
  flyToLocation,
  selectedContext,
  userHomeLocation,
  currentLocation,
  userProperties = [],
  draggableMarkerLocation,
  onDraggableMarkerMove,
  publishedDatasets = [],
  activePublishedDatasetIds,
  onRegisteredLayersChange,
}: MapLibreMapProps) {
  const containerRef            = useRef<HTMLDivElement>(null);
  const mapRef                  = useRef<any>(null);
  const maplibreglRef           = useRef<any>(null);
  const layersRef               = useRef<LayerVisibility>(initialLayers);
  const homeMarkerRef           = useRef<any>(null);
  const currentLocationMarkerRef = useRef<any>(null);
  const draggableMarkerRef       = useRef<any>(null);
  const userPropertyMarkersRef   = useRef<any[]>([]);

  const [isLoaded,    setIsLoaded]    = useState(false);
  const [mapError,    setMapError]    = useState<string | null>(null);
  const [currentZoom, setCurrentZoom] = useState<number>(zoom);
  const [isNearBhopal, setIsNearBhopal] = useState<boolean>(false);

  const prevRegisteredRef = useRef<{ sources: string[]; layers: string[] }>({ sources: [], layers: [] });

  // Dynamic Published Datasets Effect (Task 8)
  useEffect(() => {
    if (!mapRef.current || !isLoaded) return;
    const map = mapRef.current;

    if (!Array.isArray(publishedDatasets)) return;

    const currentSources: string[] = [];
    const currentLayers: string[] = [];

    publishedDatasets.forEach((ds) => {
      if (!ds.dataset_id) return;
      const sourceId = `dataset-raster-source-${ds.dataset_id}`;
      const layerId = `dataset-raster-layer-${ds.dataset_id}`;
      const tileUrl = ds.tiles_url.startsWith("http") ? ds.tiles_url : `${API_BASE}${ds.tiles_url}`;
      const isVisible = activePublishedDatasetIds ? activePublishedDatasetIds.includes(ds.dataset_id) : true;

      currentSources.push(sourceId);
      currentLayers.push(layerId);

      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: "raster",
          tiles: [tileUrl],
          tileSize: 256,
          minzoom: ds.minzoom || 12,
          maxzoom: ds.maxzoom || 21,
          bounds: ds.bounds || [77.412951, 23.254292, 77.422689, 23.256671],
        });

        // Insert underneath vector layers
        const firstVectorId = map.getLayer("osm-landuse-fill") ? "osm-landuse-fill" : (map.getLayer("osm-buildings-fill") ? "osm-buildings-fill" : undefined);

        map.addLayer(
          {
            id: layerId,
            type: "raster",
            source: sourceId,
            minzoom: ds.minzoom || 12,
            maxzoom: 22,
            paint: {
              "raster-opacity": 1.0,
              "raster-fade-duration": 0,
            },
            layout: { visibility: isVisible ? "visible" : "none" },
          },
          firstVectorId
        );
      } else {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", isVisible ? "visible" : "none");
        }
      }
    });

    const isSame =
      prevRegisteredRef.current.sources.length === currentSources.length &&
      prevRegisteredRef.current.layers.length === currentLayers.length &&
      prevRegisteredRef.current.sources.every((s, i) => s === currentSources[i]) &&
      prevRegisteredRef.current.layers.every((l, i) => l === currentLayers[i]);

    if (!isSame) {
      prevRegisteredRef.current = { sources: currentSources, layers: currentLayers };
      onRegisteredLayersChange?.(currentSources, currentLayers);
    }
  }, [publishedDatasets, activePublishedDatasetIds, isLoaded, onRegisteredLayersChange]);

  // Synchronize layersRef with prop updates
  useEffect(() => {
    layersRef.current = initialLayers;
  }, [initialLayers]);

  // Temporary CURRENT LOCATION GPS Marker Effect (Blue Circular Pulse Pin)
  useEffect(() => {
    if (!mapRef.current || !isLoaded || !maplibreglRef.current) return;
    const maplibregl = maplibreglRef.current;

    if (currentLocationMarkerRef.current) {
      currentLocationMarkerRef.current.remove();
      currentLocationMarkerRef.current = null;
    }

    if (
      currentLocation &&
      Number.isFinite(currentLocation.latitude) &&
      Number.isFinite(currentLocation.longitude) &&
      currentLocation.latitude >= -90 &&
      currentLocation.latitude <= 90 &&
      currentLocation.longitude >= -180 &&
      currentLocation.longitude <= 180
    ) {
      const el = document.createElement("div");
      el.className = "drishti-gps-marker flex flex-col items-center cursor-pointer group z-50";
      el.innerHTML = `
        <div class="px-2 py-0.5 bg-[#2563EB] text-white text-[10px] font-bold rounded-full shadow-lg border border-white flex items-center gap-1 font-sans animate-bounce">
          <span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
          <span>CURRENT LOCATION</span>
        </div>
        <div class="relative flex items-center justify-center mt-1">
          <div class="w-5 h-5 bg-[#3B82F6]/30 rounded-full animate-ping absolute"></div>
          <div class="w-4 h-4 bg-[#2563EB] border-2 border-white rounded-full shadow-md z-10"></div>
        </div>
      `;

      currentLocationMarkerRef.current = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([currentLocation.longitude, currentLocation.latitude])
        .addTo(mapRef.current);
    }
  }, [currentLocation, isLoaded]);

  // Persistent Private HOME Marker Effect (Purple Pin)
  useEffect(() => {
    if (!mapRef.current || !isLoaded || !maplibreglRef.current) return;
    const maplibregl = maplibreglRef.current;

    if (homeMarkerRef.current) {
      homeMarkerRef.current.remove();
      homeMarkerRef.current = null;
    }

    if (
      userHomeLocation &&
      Number.isFinite(userHomeLocation.latitude) &&
      Number.isFinite(userHomeLocation.longitude) &&
      userHomeLocation.latitude >= -90 &&
      userHomeLocation.latitude <= 90 &&
      userHomeLocation.longitude >= -180 &&
      userHomeLocation.longitude <= 180
    ) {
      const el = document.createElement("div");
      el.className = "drishti-home-marker flex flex-col items-center cursor-pointer group z-50";
      el.innerHTML = `
        <div class="px-2.5 py-1 bg-[#7C3AED] text-white text-[11px] font-bold rounded-lg shadow-xl border-2 border-white flex items-center gap-1.5 font-sans tracking-wide">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
          <span>${userHomeLocation.address_label || "HOME"}</span>
        </div>
        <div class="w-3 h-3 bg-[#7C3AED] border-2 border-white rounded-full shadow-md transform rotate-45 -mt-1"></div>
      `;

      homeMarkerRef.current = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat([userHomeLocation.longitude, userHomeLocation.latitude])
        .addTo(mapRef.current);
    }
  }, [userHomeLocation, isLoaded]);

  // Draggable Pin Marker Effect
  useEffect(() => {
    if (!mapRef.current || !isLoaded || !maplibreglRef.current) return;
    const maplibregl = maplibreglRef.current;

    if (draggableMarkerRef.current) {
      draggableMarkerRef.current.remove();
      draggableMarkerRef.current = null;
    }

    if (
      draggableMarkerLocation &&
      Number.isFinite(draggableMarkerLocation.latitude) &&
      Number.isFinite(draggableMarkerLocation.longitude)
    ) {
      const el = document.createElement("div");
      el.className = "drishti-draggable-marker flex flex-col items-center cursor-move group z-50";
      el.innerHTML = `
        <div class="px-2.5 py-1 bg-[#10B981] text-white text-[11px] font-bold rounded-lg shadow-2xl border-2 border-white flex items-center gap-1.5 font-sans animate-pulse">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          <span>${draggableMarkerLocation.label || "DRAG PIN TO ADJUST"}</span>
        </div>
        <div class="w-4 h-4 bg-[#10B981] border-2 border-white rounded-full shadow-lg transform rotate-45 -mt-1"></div>
      `;

      const marker = new maplibregl.Marker({
        element: el,
        anchor: "bottom",
        draggable: true,
      })
        .setLngLat([draggableMarkerLocation.longitude, draggableMarkerLocation.latitude])
        .addTo(mapRef.current);

      const handleDragEnd = () => {
        const lngLat = marker.getLngLat();
        onDraggableMarkerMove?.({ latitude: lngLat.lat, longitude: lngLat.lng });
      };

      marker.on("dragend", handleDragEnd);
      draggableMarkerRef.current = marker;
    }
  }, [draggableMarkerLocation, isLoaded, onDraggableMarkerMove]);

  // Synchronize selection highlight filters with selectedContext
  useEffect(() => {
    if (!mapRef.current || !isLoaded) return;
    const map = mapRef.current;

    const bldgId = selectedContext?.type === "ai-feature" ? String(selectedContext.id) : "___NONE___";
    const parcelId = selectedContext?.type === "parcel" ? String(selectedContext.id) : "___NONE___";

    ["ai-features-highlight-fill", "ai-features-highlight-line"].forEach((l) => {
      if (map.getLayer(l)) {
        map.setFilter(l, ["any", ["==", ["get", "id"], bldgId], ["==", ["get", "building_id"], bldgId]]);
      }
    });

    if (map.getLayer("parcels-highlight")) {
      map.setFilter("parcels-highlight", [
        "any",
        ["==", ["get", "id"], parcelId],
        ["==", ["get", "property_id"], parcelId],
      ]);
    }
  }, [selectedContext, isLoaded]);

  // User Registered Properties Markers Effect
  useEffect(() => {
    if (!mapRef.current || !isLoaded || !maplibreglRef.current) return;
    const maplibregl = maplibreglRef.current;

    userPropertyMarkersRef.current.forEach((m) => m.remove());
    userPropertyMarkersRef.current = [];

    if (Array.isArray(userProperties) && initialLayers.userProperties) {
      userProperties.forEach((prop) => {
        if (!prop || !Number.isFinite(prop.latitude) || !Number.isFinite(prop.longitude)) return;
        const el = document.createElement("div");
        el.className = "drishti-user-prop-marker flex flex-col items-center cursor-pointer group z-40";
        el.innerHTML = `
          <div class="px-2 py-0.5 bg-[#059669] text-white text-[10px] font-bold rounded-md shadow-md border border-white flex items-center gap-1 font-sans">
            <span>🏠 ${prop.title || "User Property"}</span>
          </div>
          <div class="w-2.5 h-2.5 bg-[#059669] border border-white rounded-full shadow-xs -mt-0.5"></div>
        `;

        el.addEventListener("click", () => {
          onSelectContext?.({
            type: "user-property",
            id: prop.id,
            data: prop,
          });
        });

        const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
          .setLngLat([prop.longitude, prop.latitude])
          .addTo(mapRef.current);

        userPropertyMarkersRef.current.push(marker);
      });
    }
  }, [userProperties, isLoaded, initialLayers.userProperties, onSelectContext]);

  // Apply basemap mode (Standard vs Satellite)
  const applyBasemapMode = useCallback((map: any, mode: BasemapType) => {
    if (!map || !map.getStyle()) return;

    if (map.getLayer("satellite-basemap")) {
      map.setLayoutProperty("satellite-basemap", "visibility", mode === "satellite" ? "visible" : "none");
    }

    const customLayerIds = new Set([
      "satellite-basemap", "uav-tiles",
      "osm-landuse-fill", "osm-buildings-fill", "osm-buildings-line",
      "osm-roads", "osm-waterways",
      "parcels-fill", "parcels-line", "parcels-highlight",
      "ai-buildings-fill", "ai-buildings-outline", "ai-buildings-hitbox",
      "ai-features-fill", "ai-features-line",
      "ai-features-highlight-fill", "ai-features-highlight-line",
      "bhopal-bounds-fill", "bhopal-bounds-line",
      "coverage-points-pulse", "coverage-points-circle", "coverage-points-label",
    ]);

    const style = map.getStyle();
    if (style && style.layers) {
      for (const layer of style.layers) {
        if (!customLayerIds.has(layer.id)) {
          if (layer.type === "background") {
            map.setLayoutProperty(layer.id, "visibility", mode === "satellite" ? "none" : "visible");
          } else if (layer.id.includes("landcover") || layer.id.includes("landuse") || layer.id.includes("park") || layer.id.includes("water")) {
            if (layer.type === "fill") {
              map.setLayoutProperty(layer.id, "visibility", mode === "satellite" ? "none" : "visible");
            }
          }
        }
      }
    }
  }, []);

  // Apply layer visibility change to live map
  const applyLayerVisibility = useCallback((
    map: any,
    layer: keyof LayerVisibility,
    visible: any
  ) => {
    if (!map) return;
    if (layer === "basemap") {
      applyBasemapMode(map, visible as BasemapType);
      return;
    }

    if (layer === "buildings" || layer === "buildingSource") {
      const buildingsOn = layer === "buildings" ? Boolean(visible) : layersRef.current.buildings;
      const source = layer === "buildingSource" ? (visible as string) : layersRef.current.buildingSource;
      
      const showAi = buildingsOn && source === "ai";
      const showOsm = buildingsOn && source === "osm";

      [
        "ai-buildings-fill",
        "ai-buildings-outline",
        "ai-buildings-hitbox",
        "ai-features-fill",
        "ai-features-line",
      ].forEach((id) => {
        if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", showAi ? "visible" : "none");
      });
      ["osm-buildings-fill", "osm-buildings-line"].forEach((id) => {
        if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", showOsm ? "visible" : "none");
      });
      return;
    }

    const layerIds: Record<string, string[]> = {
      uavImagery:   ["uav-tiles"],
      parcels:      ["parcels-fill", "parcels-line"],
      aiFeatures:   [
        "ai-buildings-fill",
        "ai-buildings-outline",
        "ai-buildings-hitbox",
        "ai-features-fill",
        "ai-features-line",
      ],
      osmBuildings: ["osm-buildings-fill", "osm-buildings-line"],
      osmRoads:     ["osm-roads"],
      osmWaterways: ["osm-waterways"],
      osmLanduse:   ["osm-landuse-fill"],
      userProperties: [],
    };

    const ids = layerIds[layer as string];
    if (ids) {
      for (const id of ids) {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
        }
      }
    }
  }, [applyBasemapMode]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    let cancelled = false;

    (async () => {
      try {
        const maplibre = await import("maplibre-gl");

        if (typeof (maplibre as any).setWorkerUrl === "function") {
          (maplibre as any).setWorkerUrl("/maplibre-gl-worker.mjs");
        } else if ((maplibre as any).config) {
          (maplibre as any).config.WORKER_URL = "/maplibre-gl-worker.mjs";
        }

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
          transformRequest: (url: string, resourceType?: string) => {
            if (url.startsWith(API_BASE) || url.startsWith("/api/v1")) {
              const token = getStoredAuthToken();
              return {
                url,
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                credentials: "include" as const,
              };
            }
            // OpenFreeMap glyph routing:
            // Route composite font requests like "Open Sans Regular,Arial Unicode MS Regular"
            // to Noto Sans Regular (which is verified 200 OK on openfreemap).
            if (resourceType === "Glyphs" || url.includes("tiles.openfreemap.org/fonts/")) {
              const match = url.match(/\/fonts\/([^/]+)\/([0-9]+-[0-9]+\.pbf)/);
              if (match) {
                const fontName = decodeURIComponent(match[1]);
                if (
                  !fontName.includes("Noto Sans Regular") &&
                  !fontName.includes("Noto Sans Bold") &&
                  !fontName.includes("Noto Sans Italic")
                ) {
                  return {
                    url: url.replace(/\/fonts\/[^/]+\//, "/fonts/Noto%20Sans%20Regular/"),
                  };
                }
              }
            }
            return { url };
          },
        });

        // Resolve missing style images (e.g. OpenFreeMap POI icons like "gate", "atm")
        if (typeof (map as any).setMissingStyleImageResolver === "function") {
          (map as any).setMissingStyleImageResolver(() => {
            return {
              width: 1,
              height: 1,
              data: new Uint8Array([0, 0, 0, 0]),
            };
          });
        }
        map.on("styleimagemissing", (e: any) => {
          const id = e.id;
          if (!map.hasImage(id)) {
            map.addImage(id, {
              width: 1,
              height: 1,
              data: new Uint8Array([0, 0, 0, 0]),
            });
          }
        });

        mapRef.current = map;
        maplibreglRef.current = maplibre;
        map.addControl(new maplibre.NavigationControl(), "top-right");

        map.on("load", () => {
          if (cancelled) return;
          map.resize();
          setIsLoaded(true);
          onLoad?.();

          // Determine first layer ID to insert satellite basemap at bottom
          const layers = map.getStyle()?.layers || [];
          const firstLayerId = layers.length > 0 ? layers[0].id : undefined;

          // 1. Satellite Basemap Raster Layer
          if (!map.getSource("satellite-basemap")) {
            map.addSource("satellite-basemap", {
              type: "raster",
              tiles: [SATELLITE_TILE_URL],
              tileSize: 256,
              maxzoom: 19,
              attribution: "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            });
            map.addLayer(
              {
                id: "satellite-basemap",
                type: "raster",
                source: "satellite-basemap",
                paint: { "raster-opacity": 1.0 },
                layout: { visibility: layersRef.current.basemap === "satellite" ? "visible" : "none" },
              },
              firstLayerId
            );
          }

          // 2. Dynamic UAV Orthomosaic datasets are registered underneath vector layers

          // 3. OSM Landuse
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

            map.on("mouseenter", "osm-landuse-fill", () => {
              map.getCanvas().style.cursor = "pointer";
            });
            map.on("mouseleave", "osm-landuse-fill", () => {
              map.getCanvas().style.cursor = "";
            });
          }

          // 4. OSM Buildings (Reference footprints)
          if (!map.getSource("osm-buildings")) {
            map.addSource("osm-buildings", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("buildings"),
            });
            map.addLayer({
              id: "osm-buildings-fill", type: "fill", source: "osm-buildings",
              minzoom: 13,
              paint: { "fill-color": "#64748B", "fill-opacity": 0.25 },
              layout: { visibility: layersRef.current.osmBuildings ? "visible" : "none" },
            });
            map.addLayer({
              id: "osm-buildings-line", type: "line", source: "osm-buildings",
              minzoom: 13,
              paint: { "line-color": "#334155", "line-width": 1.2 },
              layout: { visibility: layersRef.current.osmBuildings ? "visible" : "none" },
            });


            map.on("mouseenter", "osm-buildings-fill", () => {
              map.getCanvas().style.cursor = "pointer";
            });
            map.on("mouseleave", "osm-buildings-fill", () => {
              map.getCanvas().style.cursor = "";
            });
          }

          // 5. OSM Roads & Waterways
          if (!map.getSource("osm-roads")) {
            map.addSource("osm-roads", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("roads"),
            });
            map.addLayer({
              id: "osm-roads", type: "line", source: "osm-roads",
              minzoom: 12,
              paint: {
                "line-color": "#E67E22",
                "line-width": ["interpolate", ["linear"], ["zoom"], 12, 1, 17, 3],
              },
              layout: { visibility: layersRef.current.osmRoads ? "visible" : "none" },
            });
            // Transparent 16px wide interaction hit area for reliable road clicking
            map.addLayer({
              id: "osm-roads-hit-area", type: "line", source: "osm-roads",
              minzoom: 12,
              paint: {
                "line-color": "#000000",
                "line-width": 16,
                "line-opacity": 0,
              },
              layout: { visibility: layersRef.current.osmRoads ? "visible" : "none" },
            });


            map.on("mouseenter", "osm-roads", () => { map.getCanvas().style.cursor = "pointer"; });
            map.on("mouseleave", "osm-roads", () => { map.getCanvas().style.cursor = ""; });
            map.on("mouseenter", "osm-roads-hit-area", () => { map.getCanvas().style.cursor = "pointer"; });
            map.on("mouseleave", "osm-roads-hit-area", () => { map.getCanvas().style.cursor = ""; });
          }

          if (!map.getSource("osm-waterways")) {
            map.addSource("osm-waterways", {
              type: "geojson",
              data: getBhopalOsmLayerUrl("waterways"),
            });
            map.addLayer({
              id: "osm-waterways", type: "line", source: "osm-waterways",
              minzoom: 12,
              paint: { "line-color": "#2980B9", "line-width": 2 },
              layout: { visibility: layersRef.current.osmWaterways ? "visible" : "none" },
            });
          }

          // 6. Synthetic Demo Property Records (Phase 5.5)
          // Styled with amber dashed outline + light yellow fill to visually distinguish
          // from official cadastral layers. Labelled "Demo Property Records" — NOT official.
          if (!map.getSource("parcels-bhopal")) {
            map.addSource("parcels-bhopal", {
              type: "geojson",
              data: `${API_BASE}/api/v1/parcels?city=Bhopal`,
            });
            map.addLayer({
              id: "parcels-fill", type: "fill", source: "parcels-bhopal",
              minzoom: 13,
              paint: { "fill-color": "#FBBF24", "fill-opacity": 0.15 },
              layout: { visibility: layersRef.current.parcels ? "visible" : "none" },
            });
            map.addLayer({
              id: "parcels-line", type: "line", source: "parcels-bhopal",
              minzoom: 13,
              paint: { "line-color": "#D97706", "line-width": 1.8, "line-dasharray": [4, 2] },
              layout: { visibility: layersRef.current.parcels ? "visible" : "none" },
            });
            map.addLayer({
              id: "parcels-highlight", type: "line", source: "parcels-bhopal",
              minzoom: 13,
              paint: { "line-color": "#B45309", "line-width": 4.0 },
              filter: ["==", ["get", "id"], "___NONE___"],
            });


            map.on("mouseenter", "parcels-fill", () => {
              map.getCanvas().style.cursor = "pointer";
            });
            map.on("mouseleave", "parcels-fill", () => {
              map.getCanvas().style.cursor = "";
            });
          }

          // 7. AI Buildings Layer (real UAVPal inference output — 834 individual footprints)
          // Dedicated MapLibre layers: ai-buildings-fill, ai-buildings-outline, ai-buildings-hitbox
          // Rendered above parcels (z13+) so every individual building is independently clickable
          if (!map.getSource("ai-features-bhopal")) {
            map.addSource("ai-features-bhopal", {
              type: "geojson",
              data: `${API_BASE}/api/v1/features`,
            });

            // Primary visible AI building fill (rendered on top of parcels at z13+)
            map.addLayer({
              id: "ai-buildings-fill", type: "fill", source: "ai-features-bhopal",
              minzoom: 13,
              paint: {
                "fill-color": [
                  "match", ["get", "parcel_relationship"],
                  "FULLY_WITHIN",       "#0D9488",   // teal-600
                  "CROSSES_BOUNDARY",   "#D97706",   // amber-600
                  "PARTIALLY_OVERLAPS", "#F59E0B",   // amber-400
                  /* default */ "#0D9488",            // teal for unmatched
                ],
                "fill-opacity": 0.35,
              },
              layout: { visibility: (layersRef.current.aiFeatures || (layersRef.current.buildings && layersRef.current.buildingSource === "ai")) ? "visible" : "none" },
            });

            // Backward-compatible alias layer
            map.addLayer({
              id: "ai-features-fill", type: "fill", source: "ai-features-bhopal",
              minzoom: 13,
              paint: {
                "fill-color": [
                  "match", ["get", "parcel_relationship"],
                  "FULLY_WITHIN",       "#0D9488",
                  "CROSSES_BOUNDARY",   "#D97706",
                  "PARTIALLY_OVERLAPS", "#F59E0B",
                  /* default */ "#0D9488",
                ],
                "fill-opacity": 0.01,
              },
              layout: { visibility: (layersRef.current.aiFeatures || (layersRef.current.buildings && layersRef.current.buildingSource === "ai")) ? "visible" : "none" },
            });

            // Transparent hitbox layer (8px wide clickable stroke)
            map.addLayer({
              id: "ai-buildings-hitbox", type: "line", source: "ai-features-bhopal",
              minzoom: 13,
              paint: {
                "line-color": "#0D9488",
                "line-width": 8.0,
                "line-opacity": 0.0,
              },
              layout: { visibility: (layersRef.current.aiFeatures || (layersRef.current.buildings && layersRef.current.buildingSource === "ai")) ? "visible" : "none" },
            });

            // Visible building outline
            map.addLayer({
              id: "ai-buildings-outline", type: "line", source: "ai-features-bhopal",
              minzoom: 13,
              paint: {
                "line-color": [
                  "match", ["get", "parcel_relationship"],
                  "FULLY_WITHIN",       "#0F766E",   // teal-700
                  "CROSSES_BOUNDARY",   "#B45309",   // amber-700
                  "PARTIALLY_OVERLAPS", "#92400E",   // amber-800
                  /* default */ "#0F766E",
                ],
                "line-width": 1.5,
              },
              layout: { visibility: (layersRef.current.aiFeatures || (layersRef.current.buildings && layersRef.current.buildingSource === "ai")) ? "visible" : "none" },
            });

            // Backward-compatible alias outline
            map.addLayer({
              id: "ai-features-line", type: "line", source: "ai-features-bhopal",
              minzoom: 13,
              paint: { "line-color": "#0F766E", "line-width": 1.0, "line-opacity": 0.01 },
              layout: { visibility: (layersRef.current.aiFeatures || (layersRef.current.buildings && layersRef.current.buildingSource === "ai")) ? "visible" : "none" },
            });

            // Highlight fill and line
            map.addLayer({
              id: "ai-features-highlight-fill", type: "fill", source: "ai-features-bhopal",
              minzoom: 13,
              paint: { "fill-color": "#14B8A6", "fill-opacity": 0.60 },
              filter: ["==", ["get", "id"], "___NONE___"],
            });
            map.addLayer({
              id: "ai-features-highlight-line", type: "line", source: "ai-features-bhopal",
              minzoom: 13,
              paint: { "line-color": "#0F766E", "line-width": 3.5 },
              filter: ["==", ["get", "id"], "___NONE___"],
            });

            ["ai-buildings-fill", "ai-buildings-hitbox", "ai-features-fill"].forEach((layerId) => {
              map.on("mouseenter", layerId, () => {
                map.getCanvas().style.cursor = "pointer";
              });
              map.on("mouseleave", layerId, () => {
                map.getCanvas().style.cursor = "";
              });
            });
          }

          // 8. Bhopal Bounds Indicator Box
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

          // 9. Data Coverage Navigation Points
          const activeCoverageCities = getActiveCoverageCities();
          const coverageGeoJSON = {
            type: "FeatureCollection" as const,
            features: activeCoverageCities.map((c) => ({
              type: "Feature" as const,
              properties: {
                city: c.name,
                state: c.state,
                status: c.coverage.coverage_source,
                statusLabel: c.coverage.coverage_source === "prototype" ? "Prototype Dataset" : "Data Available",
                imagery: c.coverage.imagery_available,
                parcels: c.coverage.parcel_data_available,
                ai: c.coverage.ai_analysis_available,
                centerLat: c.center.lat,
                centerLon: c.center.lon,
                zoom: c.zoom_level,
                bounds: c.bounds ? JSON.stringify(c.bounds) : null,
              },
              geometry: {
                type: "Point" as const,
                coordinates: [c.center.lon, c.center.lat],
              },
            })),
          };

          if (!map.getSource("coverage-points")) {
            map.addSource("coverage-points", {
              type: "geojson",
              data: coverageGeoJSON,
            });

            map.addLayer({
              id: "coverage-points-pulse",
              type: "circle",
              source: "coverage-points",
              maxzoom: 15,
              paint: {
                "circle-radius": 14,
                "circle-color": "#2D5016",
                "circle-opacity": 0.18,
                "circle-stroke-width": 1.5,
                "circle-stroke-color": "#B7862E",
                "circle-stroke-opacity": 0.5,
              },
            });

            map.addLayer({
              id: "coverage-points-circle",
              type: "circle",
              source: "coverage-points",
              maxzoom: 15,
              paint: {
                "circle-radius": 7,
                "circle-color": "#0E5A3A",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#F6F2EA",
              },
            });

            map.addLayer({
              id: "coverage-points-label",
              type: "symbol",
              source: "coverage-points",
              maxzoom: 15,
              layout: {
                "text-field": ["concat", ["get", "city"], "\n", ["get", "statusLabel"]],
                "text-size": 11,
                "text-offset": [0, 1.4],
                "text-anchor": "top",
                "text-justify": "center",
              },
              paint: {
                "text-color": "#23211E",
                "text-halo-color": "#F6F2EA",
                "text-halo-width": 1.5,
              },
            });

            map.on("mouseenter", "coverage-points-circle", () => {
              map.getCanvas().style.cursor = "pointer";
            });
            map.on("mouseleave", "coverage-points-circle", () => {
              map.getCanvas().style.cursor = "";
            });


          }

          // ── DETERMINISTIC VECTOR FEATURE SELECTION (Phase 24.9) ─────────────
          const INTERACTIVE_LAYER_IDS = [
            "ai-buildings-fill",
            "ai-buildings-hitbox",
            "ai-features-fill",
            "parcels-fill",
            "osm-buildings-fill",
            "osm-roads",
            "osm-roads-hit-area",
            "osm-landuse-fill",
            "coverage-points-circle",
          ];

          const PRIORITY_ORDER: Record<string, number> = {
            "ai-buildings-fill": 1,
            "ai-buildings-hitbox": 1,
            "ai-features-fill": 1,
            "parcels-fill": 2,
            "osm-buildings-fill": 3,
            "osm-roads": 4,
            "osm-roads-hit-area": 4,
            "osm-landuse-fill": 5,
            "coverage-points-circle": 6,
          };

          map.on("click", (e: any) => {
            // Priority 1: Check AI Building click directly with hit tolerance bbox
            // If the user clicks on an AI building: ONLY the building interaction executes, parcel never opens!
            const isAiBuildingVisible = layersRef.current.aiFeatures || (layersRef.current.buildings && layersRef.current.buildingSource === "ai");
            const buildingLayers = ["ai-buildings-fill", "ai-buildings-hitbox", "ai-features-fill"].filter((id) => map.getLayer(id));
            if (isAiBuildingVisible && buildingLayers.length > 0) {
              const bbox: [any, any] = [
                [e.point.x - 4, e.point.y - 4],
                [e.point.x + 4, e.point.y + 4],
              ];
              const buildingFeatures = map.queryRenderedFeatures(bbox, { layers: buildingLayers });
              if (buildingFeatures && buildingFeatures.length > 0) {
                const bldg = buildingFeatures[0];
                const props = bldg.properties || {};
                const bldgId = props.building_id || props.id || "AI-001";
                if (onSelectContext) {
                  onSelectContext({
                    type: "ai-feature",
                    id: String(bldgId),
                    data: props,
                  });
                }
                // STOP immediately! Never proceed to parcel selection when clicking a building!
                return;
              }
            }

            const availableLayers = INTERACTIVE_LAYER_IDS.filter((id) => map.getLayer(id));
            if (availableLayers.length === 0) return;

            const features = map.queryRenderedFeatures(e.point, { layers: availableLayers });
            if (!features || features.length === 0) {
              // Clicked on UAV raster imagery, standard tiles, or empty canvas -> NEVER select raster
              return;
            }

            // Sort deterministically by project priority
            features.sort((a: any, b: any) => {
              const pA = PRIORITY_ORDER[a.layer?.id || ""] || 99;
              const pB = PRIORITY_ORDER[b.layer?.id || ""] || 99;
              return pA - pB;
            });

            const top = features[0];
            const layerId = top.layer?.id;
            const props = top.properties || {};

            if (layerId === "ai-buildings-fill" || layerId === "ai-buildings-hitbox" || layerId === "ai-features-fill") {
              const bldgId = props.building_id || props.id || "AI-001";
              if (onSelectContext) {
                onSelectContext({
                  type: "ai-feature",
                  id: String(bldgId),
                  data: props,
                });
              }
            } else if (layerId === "parcels-fill") {
              const propId = (props.property_id as string) || (props.id as string);
              if (propId && onSelectContext) {
                onSelectContext({ type: "parcel", id: propId, data: props });
              }
            } else if (layerId === "osm-buildings-fill") {
              const bldgId = props.osm_id || props.id || `OSM-BLDG-${top.id || "001"}`;
              if (onSelectContext) {
                onSelectContext({
                  type: "osm-feature",
                  id: String(bldgId),
                  data: {
                    ...props,
                    osm_id: String(bldgId),
                    featureType: "Building",
                    geometryType: top.geometry?.type || "Polygon",
                    source: "OpenStreetMap",
                    source_type: "REFERENCE_GIS",
                  },
                });
              }
            } else if (layerId === "osm-roads" || layerId === "osm-roads-hit-area") {
              if (onSelectContext) {
                onSelectContext({
                  type: "road",
                  id: props.osm_id || props.id || "ROAD-001",
                  data: {
                    ...props,
                    source: "OpenStreetMap (Reference GIS)",
                    source_type: "REFERENCE_GIS",
                  },
                });
              }
            } else if (layerId === "osm-landuse-fill") {
              if (onSelectContext) {
                onSelectContext({
                  type: "landuse",
                  id: props.osm_id || props.id || "LU-001",
                  data: {
                    ...props,
                    source: "OpenStreetMap (Reference GIS)",
                    source_type: "REFERENCE_GIS",
                  },
                });
              }
            } else if (layerId === "coverage-points-circle") {
              if (onSelectContext) {
                onSelectContext({
                  type: "coverage",
                  id: props.city || "Bhopal",
                  data: props,
                });
              }
            }
          });

          // Initial Basemap mode application
          applyBasemapMode(map, layersRef.current.basemap);
        });

        // ── Navigation & Zoom Event Tracking ─────────────────────────────────
        map.on("moveend", () => {
          const ctr = map.getCenter();
          const zm  = map.getZoom();
          setCurrentZoom(zm);

          const kmToBhopal = distanceKm(
            ctr.lat, ctr.lng,
            BHOPAL_CITY_CENTER.lat, BHOPAL_CITY_CENTER.lon
          );
          const nearBhopal = kmToBhopal <= BHOPAL_LOAD_RADIUS_KM;
          setIsNearBhopal(nearBhopal);
          onNearBhopalChange?.(nearBhopal);
        });

        // Handle missing map style sprite icons cleanly
        map.on("styleimagemissing", (e: any) => {
          const id = e?.id;
          if (id && !map.hasImage(id)) {
            try {
              const canvas = document.createElement("canvas");
              canvas.width = 1;
              canvas.height = 1;
              const ctx = canvas.getContext("2d");
              if (ctx) {
                ctx.fillStyle = "rgba(0, 0, 0, 0)";
                ctx.fillRect(0, 0, 1, 1);
                const imageData = ctx.getImageData(0, 0, 1, 1);
                map.addImage(id, imageData);
              }
            } catch {
              // Ignore fallback canvas errors
            }
          }
        });

        map.on("error", (e: any) => {
          const msg = e?.error?.message || e?.message || (typeof e === "string" ? e : "");
          if (msg && !msg.includes("glyph") && !msg.includes("sprite") && !msg.includes("image") && !msg.includes("404")) {
            console.warn("MapLibre event warning:", msg);
          }
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
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Smooth flyTo / fitBounds Camera Animation ─────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isLoaded || !flyToLocation) return;

    if (flyToLocation.bounds) {
      map.fitBounds(flyToLocation.bounds, { padding: 50, maxZoom: 18, duration: 2000 });
    } else {
      map.flyTo({
        center: flyToLocation.center,
        zoom: flyToLocation.zoom,
        duration: 2000,
        essential: true,
      });
    }
  }, [flyToLocation, isLoaded]);

  // ── Apply Layer Visibility and Basemap changes to Live Map ───────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isLoaded) return;

    const lv = initialLayers;
    (Object.keys(lv) as (keyof LayerVisibility)[]).forEach((layer) => {
      applyLayerVisibility(map, layer, lv[layer]);
    });
  }, [initialLayers, isLoaded, applyLayerVisibility]);

  // ── Apply Selection Geometry Highlighting ────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isLoaded) return;

    if (map.getLayer("parcels-highlight")) {
      if (selectedContext?.type === "parcel") {
        map.setFilter("parcels-highlight", [
          "any",
          ["==", ["get", "property_id"], selectedContext.id],
          ["==", ["get", "id"], selectedContext.id],
        ]);
      } else {
        map.setFilter("parcels-highlight", ["==", ["get", "id"], "___NONE___"]);
      }
    }

    if (map.getLayer("ai-features-highlight-fill") && map.getLayer("ai-features-highlight-line")) {
      if (selectedContext?.type === "ai-feature") {
        map.setFilter("ai-features-highlight-fill", ["==", ["get", "id"], selectedContext.id]);
        map.setFilter("ai-features-highlight-line", ["==", ["get", "id"], selectedContext.id]);
      } else {
        map.setFilter("ai-features-highlight-fill", ["==", ["get", "id"], "___NONE___"]);
        map.setFilter("ai-features-highlight-line", ["==", ["get", "id"], "___NONE___"]);
      }
    }
  }, [selectedContext, isLoaded]);

  const handleZoomToUav = () => {
    if (mapRef.current) {
      mapRef.current.fitBounds(BHOPAL_MAP_CONFIG.bounds, { padding: 50, maxZoom: 18, duration: 1800 });
    }
  };

  return (
    <div style={{ position: "relative", width: "100%", height }}>
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%" }}
        role="application"
        aria-label="Interactive map — DrishtiGIS India"
      />

      {/* Loading overlay */}
      {!isLoaded && !mapError && (
        <div
          style={{
            position: "absolute", inset: 0, display: "flex",
            alignItems: "center", justifyContent: "center",
            background: "#F7F3EC", zIndex: 10,
          }}
          aria-live="polite"
          aria-label="Map loading"
        >
          <div style={{ textAlign: "center", color: "#8A8A8A" }}>
            <div style={{ fontSize: "0.875rem", fontWeight: 500 }}>Initializing WebGIS Engine…</div>
          </div>
        </div>
      )}

      {/* Error overlay */}
      {mapError && (
        <div
          style={{
            position: "absolute", inset: 0, display: "flex",
            alignItems: "center", justifyContent: "center",
            background: "#F7F3EC", zIndex: 10, padding: "1rem",
          }}
          role="alert"
        >
          <p style={{ color: "#2C2C2C", fontSize: "0.875rem" }}>{mapError}</p>
        </div>
      )}

      {/* Zoom Prompt Banner when UAV layer is enabled but map is zoomed out */}
      {isLoaded && initialLayers.uavImagery && isNearBhopal && currentZoom < 17 && (
        <div
          style={{
            position: "absolute", top: "1rem", left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(14, 90, 58, 0.95)",
            color: "#F6F2EA",
            borderRadius: "8px", padding: "0.4rem 0.9rem",
            fontSize: "0.75rem", fontWeight: 600,
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            zIndex: 15, display: "flex", alignItems: "center", gap: "0.5rem",
          }}
        >
          <span>Zoom in (z17+) to view high-res UAV Orthomosaic (0.02m)</span>
          <button
            onClick={handleZoomToUav}
            style={{
              background: "#F6F2EA", color: "#0E5A3A",
              border: "none", borderRadius: "4px",
              padding: "2px 8px", fontSize: "0.7rem",
              fontWeight: 700, cursor: "pointer",
            }}
          >
            Zoom to UAV Extent →
          </button>
        </div>
      )}

      {/* Dataset Label */}
      {isLoaded && (
        <div
          style={{
            position: "absolute", bottom: "1.5rem", left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(247,243,236,0.92)",
            border: "1px solid #E4DBCF",
            borderRadius: "6px", padding: "0.25rem 0.75rem",
            fontSize: "0.75rem", color: "#2C2C2C",
            pointerEvents: "none", whiteSpace: "nowrap", zIndex: 5,
            boxShadow: "0 2px 6px rgba(0,0,0,0.05)",
          }}
          aria-label="Dataset label"
        >
          Prototype Dataset &mdash; Bhopal UAV (0.02m)
        </div>
      )}
    </div>
  );
}
