"use client";

/**
 * DrishtiGIS — Contextual Right Sidebar
 * =======================================
 * Primary contextual selection surface for WebGIS.
 * Displays:
 *   1. Property Details (for selected parcels)
 *   2. AI Building Feature Details (for selected AI building extractions)
 *   3. Data Coverage & Prototype Information (for selected coverage points)
 *
 * Replaces large floating MapLibre map popups with a clean, unified,
 * accessible DrishtiGIS sidebar interface.
 */

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { 
  X, 
  Building, 
  MapPin, 
  Sparkles, 
  AlertTriangle, 
  FileText, 
  Info,
  CheckCircle,
  ArrowRight,
  Compass,
  History,
  Route,
  Layers,
  Bot,
  Lock,
  AlertCircle,
  ShieldAlert,
  KeyRound,
  ClipboardCheck
} from "lucide-react";
import { fetchParcel, type ParcelDetailResponse } from "@/lib/api/parcels";
import type { RealAIBuildingProperties } from "@/lib/demo-data/types";
import { BHOPAL_MAP_CONFIG } from "@/lib/gis/bounds";
import { useAuth } from "@/lib/auth/Context";
import { ApiError } from "@/lib/api/client";

import { ReviewModePanel } from "./ReviewModePanel";

export type ContextType = "parcel" | "ai-feature" | "coverage" | "road" | "landuse" | "user-property" | "osm-feature";

export interface MapContextState {
  type: ContextType;
  id: string;
  data?: any;
}

interface ContextSidebarProps {
  context: MapContextState | null;
  onClose: () => void;
  onSelectContext: (ctx: MapContextState) => void;
  onFlyTo?: (lat: number, lon: number, zoom: number, bounds?: [[number, number], [number, number]]) => void;
}

export type ParcelDataState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ParcelDetailResponse }
  | { status: "unauthorized"; message: string }
  | { status: "forbidden"; message: string }
  | { status: "not_found"; message: string }
  | { status: "error"; message: string; statusCode?: number };

export function ContextSidebar({
  context,
  onClose,
  onSelectContext,
  onFlyTo,
}: ContextSidebarProps) {
  const { token } = useAuth();
  const [parcelState, setParcelState] = useState<ParcelDataState>({ status: "idle" });
  const [isReviewMode, setIsReviewMode] = useState<boolean>(false);
  const activePropertyIdRef = useRef<string | null>(null);

  // Reset review mode when context changes
  useEffect(() => {
    setIsReviewMode(false);
  }, [context?.id, context?.type]);


  // Fetch parcel details when context is 'parcel'
  useEffect(() => {
    if (!context || context.type !== "parcel") {
      activePropertyIdRef.current = null;
      setParcelState({ status: "idle" });
      return;
    }

    const propertyId = context.id;
    // Prevent duplicate simultaneous or repeated requests for the same parcel ID
    if (propertyId === activePropertyIdRef.current) {
      return;
    }

    activePropertyIdRef.current = propertyId;
    let cancelled = false;

    setParcelState({ status: "loading" });
    fetchParcel(propertyId, token)
      .then((data) => {
        if (!cancelled) {
          setParcelState({ status: "success", data });
        }
      })
      .catch((err: any) => {
        if (cancelled) return;
        const statusCode = err?.status ?? (err instanceof ApiError ? err.status : 500);
        if (statusCode === 401) {
          setParcelState({
            status: "unauthorized",
            message: "Authentication required to view official property cadastral details.",
          });
        } else if (statusCode === 403) {
          setParcelState({
            status: "forbidden",
            message: "You do not have permission to view this cadastral property record.",
          });
        } else if (statusCode === 404) {
          setParcelState({
            status: "not_found",
            message: `Property record '${propertyId}' was not found in the cadastral database.`,
          });
        } else {
          setParcelState({
            status: "error",
            message: err?.message || `Property details for '${propertyId}' could not be loaded.`,
            statusCode,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [context?.id, context?.type, token]);

  if (!context) return null;

  return (
    <aside
      className="absolute top-0 right-0 bottom-0 z-30 w-full sm:w-[380px] lg:w-[420px] bg-[#FBF9F5] border-l border-[#E8E0D0] shadow-2xl flex flex-col font-sans select-none transition-all duration-300 transform translate-x-0"
      role="complementary"
      aria-label="Map context details sidebar"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#E8E0D0] bg-[#F7F3EC] shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center font-bold shadow-xs">
            {context.type === "parcel" && <Building className="w-4 h-4" />}
            {context.type === "ai-feature" && <Sparkles className="w-4 h-4" />}
            {context.type === "coverage" && <Compass className="w-4 h-4" />}
            {context.type === "road" && <Route className="w-4 h-4" />}
            {context.type === "landuse" && <Layers className="w-4 h-4" />}
            {context.type === "osm-feature" && <Building className="w-4 h-4" />}
          </div>
          <div>
            <span className="font-display font-bold text-sm text-[#2D5016] block leading-tight">
              {context.type === "parcel" && `Property ${context.id}`}
              {context.type === "ai-feature" && `AI Building ${context.id}`}
              {context.type === "coverage" && `${context.id} Coverage`}
              {context.type === "road" && `Road ${context.id}`}
              {context.type === "landuse" && `Land-Use Pattern ${context.id}`}
              {context.type === "osm-feature" && `OSM Feature ${context.id}`}
            </span>
            <span className="text-[10px] text-[#8A8A8A] uppercase font-mono tracking-wider">
              {context.type === "parcel" && "Urban Cadastral Intelligence"}
              {context.type === "ai-feature" && "AI Feature Extraction Output"}
              {context.type === "coverage" && "Data Onboarding & Status"}
              {context.type === "road" && "Transport & Access Network"}
              {context.type === "landuse" && "Observed Land-Use Intelligence"}
              {context.type === "osm-feature" && "OpenStreetMap Reference GIS"}
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-7 h-7 rounded-full bg-[#EDE8DE] hover:bg-[#E8E0D0] text-[#6B6B6B] flex items-center justify-center transition-colors cursor-pointer"
          aria-label="Close sidebar"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Main Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        
        {/* If Review Mode is active */}
        {isReviewMode ? (
          <ReviewModePanel
            parcelId={context.type === "parcel" ? context.id : undefined}
            onCloseReview={() => setIsReviewMode(false)}
          />
        ) : (
          <>
            {/* Prototype Disclaimer */}
            <div className="bg-[#EDE8DE] border border-[#E8E0D0] rounded-lg p-3 text-[11px] text-[#6B6B6B] leading-relaxed">
              <div className="flex items-center justify-between mb-0.5">
                <div className="flex items-center gap-1.5 font-bold text-[#2C2C2C]">
                  <Info className="w-3.5 h-3.5 text-[#C4922A]" />
                  <span>Prototype Demonstration Data</span>
                </div>
                {(context.type === "parcel" || context.type === "ai-feature") && (
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setIsReviewMode(true)}
                      className="flex items-center gap-1 px-2 py-0.5 bg-cyan-900 text-cyan-200 hover:bg-cyan-800 rounded font-semibold text-[10px] transition-colors"
                    >
                      <ClipboardCheck className="w-3 h-3 text-cyan-400" />
                      Review Issue
                    </button>
                    <a
                      href={`/app/exports?parcel=${context.id}`}
                      className="flex items-center gap-1 px-2 py-0.5 bg-slate-800 text-slate-200 hover:bg-slate-700 rounded font-semibold text-[10px] transition-colors"
                    >
                      Export GIS
                    </a>
                  </div>
                )}
              </div>
              {context.type === "coverage"
                ? "Bhopal is the first fully onboarded prototype area with high-resolution UAV imagery and derived AI features."
                : "Analytical demonstration output — not official government survey or legal land records."}
            </div>


        {/* ── MODE 1: PARCEL / PROPERTY DETAILS ─────────────────────────────── */}
        {context.type === "parcel" && (
          <>
            {/* Clicked Vector Feature Summary (from map layer) */}
            {context.data && (
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5 text-[#2D5016]" />
                    <span>CLICKED PARCEL VECTOR FEATURE</span>
                  </h3>
                  <span className="text-[9px] font-bold bg-[#EDE8DE] text-[#69635C] px-1.5 py-0.5 rounded font-mono">
                    {context.id}
                  </span>
                </div>
                <div className="space-y-1.5 text-xs">
                  {context.data.plot_number && (
                    <Row label="Plot Number" value={String(context.data.plot_number)} />
                  )}
                  {context.data.survey_number && (
                    <Row label="Survey Number" value={String(context.data.survey_number)} />
                  )}
                  {context.data.area_m2 && (
                    <Row label="Feature Area" value={`${Math.round(context.data.area_m2)} m²`} />
                  )}
                  {context.data.land_use && (
                    <Row label="Land Use" value={String(context.data.land_use)} />
                  )}
                  <Row label="Data Source" value="Vector Map Layer (SYNTHETIC_DEMO)" />
                </div>
              </section>
            )}

            {parcelState.status === "loading" && (
              <div className="p-6 text-center text-xs text-[#8A8A8A] space-y-2 bg-[#F7F3EC]/50 border border-[#E8E0D0] rounded-xl">
                <div className="w-6 h-6 rounded-full border-2 border-[#E8E0D0] border-t-[#2D5016] animate-spin mx-auto" />
                <p>Fetching authoritative parcel intelligence record…</p>
              </div>
            )}

            {parcelState.status === "unauthorized" && (
              <div className="p-4 bg-amber-50/80 border border-amber-300 rounded-xl space-y-3" role="alert">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                  <Lock className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>Authentication Required</span>
                </div>
                <p className="text-[11px] text-amber-800 leading-relaxed">
                  Cadastral property records and AI discrepancy intelligence require an active authenticated session.
                </p>
                <div className="pt-1">
                  <Link
                    href={`/login?redirect=${encodeURIComponent(typeof window !== "undefined" ? window.location.pathname : "/app/map")}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#2D5016] text-white hover:bg-[#3B661E] rounded-lg text-xs font-semibold shadow-xs transition-colors"
                  >
                    <KeyRound className="w-3.5 h-3.5" />
                    <span>Sign In to Access Authoritative Record</span>
                  </Link>
                </div>
              </div>
            )}

            {parcelState.status === "forbidden" && (
              <div className="p-4 bg-red-50/80 border border-red-300 rounded-xl space-y-2" role="alert">
                <div className="flex items-center gap-2 text-red-900 font-bold text-xs">
                  <ShieldAlert className="w-4 h-4 text-red-700 shrink-0" />
                  <span>Access Restricted</span>
                </div>
                <p className="text-[11px] text-red-800 leading-relaxed">
                  {parcelState.message}
                </p>
              </div>
            )}

            {parcelState.status === "not_found" && (
              <div className="p-4 bg-slate-50 border border-slate-300 rounded-xl space-y-2" role="alert">
                <div className="flex items-center gap-2 text-slate-800 font-bold text-xs">
                  <AlertCircle className="w-4 h-4 text-slate-600 shrink-0" />
                  <span>Record Not Found</span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {parcelState.message}
                </p>
              </div>
            )}

            {parcelState.status === "error" && (
              <div className="p-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg space-y-1" role="alert">
                <div className="font-semibold flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Unable to load property record</span>
                </div>
                <p>{parcelState.message}</p>
              </div>
            )}

            {parcelState.status === "success" && (
              <div className="space-y-4">

                {/* SYNTHETIC DEMO badge — shown whenever source is SYNTHETIC_DEMO */}
                {parcelState.data._source === "SYNTHETIC_DEMO" && (
                  <div className="flex items-start gap-2 bg-amber-50 border border-amber-300 rounded-lg px-3 py-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[11px] font-bold text-amber-900">DEMO PROPERTY — NOT OFFICIAL LAND RECORD</p>
                      <p className="text-[10px] text-amber-700 leading-snug mt-0.5">
                        ⚠ Synthetic prototype data — not an official land record.
                        Identifiers, owner names, and property data are synthetic.
                      </p>
                    </div>
                  </div>
                )}

                {/* Property Basics */}
                {(() => {
                  const props = {
                    ...(parcelState.data.parcel?.properties ?? {}),
                    ...(parcelState.data.property ?? {}),
                  } as Record<string, unknown>;
                  const isSynthetic = parcelState.data._source === "SYNTHETIC_DEMO";
                  // synthetic fields
                  const ownerName  = (props["owner_name"] ?? props["current_owner_name"]) as string | undefined;
                  const landType   = (props["land_use"] ?? props["land_type"] ?? "Residential") as string;
                  const centLon    = (props as Record<string, unknown>)["centroid_lon"] as number | undefined;
                  const centLat    = (props as Record<string, unknown>)["centroid_lat"] as number | undefined;
                  const coordLabel = centLon && centLat
                    ? `${centLat.toFixed(5)}° N, ${centLon.toFixed(5)}° E`
                    : "Bhopal, Madhya Pradesh";

                  return (
                    <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                      <h3 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-[#2D5016]" />
                        <span>PROPERTY DETAILS</span>
                        {isSynthetic && (
                          <span className="ml-auto text-[9px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded uppercase tracking-wide">
                            DEMO DATA
                          </span>
                        )}
                      </h3>
                      <div className="space-y-1.5">
                        <Row label="Property ID"    value={String(props?.property_id ?? context.id)} />
                        <Row label="Plot / Survey #" value={String(props?.plot_number ?? props?.survey_number ?? "—")} />
                        {ownerName && <Row label="Owner (Synthetic)" value={ownerName} />}
                        <Row label="Parcel Area"    value={props?.area_m2 ? `${props.area_m2} m²` : "—"} />
                        <Row label="Location"       value="Bhopal, Madhya Pradesh" />
                        <Row label="Coordinates"    value={coordLabel} />
                        <Row label="Land Use"       value={String(landType)} />
                        <Row label="Record Status"  value={isSynthetic ? "Synthetic Demo" : "Prototype Dataset"} />
                      </div>
                    </section>
                  );
                })()}

                {/* A. OWNERSHIP & RESIDENTS */}
                {(() => {
                  const props = (parcelState.data.property ?? parcelState.data.parcel?.properties ?? {}) as Record<string, any>;
                  const rawType = String(props.property_type ?? props.land_type ?? props.land_use ?? "HOUSE").toUpperCase();
                  const isVacant = rawType === "VACANT_PLOT" || rawType === "VACANT PLOT" || rawType === "VACANT";
                  let typeLabel = "House";
                  if (isVacant) typeLabel = "Vacant Plot";
                  else if (rawType.includes("BUILDING") || rawType.includes("COMMERCIAL")) typeLabel = "Building";
                  else if (rawType.includes("OTHER")) typeLabel = "Other";

                  const currOwner = props.current_owner_name ?? props.owner_name ?? "Not available";
                  const prevOwner = props.previous_owner_name ?? "Not available";
                  const residents = props.resident_count;

                  return (
                    <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                      <h3 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Building className="w-3.5 h-3.5 text-[#2D5016]" />
                        <span>OWNERSHIP &amp; RESIDENTS</span>
                      </h3>

                      <div className="space-y-1.5">
                        <Row label="Property Type" value={typeLabel} />
                        <Row label="Current Owner" value={String(currOwner)} />
                        <Row label="Previous Owner" value={String(prevOwner)} />
                        {!isVacant && (
                          <Row
                            label="Current Residents"
                            value={residents != null ? `${residents} resident${residents === 1 ? '' : 's'}` : "Not available"}
                          />
                        )}
                      </div>
                      <p className="text-[9px] text-[#8A8A8A] italic pt-1 border-t border-[#E8E0D0]">
                        Illustrative demo ownership data — not an official title deed or land record.
                      </p>
                    </section>
                  );
                })()}

                {/* B. PROPERTY VALUE */}
                {(() => {
                  const props = (parcelState.data.property ?? parcelState.data.parcel?.properties ?? {}) as Record<string, any>;
                  const currentYear = new Date().getFullYear();
                  const valYear = props.valuation_year ?? currentYear;

                  const formatINR = (val: any) => {
                    if (val == null || val === "" || isNaN(Number(val))) return "Not available";
                    return "₹" + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 0 });
                  };

                  const purchaseStr = formatINR(props.purchase_price_inr);
                  const sellingStr = formatINR(props.estimated_selling_price_inr);

                  return (
                    <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-[#C4922A]" />
                          <span>PROPERTY VALUE</span>
                        </h3>
                        <span className="text-[9px] font-mono bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-bold">
                          DEMO ESTIMATE
                        </span>
                      </div>

                      <div className="space-y-1.5">
                        <Row label="Purchase Price" value={purchaseStr} />
                        <Row label={`Estimated Selling Price — ${valYear}`} value={sellingStr} />
                        <Row label="Valuation Basis" value="Estimated market value" />
                      </div>
                      <p className="text-[9px] text-[#8A8A8A] italic pt-1 border-t border-[#E8E0D0]">
                        Illustrative demo estimate — not an official government circle rate or registered valuation.
                      </p>
                    </section>
                  );
                })()}

                {/* AI Analysis Summary — real UAVPal data */}
                {(() => {
                  const ai = parcelState.data.ai_analysis;
                  if (!ai) return null;
                  return (
                    <section className="bg-[#F0FAFA] border border-teal-200 rounded-xl p-3.5 space-y-2">
                      <h3 className="text-[10px] font-bold text-teal-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                        <span>AI BUILDING ANALYSIS</span>
                        <span className="ml-auto text-[9px] font-mono text-teal-500 normal-case tracking-normal">UAVPal U-Net</span>
                      </h3>
                      <div className="space-y-1.5">
                        <Row label="Buildings Detected" value={String(ai.building_count)} />
                        <Row label="Total Detected Area"
                          value={ai.total_detected_area_m2 > 0 ? `${ai.total_detected_area_m2.toFixed(1)} m²` : "—"} />
                        <Row label="Parcel Area"
                          value={ai.parcel_area_m2 > 0 ? `${ai.parcel_area_m2} m²` : "—"} />
                        <Row label="Coverage Ratio"
                          value={ai.coverage_ratio != null ? `${(ai.coverage_ratio * 100).toFixed(1)}%` : "—"} />
                        <Row label="Avg Confidence"
                          value={ai.average_confidence != null ? `${(ai.average_confidence * 100).toFixed(0)}%` : "—"} />
                        {ai.discrepancy_count > 0 && (
                          <Row label="Discrepancies" value={String(ai.discrepancy_count)} highlight />
                        )}
                      </div>
                      <p className="text-[10px] text-teal-700 leading-snug mt-1 border-t border-teal-100 pt-1.5">
                        AI-derived geometric analysis — not a legal determination.
                      </p>
                    </section>
                  );
                })()}

                {/* Discrepancies from real AI analysis */}
                {(() => {
                  const ai = parcelState.data.ai_analysis;
                  const discs = ai?.discrepancies ?? parcelState.data.discrepancies;
                  if (!discs || discs.length === 0) return null;
                  const first = discs[0] as Record<string, unknown>;
                  return (
                    <section className="bg-amber-50/70 border border-amber-200 rounded-xl p-3.5 space-y-2">
                      <div className="font-semibold text-amber-900 text-xs flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                        <span>Spatial Discrepancy Observation</span>
                      </div>
                      <p className="text-[11px] text-amber-800 leading-relaxed">
                        {(first?.["description"] as string | undefined)
                          ?? (first?.["ui_label"] as string | undefined)
                          ?? "AI-detected geometry differs from available parcel geometry."}
                      </p>
                      {discs.length > 1 && (
                        <p className="text-[10px] text-amber-600">
                          +{discs.length - 1} additional observation{discs.length > 2 ? "s" : ""}
                        </p>
                      )}
                    </section>
                  );
                })()}

                {/* History & Multi-Epoch Change Detection */}
                <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 text-[11px] text-[#6B6B6B] space-y-2">
                  <div className="flex items-center justify-between font-bold text-[#2C2C2C]">
                    <div className="flex items-center gap-1.5">
                      <History className="w-3.5 h-3.5 text-[#2D5016]" />
                      <span className="uppercase text-[10px] tracking-wider text-[#2D5016]">MULTI-EPOCH TEMPORAL ANALYSIS</span>
                    </div>
                    <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1.5 py-0.5 rounded">
                      EPOCH A vs B
                    </span>
                  </div>

                  <div className="space-y-1.5 pt-1">
                    <Row label="Baseline Epoch" value="EPOCH-BPL-2024-01 (UAV 0.02m)" />
                    <Row label="Target Epoch" value="EPOCH-BPL-2025-06 (Software Fixture)" />
                    <Row label="Building Footprint Delta" value="1 Added, 1 Modified (Fixture)" highlight />
                  </div>

                  <div className="bg-[#EDE8DE]/60 p-2 rounded-lg text-[10px] text-[#69635C] leading-relaxed mt-2 border border-[#E8E0D0]">
                    <div className="font-semibold text-[#2C2C2C] mb-0.5">Analytical Observation Disclaimer</div>
                    Observed AI building footprint differences represent spatial processing metrics. They do not constitute official land record changes or legal property violations.
                  </div>
                </section>

                <Link
                  href={`/app/assistant?entity_type=parcel&entity_id=${context.id}`}
                  className="w-full inline-flex items-center justify-center gap-2 bg-[#2D5016] text-[#FBF9F5] hover:bg-[#3A6B1E] px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-colors mt-3 shadow-xs"
                >
                  <Bot className="w-4 h-4" />
                  <span>Ask AI Assistant About This Parcel</span>
                </Link>
              </div>
            )}
          </>
        )}

        {/* ── MODE 2: AI BUILDING FEATURE DETAILS ────────────────────────────── */}
        {context.type === "ai-feature" && (() => {
          // context.data contains RealAIBuildingProperties from the map click
          const d = context.data as any;
          const bldgId          = d?.building_id ?? d?.id ?? context.id;
          const primaryPropertyId = d?.primary_property_id ?? null;
          const primaryParcelId   = d?.primary_parcel_id ?? null;
          const parentParcel    = d?.parent_parcel_id ?? primaryPropertyId ?? primaryParcelId ?? "No parcel match";
          const relationship    = d?.boundary_status ?? d?.parcel_relationship ?? "NO_PARCEL_MATCH";
          const reviewStatus    = d?.review_status ?? (relationship === "CROSSES_BOUNDARY" ? "FLAGGED_OVERHANG" : (relationship === "FULLY_WITHIN" ? "VERIFIED" : "UNASSOCIATED"));
          const landUse         = d?.land_use ?? "Residential / Built-up";
          const source          = d?.source ?? "AI_DERIVED_UAVPAL";
          const sourceTile      = d?.source_tile ?? "—";
          const model           = d?.model ?? "UNet-ResNet18-UAVPal";
          const confidence      = d?.confidence != null ? d.confidence : null;
          const areaM2          = d?.building_area_m2 ?? d?.area_m2 ?? null;
          const overlapRatio    = d?.overlap_ratio ?? null;

          const relationshipLabel: Record<string, string> = {
            FULLY_WITHIN:       "Fully Within Parcel",
            CROSSES_BOUNDARY:   "Crosses Parcel Boundary",
            PARTIALLY_OVERLAPS: "Partially Overlaps Parcel",
            TOUCHES_BOUNDARY:   "Touches Parcel Boundary",
            NO_PARCEL_MATCH:    "No Parcel Match",
          };
          const relationshipColour: Record<string, string> = {
            FULLY_WITHIN:       "text-teal-700 bg-teal-50 border-teal-200",
            CROSSES_BOUNDARY:   "text-amber-700 bg-amber-50 border-amber-200",
            PARTIALLY_OVERLAPS: "text-amber-600 bg-amber-50 border-amber-200",
            NO_PARCEL_MATCH:    "text-stone-600 bg-stone-50 border-stone-200",
            TOUCHES_BOUNDARY:   "text-stone-600 bg-stone-50 border-stone-200",
          };

          return (
            <div className="space-y-4">
              {/* AI DETECTED BUILDING card */}
              <section className="bg-[#F0FAFA] border border-teal-200 rounded-xl p-3.5 space-y-2.5">
                <div className="flex items-center justify-between pb-1.5 border-b border-teal-100">
                  <h3 className="text-[10px] font-bold text-teal-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                    <span>AI DETECTED BUILDING</span>
                  </h3>
                  <span className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-teal-100/70 text-teal-700">
                    {source}
                  </span>
                </div>
                <div className="space-y-1.5">
                  <Row label="Building ID" value={bldgId} />
                  <Row label="Detected Area"
                    value={areaM2 != null ? `${Number(areaM2).toFixed(1)} m²` : "—"} />
                  <Row label="AI Confidence"
                    value={confidence != null ? `${(Number(confidence) * 100).toFixed(0)}%` : "—"} />
                  <Row label="Detection Source" value="UAV Imagery (U-Net ResNet18)" />
                  <Row label="Land Use" value={landUse} />
                  <Row label="Source Tile" value={sourceTile} />
                  <Row label="Model Architecture" value={model} />
                </div>
              </section>

              {/* Spatial Association & Boundary Relationship */}
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2.5">
                <h3 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-[#2D5016]" />
                  <span>PARCEL RELATIONSHIP & REVIEW</span>
                </h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs py-1 border-b border-[#EDE8DE]">
                    <span className="text-[#6B6B6B]">Parent Parcel</span>
                    <span className="font-mono font-semibold text-[#2C2C2C]">
                      {parentParcel}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1 border-b border-[#EDE8DE]">
                    <span className="text-[#6B6B6B]">Boundary Relationship</span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${relationshipColour[relationship] ?? "text-stone-700"}`}>
                      {relationshipLabel[relationship] ?? relationship}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1 border-b border-[#EDE8DE]">
                    <span className="text-[#6B6B6B]">Review Status</span>
                    <span className={`text-[11px] font-bold uppercase tracking-wider ${
                      reviewStatus === "FLAGGED_OVERHANG" ? "text-amber-700" :
                      reviewStatus === "VERIFIED" ? "text-teal-700" : "text-stone-600"
                    }`}>
                      {reviewStatus}
                    </span>
                  </div>

                  {overlapRatio != null && overlapRatio > 0 && (
                    <Row label="Parcel Overlap"
                      value={`${(Number(overlapRatio) * 100).toFixed(1)}%`} />
                  )}

                  {parentParcel === "No parcel match" && (
                    <p className="text-[10px] text-[#8A8A8A] leading-snug pt-0.5">
                      This building footprint does not geometrically intersect any prototype cadastral parcel polygon.
                    </p>
                  )}
                </div>
              </section>

              {/* Legal & Cadastral Disclaimer */}
              <section className="bg-amber-50/70 border border-amber-200/80 rounded-lg p-3 text-[10px] text-amber-900 leading-snug space-y-1">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>AI Detection ≠ Cadastral Ownership</span>
                </div>
                <p>
                  <strong>AI Detected Building</strong> represents a physical feature extracted from UAV imagery.
                  <strong> Parent Parcel</strong> is a spatial geometric association only.
                  This AI footprint does <em>not</em> constitute a legal cadastral boundary and does not prove ownership.
                </p>
              </section>

              {/* Action — View Associated Parcel */}
              {primaryPropertyId && (
                <div className="pt-1">
                  <button
                    type="button"
                    onClick={() => onSelectContext({ type: "parcel", id: primaryPropertyId })}
                    className="w-full bg-[#2D5016] text-[#FBF9F5] hover:bg-[#3A6B1E] border border-transparent font-semibold py-2 px-3 rounded-lg text-xs flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer"
                  >
                    <ArrowRight className="w-3.5 h-3.5" />
                    <span>{primaryPropertyId?.includes("DEMO") ? "View Demo Property Record" : "View Property Record"}</span>
                  </button>
                </div>
              )}
            </div>
          );
        })()}

        {/* ── MODE 3: COVERAGE / PROTOTYPE DATA ──────────────────────────────── */}
        {context.type === "coverage" && (
          <div className="space-y-4">
            <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#E8E0D0] pb-2">
                <div>
                  <strong className="font-display text-sm text-[#0E5A3A] block">{context.id}</strong>
                  <span className="text-[11px] text-[#69635C]">Madhya Pradesh, India</span>
                </div>
                <span className="text-[10px] font-bold bg-[#0E5A3A] text-[#F6F2EA] px-2 py-0.5 rounded">
                  Prototype Area
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="font-semibold text-[#69635C]">Data available:</div>
                <div className="space-y-1 text-[#0E5A3A] font-medium">
                  <div className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-[#0E5A3A]" /> High-Res UAV Imagery (0.02m)</div>
                  <div className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-[#0E5A3A]" /> Prototype Cadastral Parcels</div>
                  <div className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-[#0E5A3A]" /> AI Building Extractions</div>
                  <div className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-[#0E5A3A]" /> OSM Reference Data</div>
                </div>
              </div>
            </section>

            <div className="pt-2">
              <button
                type="button"
                onClick={() => {
                  onFlyTo?.(
                    BHOPAL_MAP_CONFIG.center[1],
                    BHOPAL_MAP_CONFIG.center[0],
                    BHOPAL_MAP_CONFIG.zoom,
                    BHOPAL_MAP_CONFIG.bounds as any
                  );
                }}
                className="w-full bg-[#0E5A3A] text-[#F6F2EA] hover:bg-[#126B46] font-semibold py-2.5 px-3 rounded-lg text-xs flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer"
              >
                <span>Explore Area →</span>
              </button>
            </div>
          </div>
        )}

        {/* ── MODE 4: ROAD / ACCESS CORRIDOR DETAILS ───────────────────────── */}
        {context.type === "road" && (() => {
          const d = context.data || {};
          const roadClass = String(d.road_class || d.highway || "LOCAL").toUpperCase();
          const roadName = d.name || "Unnamed Access Segment";
          const width = d.estimated_width_m ? `${d.estimated_width_m} m` : "5.5 m (estimated)";
          const surface = String(d.surface_type || d.surface || "PAVED").toUpperCase();
          const sourceType = String(d.source_type || "REFERENCE_GIS");
          const length = d.length_m ? `${Math.round(d.length_m)} m` : "—";

          return (
            <div className="space-y-4">
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                <h3 className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Route className="w-3.5 h-3.5 text-[#2D5016]" />
                  <span>ROAD FEATURE DETAILS</span>
                </h3>
                <div className="space-y-1.5">
                  <Row label="Road ID" value={context.id} />
                  <Row label="Street Name" value={roadName} />
                  <Row label="Road Class" value={roadClass} highlight />
                  <Row label="Est. Width" value={width} />
                  <Row label="Segment Length" value={length} />
                  <Row label="Surface Type" value={surface} />
                  <Row label="Data Source" value="OpenStreetMap" />
                  <Row label="Source Classification" value={sourceType} />
                </div>
              </section>

              <div className="bg-[#EDE8DE]/60 p-2.5 rounded-lg text-[10px] text-[#69635C] leading-relaxed border border-[#E8E0D0]">
                <div className="font-semibold text-[#2C2C2C] mb-0.5">Reference Data Attribution</div>
                Road network geometry provided by OpenStreetMap supplementary GIS reference data. Classified under REFERENCE_GIS.
              </div>
            </div>
          );
        })()}

        {/* ── MODE 5: LAND-USE FEATURE DETAILS ─────────────────────────────── */}
        {context.type === "landuse" && (() => {
          const d = context.data || {};
          const classification = String(d.classification || d.landuse || "RESIDENTIAL").toUpperCase();
          const area = d.area_m2 ? `${Math.round(d.area_m2)} m²` : "—";
          const sourceType = String(d.source_type || "REFERENCE_GIS");
          const evidence = d.evidence || "Observed polygon pattern from reference GIS.";

          return (
            <div className="space-y-4">
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                <h3 className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-[#2D5016]" />
                  <span>OBSERVED LAND-USE PATTERN</span>
                </h3>
                <div className="space-y-1.5">
                  <Row label="Feature ID" value={context.id} />
                  <Row label="Observed Pattern" value={classification} highlight />
                  <Row label="Polygon Area" value={area} />
                  <Row label="Data Source" value="OpenStreetMap" />
                  <Row label="Source Classification" value={sourceType} />
                  <Row label="Evidence" value={evidence} />
                </div>
              </section>

              <div className="bg-amber-50/70 border border-amber-200 p-2.5 rounded-lg text-[10px] text-amber-900 leading-relaxed">
                <div className="font-semibold text-amber-950 mb-0.5">Non-Legal Classification Disclaimer</div>
                Observed physical land-use pattern derived from spatial features. Does not constitute official legal land-use zoning or permitted property rights.
              </div>
            </div>
          );
        })()}

        {/* ── MODE 6: OSM REFERENCE GIS FEATURE DETAILS ─────────────────────── */}
        {context.type === "osm-feature" && (() => {
          const d = context.data || {};
          const featureName = d.name || d.address_label || "Unnamed Feature";
          const featureType = d.featureType || (d.building ? "Building" : "Reference GIS Feature");
          const osmId = d.osm_id || context.id;
          const buildingType = d.building ? String(d.building).toUpperCase() : "YES";
          const geometryType = d.geometryType || "Polygon";

          return (
            <div className="space-y-4">
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
                <h3 className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Building className="w-3.5 h-3.5 text-[#2D5016]" />
                  <span>REFERENCE GIS FEATURE</span>
                </h3>
                <div className="space-y-1.5">
                  <Row label="OSM ID" value={String(osmId)} />
                  <Row label="Feature Type" value={featureType} highlight />
                  <Row label="Feature Name" value={featureName} />
                  {d.building && <Row label="Building Classification" value={buildingType} />}
                  <Row label="Geometry" value={geometryType} />
                  <Row label="Data Source" value="OpenStreetMap" />
                  <Row label="Classification" value="REFERENCE_GIS" />
                </div>
              </section>

              <div className="bg-[#EDE8DE]/70 border border-[#E8E0D0] p-3 rounded-lg text-[11px] text-[#555] leading-relaxed">
                <div className="font-semibold text-[#2C2C2C] mb-1">Reference GIS Feature — Not Official Land Record</div>
                This boundary is provided from open reference spatial data (OpenStreetMap) to assist spatial navigation. It does not represent an official legal land record or cadastral ownership boundary.
              </div>
            </div>
          );
        })()}

          </>
        )}
      </div>
    </aside>
  );
}

function Row({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between text-xs py-1 border-b border-[#EDE8DE] last:border-0">
      <span className="text-[#6B6B6B]">{label}</span>
      <span className={`font-medium ${highlight ? "text-amber-800 font-bold" : "text-[#2C2C2C]"}`}>
        {value}
      </span>
    </div>
  );
}
