"use client";

import { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { 
  MapPin, 
  Compass, 
  ShieldCheck, 
  ChevronDown, 
  Crosshair,
  SlidersHorizontal,
  Home,
  LogOut,
  UserCheck,
  User,
  Trash2,
  Move,
  CheckCircle2,
  Bot,
  Sparkles
} from "lucide-react";

import type { MapLibreMapProps } from "@/components/map/MapLibreMap";
import { LayerControl } from "@/components/map/LayerControl";
import { ContextSidebar, type MapContextState } from "@/components/map/ContextSidebar";
import { LocationSearch } from "./LocationSearch";
import { LocationConsentModal } from "@/components/map/LocationConsentModal";
import { useAuth } from "@/lib/auth/Context";
import { fetchUserHome, saveUserHome, deleteUserHome, type UserHomeData } from "@/lib/api/userHome";
import { fetchUserProperties, fetchPublicUserProperties, type UserPropertyData } from "@/lib/api/userProperties";
import { fetchPublishedDatasets, type PublishedDatasetItem } from "@/lib/api/datasets";
import { RasterDebugPanel } from "@/components/map/RasterDebugPanel";
import { AssistantChatWidget } from "@/components/assistant/AssistantChatWidget";
import type { MapAction } from "@/lib/types/assistant";
import type { LayerVisibility } from "@/lib/gis/coverage";
import { DEFAULT_LAYER_VISIBILITY } from "@/lib/gis/coverage";
import { INDIA_CENTER } from "@/lib/gis/india";

function MapSkeleton() {
  return (
    <div
      className="w-full h-full bg-[#F7F3EC] flex flex-col items-center justify-center gap-3"
      role="status"
      aria-label="Loading map canvas"
    >
      <div className="w-10 h-10 rounded-full border-3 border-[#E8E0D0] border-t-[#2D5016] animate-spin" />
      <p className="text-xs text-[#8A8A8A] font-medium tracking-wide">
        Initializing MapLibre WebGIS Engine…
      </p>
    </div>
  );
}

const MapLibreMapDynamic = dynamic(
  () => import("@/components/map/MapLibreMap").then((m) => m.MapLibreMap),
  { ssr: false, loading: () => <MapSkeleton /> }
) as React.ComponentType<MapLibreMapProps>;

export function MapCanvas() {
  const { user, token, logout } = useAuth();
  const [layers, setLayers] = useState<LayerVisibility>(DEFAULT_LAYER_VISIBILITY);
  const [mapContext, setMapContext] = useState<MapContextState | null>(null);
  const [nearBhopal, setNearBhopal] = useState(false);
  const [showLayerControl, setShowLayerControl] = useState(true);
  const [showAssistantChat, setShowAssistantChat] = useState(false);

  // User Home & GPS Consent state
  const [userHome, setUserHome] = useState<UserHomeData | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{ latitude: number; longitude: number; accuracy: number } | null>(null);
  const [tempGpsCoords, setTempGpsCoords] = useState<{ latitude: number; longitude: number; accuracy: number } | null>(null);
  const [isConsentModalOpen, setIsConsentModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // User Registered Properties
  const [userProperties, setUserProperties] = useState<UserPropertyData[]>([]);

  // Dynamic Published Datasets & Raster Diagnostics state (Task 7 & 11)
  const [publishedDatasets, setPublishedDatasets] = useState<PublishedDatasetItem[]>([]);
  const [activePublishedDatasetIds, setActivePublishedDatasetIds] = useState<string[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [registeredSources, setRegisteredSources] = useState<string[]>([]);
  const [registeredLayers, setRegisteredLayers] = useState<string[]>([]);
  const [isMapLoaded, setIsMapLoaded] = useState(false);

  // Draggable Pin adjustment mode
  const [draggablePin, setDraggablePin] = useState<{ latitude: number; longitude: number; label?: string; mode: "home" | "property" } | null>(null);

  // Property ID Quick Search & Camera Control
  const [propertySearchInput, setPropertySearchInput] = useState("");
  const [flyTo, setFlyTo] = useState<{ center: [number, number]; zoom: number; bounds?: [[number, number], [number, number]] } | null>(null);

  // Fetch Published Datasets on Mount & Handle URL Query dataset_id (Task 7 & 10)
  useEffect(() => {
    let isMounted = true;

    const loadPublished = async () => {
      try {
        const res = await fetchPublishedDatasets();
        if (!isMounted) return;
        setPublishedDatasets(res.datasets);
        const ids = res.datasets.map((d) => d.dataset_id);
        setActivePublishedDatasetIds(ids);

        // Check for URL query param dataset_id (e.g. from Admin "View on Map" action)
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          const urlDatasetId = params.get("dataset_id");
          if (urlDatasetId) {
            const match = res.datasets.find((d) => d.dataset_id === urlDatasetId);
            if (match && match.bounds) {
              setSelectedDatasetId(match.dataset_id);
              setFlyTo({
                center: [(match.bounds[0] + match.bounds[2]) / 2, (match.bounds[1] + match.bounds[3]) / 2],
                zoom: 17,
                bounds: [
                  [match.bounds[0], match.bounds[1]],
                  [match.bounds[2], match.bounds[3]],
                ],
              });
            }
          }
        }
      } catch (err) {
        console.error("Failed to load published datasets:", err);
      }
    };

    loadPublished();
    return () => {
      isMounted = false;
    };
  }, []);

  // Load User HOME & User Properties on mount & account change
  useEffect(() => {
    // Immediately clear all ephemeral GPS and previous user's location state
    setTempGpsCoords(null);
    setCurrentLocation(null);
    setDraggablePin(null);
    setUserHome(null); // CRITICAL: Never retain previous user's HOME marker

    // Sanitize any legacy un-scoped location keys in localStorage
    if (typeof window !== "undefined") {
      try {
        const legacyKeys = ["homeLocation", "HOME_LOCATION", "savedHome", "userHome", "home_lat", "home_lng", "lastLocation"];
        legacyKeys.forEach((k) => localStorage.removeItem(k));
      } catch {}
    }

    if (!token || !user) {
      return;
    }

    let isMounted = true;

    // Load HOME strictly for the authenticated user
    fetchUserHome(token).then((homeData) => {
      if (!isMounted) return;
      // Scoping verification: HOME must belong to the active user
      if (homeData && homeData.user_id === user.user_id) {
        setUserHome(homeData);
      } else if (homeData && !homeData.user_id) {
        setUserHome(homeData);
      } else {
        setUserHome(null);
      }
      // CRITICAL REQUIREMENT 1: NEVER call setFlyTo here!
      // Map view must remain the default neutral India-level geographic overview.
    });

    // Load Properties
    const loadProps = async () => {
      const myProps = token ? await fetchUserProperties(token) : [];
      const pubProps = await fetchPublicUserProperties();
      const combinedMap = new Map<string, any>();
      pubProps.forEach((p) => { if (p.id) combinedMap.set(p.id, p); });
      myProps.forEach((p) => { if (p.id) combinedMap.set(p.id, p); });
      if (isMounted) {
        setUserProperties(Array.from(combinedMap.values()));
      }
    };
    loadProps();

    return () => { isMounted = false; };
  }, [token, user?.user_id]);

  const handleLayerChange = useCallback(
    (layer: keyof LayerVisibility, visible: any) => {
      setLayers((prev) => ({ ...prev, [layer]: visible }));
    },
    []
  );

  const handleRegisteredLayersChange = useCallback((sources: string[], layers: string[]) => {
    setRegisteredSources((prev) => {
      if (prev.length === sources.length && prev.every((s, i) => s === sources[i])) return prev;
      return sources;
    });
    setRegisteredLayers((prev) => {
      if (prev.length === layers.length && prev.every((l, i) => l === layers[i])) return prev;
      return layers;
    });
  }, []);

  const handleCitySelect = useCallback(
    (lat: number, lon: number, zoom: number, bounds?: [[number, number], [number, number]]) => {
      setFlyTo({ center: [lon, lat], zoom, bounds });
    },
    []
  );

  const handlePropertySearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!propertySearchInput.trim()) return;
    const formattedId = propertySearchInput.trim().toUpperCase();
    setMapContext({ type: "parcel", id: formattedId });
  };

  const handleExecuteAssistantAction = useCallback((action: MapAction) => {
    if (action.action === "SHOW_LAYER" && action.target_id) {
      const tid = action.target_id.toLowerCase();
      if (tid === "imagery") {
        setLayers((prev) => ({ ...prev, imagery: true }));
      } else if (tid === "parcels") {
        setLayers((prev) => ({ ...prev, parcels: true }));
      } else if (tid === "roads") {
        setLayers((prev) => ({ ...prev, roads: true }));
      } else if (tid === "landuse") {
        setLayers((prev) => ({ ...prev, landuse: true }));
      } else if (tid === "ai_buildings" || tid === "buildings") {
        setLayers((prev) => ({ ...prev, buildings: true }));
      } else if (tid === "discrepancies") {
        setLayers((prev) => ({ ...prev, parcels: true, buildings: true }));
      }
    } else if (action.action === "ZOOM_TO_FEATURE" || action.action === "SELECT_FEATURE") {
      if (action.target_id) {
        setMapContext({ type: "parcel", id: action.target_id.toUpperCase() });
      }
    }
  }, []);

  // GPS Consent Granted Callback
  const handleConsentGranted = (coords: { latitude: number; longitude: number; accuracy: number }) => {
    setCurrentLocation(coords);
    setTempGpsCoords(coords);
    setFlyTo({
      center: [coords.longitude, coords.latitude],
      zoom: 16,
    });
  };

  // Save current device/temp GPS position as HOME
  const handleSaveHome = async (lat?: number, lon?: number) => {
    const targetLat = lat ?? tempGpsCoords?.latitude ?? currentLocation?.latitude;
    const targetLon = lon ?? tempGpsCoords?.longitude ?? currentLocation?.longitude;
    if (targetLat === undefined || targetLon === undefined) return;

    try {
      const saved = await saveUserHome(
        token,
        targetLat,
        targetLon,
        "HOME",
        tempGpsCoords?.accuracy ?? currentLocation?.accuracy
      );
      setUserHome(saved);
      setTempGpsCoords(null);
      setDraggablePin(null);
    } catch (err: any) {
      alert(err.message || "Failed to save HOME location");
    }
  };

  // Start "Move HOME" mode with draggable pin
  const handleStartMoveHome = () => {
    if (userHome) {
      setDraggablePin({
        latitude: userHome.latitude,
        longitude: userHome.longitude,
        label: "DRAG PIN TO ADJUST HOME",
        mode: "home",
      });
      setFlyTo({
        center: [userHome.longitude, userHome.latitude],
        zoom: 17,
      });
    }
  };

  // Center map on saved HOME
  const handleCenterOnHome = () => {
    if (userHome) {
      setFlyTo({
        center: [userHome.longitude, userHome.latitude],
        zoom: 17,
      });
    }
  };

  // Delete saved HOME
  const handleDeleteHome = async () => {
    if (confirm("Are you sure you want to delete your private HOME location marker?")) {
      await deleteUserHome(token);
      setUserHome(null);
      setDraggablePin(null);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#F7F3EC] select-none">
      
      {/* ── Top Navigation Bar ────────────────────────────────────────────── */}
      <header className="h-13 bg-[#FBF9F5] border-b border-[#E8E0D0] px-4 flex items-center justify-between gap-3 z-30 shrink-0 shadow-xs">
        
        {/* Brand & App Link */}
        <div className="flex items-center gap-3">
          <Link 
            href="/" 
            className="flex items-center gap-2 hover:opacity-85 transition-opacity group"
            title="Back to Landing Page"
          >
            <div className="w-7 h-7 rounded-md bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center shadow-xs">
              <Compass className="w-4 h-4 text-[#FBF9F5]" />
            </div>
            <span className="font-display font-bold text-base text-[#2D5016] tracking-tight">
              DrishtiGIS
            </span>
          </Link>

          <span className="text-[#8A8A8A] text-xs font-light">/</span>

          {/* Mode Tag */}
          <div className="hidden sm:flex items-center gap-1.5 bg-[#EDE8DE] text-[#2C2C2C] px-2.5 py-0.5 rounded text-[11px] font-medium border border-[#E8E0D0]">
            <Compass className="w-3 h-3 text-[#2D5016]" />
            <span>WebGIS Workspace</span>
          </div>
        </div>

        {/* Center: City Search & Property ID Quick Search */}
        <div className="flex items-center gap-2 flex-1 max-w-xl justify-center">
          
          <LocationSearch onSelect={handleCitySelect} />

          <form onSubmit={handlePropertySearchSubmit} className="hidden md:flex items-center relative">
            <input
              type="text"
              value={propertySearchInput}
              onChange={(e) => setPropertySearchInput(e.target.value)}
              placeholder="Search Property ID..."
              className="w-48 bg-[#F7F3EC] border border-[#E8E0D0] rounded-md px-2.5 py-1 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
            />
            <button
              type="submit"
              className="absolute right-1 px-1.5 py-0.5 text-[10px] font-semibold bg-[#2D5016] text-white rounded hover:bg-[#3A6B1E]"
            >
              Go
            </button>
          </form>

        </div>

        {/* Right Section: GPS Action, Layer Toggle & Account */}
        <div className="flex items-center gap-2 text-xs">
          
          {/* Explicit GPS Consent Action */}
          <button
            onClick={() => setIsConsentModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#7C3AED]/10 text-[#7C3AED] hover:bg-[#7C3AED]/20 border border-[#7C3AED]/30 font-semibold transition-all"
            title="Request device location consent to position map"
          >
            <Crosshair className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Use My Location</span>
          </button>

          {/* Toggle Layer Panel Button */}
          <button
            onClick={() => setShowLayerControl((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md border text-xs font-medium transition-all ${
              showLayerControl
                ? "bg-[#2D5016] text-white border-[#2D5016]"
                : "bg-[#FBF9F5] text-[#2C2C2C] border-[#E8E0D0] hover:bg-[#EDE8DE]"
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Layers</span>
          </button>

          {/* Toggle AI Assistant Chat Button */}
          <button
            onClick={() => setShowAssistantChat((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md border text-xs font-semibold transition-all cursor-pointer ${
              showAssistantChat
                ? "bg-[#2D5016] text-white border-[#2D5016] shadow-xs"
                : "bg-[#FBF9F5] text-[#2D5016] border-[#2D5016]/40 hover:bg-[#2D5016]/10"
            }`}
            title="Open DrishtiGIS Grounded AI Assistant (SIH26012)"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#C4922A]" />
            <span>AI Assistant</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
          </button>

          {/* Account Profile Dropdown */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen((prev) => !prev)}
              className="flex items-center gap-1.5 bg-[#EDE8DE] text-[#2C2C2C] px-2.5 py-1 rounded-md border border-[#E8E0D0] font-medium hover:bg-[#E8E0D0] transition-colors"
            >
              <UserCheck className="w-3.5 h-3.5 text-[#2D5016]" />
              <span className="max-w-[100px] truncate">{user?.name || "Account"}</span>
              <span className="text-[10px] bg-[#2D5016] text-white px-1 rounded font-mono font-bold">
                {user?.role || "USER"}
              </span>
              <ChevronDown className="w-3 h-3 text-[#8A8A8A]" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-1 w-60 bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl shadow-2xl py-1.5 z-50 text-xs font-sans space-y-1">
                <div className="px-3 py-1.5 border-b border-[#E8E0D0]">
                  <p className="font-bold text-[#2C2C2C] truncate">{user?.name}</p>
                  <p className="text-[11px] text-[#8A8A8A] truncate">{user?.email}</p>
                  <p className="text-[10px] text-[#7C3AED] font-semibold mt-0.5">Role: {user?.role}</p>
                </div>

                <Link
                  href="/app/profile"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-[#2C2C2C] hover:bg-[#EDE8DE] transition-colors font-semibold"
                >
                  <User className="w-3.5 h-3.5 text-[#2D5016]" />
                  <span>My Profile & Properties</span>
                </Link>

                {user?.role === "ADMIN" && (
                  <Link
                    href="/admin"
                    onClick={() => setUserMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-1.5 text-[#2C2C2C] hover:bg-[#EDE8DE] transition-colors font-semibold"
                  >
                    <ShieldCheck className="w-3.5 h-3.5 text-[#2D5016]" />
                    <span>Admin Console</span>
                  </Link>
                )}

                {userHome ? (
                  <>
                    <button
                      onClick={() => {
                        handleCenterOnHome();
                        setUserMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-[#7C3AED] hover:bg-[#7C3AED]/10 transition-colors font-semibold"
                    >
                      <Home className="w-3.5 h-3.5" />
                      <span>Center on My HOME</span>
                    </button>

                    <button
                      onClick={() => {
                        handleStartMoveHome();
                        setUserMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-[#10B981] hover:bg-[#10B981]/10 transition-colors font-semibold"
                    >
                      <Move className="w-3.5 h-3.5" />
                      <span>Move HOME Location</span>
                    </button>

                    <button
                      onClick={() => {
                        handleDeleteHome();
                        setUserMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete My HOME Marker</span>
                    </button>
                  </>
                ) : null}

                <div className="border-t border-[#E8E0D0] pt-1">
                  <button
                    onClick={async () => {
                      setUserMenuOpen(false);
                      await logout();
                      setUserHome(null);
                      setCurrentLocation(null);
                      setTempGpsCoords(null);
                      setDraggablePin(null);
                    }}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-red-600 hover:bg-red-50 transition-colors font-semibold"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>

      </header>

      {/* ── Main GIS Map Area ───────────────────────────────────────────── */}
      <main className="flex-1 relative overflow-hidden">
        
        {/* Temp GPS Position Banner (Save as HOME Action) */}
        {tempGpsCoords && !draggablePin && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-[#FBF9F5] border border-[#7C3AED] rounded-xl p-2.5 px-4 shadow-2xl flex items-center gap-3 font-sans text-xs">
            <div className="w-7 h-7 rounded-lg bg-[#7C3AED]/10 text-[#7C3AED] flex items-center justify-center font-bold">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <p className="font-bold text-[#2C2C2C]">Device Location Obtained</p>
              <p className="text-[11px] text-[#8A8A8A]">
                Accuracy: ~{Math.round(tempGpsCoords.accuracy)}m. Save as private HOME or adjust position on map?
              </p>
            </div>
            <div className="flex items-center gap-1.5 ml-2">
              <button
                onClick={() => handleSaveHome()}
                className="bg-[#7C3AED] text-white px-3 py-1 rounded-lg text-xs font-semibold hover:bg-[#6D28D9] transition-colors shadow-xs"
              >
                Save as HOME
              </button>
              <button
                onClick={() => {
                  setDraggablePin({
                    latitude: tempGpsCoords.latitude,
                    longitude: tempGpsCoords.longitude,
                    label: "DRAG PIN TO EXACT HOME",
                    mode: "home",
                  });
                  setTempGpsCoords(null);
                }}
                className="bg-[#10B981] text-white px-3 py-1 rounded-lg text-xs font-semibold hover:bg-[#059669] transition-colors flex items-center gap-1"
              >
                <Move className="w-3.5 h-3.5" />
                <span>Adjust Pin</span>
              </button>
              <button
                onClick={() => setTempGpsCoords(null)}
                className="bg-[#EDE8DE] text-[#2C2C2C] px-2.5 py-1 rounded-lg text-xs hover:bg-[#E8E0D0] transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Draggable Pin Banner */}
        {draggablePin && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-[#FBF9F5] border border-[#10B981] rounded-xl p-2.5 px-4 shadow-2xl flex items-center gap-3 font-sans text-xs animate-bounce">
            <div className="w-7 h-7 rounded-lg bg-[#10B981]/10 text-[#10B981] flex items-center justify-center font-bold">
              <Move className="w-4 h-4" />
            </div>
            <div>
              <p className="font-bold text-[#2C2C2C]">Drag Pin Mode Active</p>
              <p className="text-[11px] text-[#8A8A8A]">
                Lat: {draggablePin.latitude.toFixed(6)}, Lon: {draggablePin.longitude.toFixed(6)}
              </p>
            </div>
            <div className="flex items-center gap-1.5 ml-2">
              <button
                onClick={() => handleSaveHome(draggablePin.latitude, draggablePin.longitude)}
                className="bg-[#10B981] text-white px-3 py-1 rounded-lg text-xs font-semibold hover:bg-[#059669] transition-colors flex items-center gap-1 shadow-xs"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Confirm Position</span>
              </button>
              <button
                onClick={() => setDraggablePin(null)}
                className="bg-[#EDE8DE] text-[#2C2C2C] px-2.5 py-1 rounded-lg text-xs hover:bg-[#E8E0D0] transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* MapLibre GL Canvas */}
        <MapLibreMapDynamic
          center={flyTo?.center ?? [INDIA_CENTER.lon, INDIA_CENTER.lat] as [number, number]}
          zoom={flyTo?.zoom ?? INDIA_CENTER.zoom}
          height="100%"
          onLoad={() => setIsMapLoaded(true)}
          onSelectContext={setMapContext}
          onNearBhopalChange={setNearBhopal}
          initialLayers={layers}
          flyToLocation={flyTo}
          selectedContext={mapContext}
          userHomeLocation={userHome}
          currentLocation={currentLocation}
          userProperties={userProperties}
          draggableMarkerLocation={draggablePin}
          onDraggableMarkerMove={(coords) => {
            setDraggablePin((prev) => (prev ? { ...prev, ...coords } : null));
          }}
          publishedDatasets={publishedDatasets}
          activePublishedDatasetIds={activePublishedDatasetIds}
          onRegisteredLayersChange={handleRegisteredLayersChange}
        />

        {/* Floating Layer Control Overlay */}
        {showLayerControl && (
          <LayerControl
            visibility={layers}
            onChange={handleLayerChange}
            onBasemapChange={(basemap) => setLayers((prev) => ({ ...prev, basemap }))}
            hasSidebar={Boolean(mapContext)}
            publishedDatasets={publishedDatasets}
            activeDatasetIds={activePublishedDatasetIds}
            onToggleDataset={(id, visible) => {
              setSelectedDatasetId(id);
              setActivePublishedDatasetIds((prev) =>
                visible ? [...new Set([...prev, id])] : prev.filter((x) => x !== id)
              );
            }}
            onZoomToDataset={(bounds) => {
              setFlyTo({
                center: [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
                zoom: 17,
                bounds: [
                  [bounds[0], bounds[1]],
                  [bounds[2], bounds[3]],
                ],
              });
            }}
          />
        )}

        {/* Raster Visibility Debug Panel (Developer/Admin Diagnostic Section) */}
        <RasterDebugPanel
          publishedDatasets={publishedDatasets}
          selectedDatasetId={selectedDatasetId}
          onSelectDataset={setSelectedDatasetId}
          registeredSources={registeredSources}
          registeredLayers={registeredLayers}
          isMapLoaded={isMapLoaded}
          onZoomToDataset={(bounds) => {
            setFlyTo({
              center: [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
              zoom: 17,
              bounds: [
                [bounds[0], bounds[1]],
                [bounds[2], bounds[3]],
              ],
            });
          }}
        />

        {/* Unified Right Context Sidebar */}
        <ContextSidebar
          context={mapContext}
          onClose={() => setMapContext(null)}
          onSelectContext={setMapContext}
          onFlyTo={handleCitySelect}
        />

        {/* Floating AI Assistant Chat Launcher Button (FAB) */}
        {!showAssistantChat && (
          <button
            onClick={() => setShowAssistantChat(true)}
            className={`absolute bottom-6 z-40 bg-[#2D5016] hover:bg-[#3A6B1E] text-[#FBF9F5] px-4 py-2.5 rounded-2xl shadow-xl hover:shadow-2xl border border-[#3A6B1E] flex items-center gap-2.5 text-xs font-semibold transition-all duration-300 hover:scale-105 active:scale-95 group select-none cursor-pointer ${
              Boolean(mapContext) ? "right-6 sm:right-[435px]" : "right-6"
            }`}
            title="Open DrishtiGIS Grounded AI Assistant (SIH26012)"
          >
            <div className="relative">
              <Bot className="w-4 h-4 text-[#F7F3EC]" />
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#10B981] ring-2 ring-[#2D5016] animate-pulse" />
            </div>
            <span>Ask DrishtiGIS AI</span>
            <span className="text-[10px] bg-[#3A6B1E] px-1.5 py-0.5 rounded font-mono font-bold text-[#F7F3EC]">
              SIH26012
            </span>
          </button>
        )}

        {/* Grounded AI Assistant Chat Widget */}
        <AssistantChatWidget
          isOpen={showAssistantChat}
          onClose={() => setShowAssistantChat(false)}
          hasSidebar={Boolean(mapContext)}
          selectedContext={
            mapContext?.type === "parcel"
              ? {
                  entity_type: "parcel",
                  entity_id: mapContext.id || mapContext.data?.property_id,
                  region_id: "bhopal_mp",
                }
              : mapContext?.type === "ai-feature"
              ? {
                  entity_type: "building",
                  entity_id: String(mapContext.id || ""),
                  region_id: "bhopal_mp",
                }
              : { entity_type: "region", region_id: "bhopal_mp" }
          }
          onExecuteMapAction={handleExecuteAssistantAction}
        />

      </main>

      {/* Explicit Geolocation Consent Modal */}
      <LocationConsentModal
        isOpen={isConsentModalOpen}
        onClose={() => setIsConsentModalOpen(false)}
        onConsentGranted={handleConsentGranted}
        onManualSelect={() => {
          const el = document.querySelector<HTMLInputElement>("input[placeholder*='Search Property']");
          if (el) el.focus();
        }}
      />
    </div>
  );
}
