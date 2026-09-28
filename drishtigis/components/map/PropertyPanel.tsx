"use client";

/**
 * DrishtiGIS — Property Detail Panel
 * =====================================
 * Displays property intelligence data when a parcel is selected on the map.
 *
 * Data integrity rules:
 *   - Prototype disclaimer is always visible and not collapsible
 *   - legal_status null means never showing legal language
 *   - AI features labeled as AI_DERIVED_DEMO — not official survey data
 *   - Discrepancies use only safe language (no "illegal", "fraud", etc.)
 */

import { useEffect, useRef, useState } from "react";
import { 
  X, 
  Building, 
  MapPin, 
  Ruler, 
  Sparkles, 
  AlertTriangle, 
  ShieldAlert, 
  FileText, 
  Info,
  CheckCircle,
  ExternalLink
} from "lucide-react";
import { fetchParcel, type ParcelDetailResponse } from "@/lib/api/parcels";

interface PropertyPanelProps {
  propertyId: string | null;
  onClose: () => void;
}

type PanelState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ParcelDetailResponse }
  | { status: "error"; message: string };

export function PropertyPanel({ propertyId, onClose }: PropertyPanelProps) {
  const [state, setState] = useState<PanelState>({ status: "idle" });
  const abortRef = useRef<AbortController | null>(null);
  const lastIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!propertyId) return;
    if (propertyId === lastIdRef.current && state.status === "success") return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    lastIdRef.current = propertyId;

    const load = async () => {
      setState({ status: "loading" });
      try {
        const data = await fetchParcel(propertyId);
        if (!controller.signal.aborted) {
          setState({ status: "success", data });
        }
      } catch {
        if (!controller.signal.aborted) {
          setState({ status: "error", message: "Property data could not be loaded." });
        }
      }
    };

    load();

    return () => { controller.abort(); };
  }, [propertyId]);

  if (!propertyId) return null;

  // PROTOTYPE DISCLAIMER — always rendered first, never hidden
  const disclaimer = (
    <div
      className="bg-[#EDE8DE] border border-[#E8E0D0] rounded-lg p-3 text-[11px] text-[#6B6B6B] m-3 leading-relaxed"
      role="note"
      aria-label="Data disclaimer"
    >
      <div className="flex items-center gap-1.5 font-bold text-[#2C2C2C] mb-0.5">
        <Info className="w-3.5 h-3.5 text-[#C4922A]" />
        <span>Prototype Demonstration Data</span>
      </div>
      {state.status === "success"
        ? state.data._disclaimer
        : "This is prototype demonstration data for Bhopal, MP. Not official government cadastral records."}
    </div>
  );

  return (
    <aside
      className="fixed inset-y-0 right-0 z-30 w-full sm:w-[380px] lg:w-[420px] bg-[#FBF9F5] border-l border-[#E8E0D0] shadow-2xl flex flex-col font-sans transition-all duration-300 transform translate-x-0"
      role="complementary"
      aria-label="Property detail panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#E8E0D0] bg-[#F7F3EC] shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#2D5016]/10 text-[#2D5016] flex items-center justify-center font-bold">
            <Building className="w-4 h-4" />
          </div>
          <div>
            <span className="font-display font-bold text-sm text-[#2D5016] block leading-tight">
              {propertyId}
            </span>
            <span className="text-[10px] text-[#8A8A8A] uppercase font-mono tracking-wider">
              Demonstration Cadastral Record
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-7 h-7 rounded-full bg-[#EDE8DE] hover:bg-[#E8E0D0] text-[#6B6B6B] flex items-center justify-center transition-colors"
          aria-label="Close property panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Main Body Content */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {disclaimer}

        {state.status === "loading" && (
          <div className="p-6 text-center text-xs text-[#8A8A8A] space-y-2">
            <div className="w-6 h-6 rounded-full border-2 border-[#E8E0D0] border-t-[#2D5016] animate-spin mx-auto" />
            <p>Fetching parcel intelligence record…</p>
          </div>
        )}

        {state.status === "error" && (
          <div className="p-4 text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg mx-3" role="alert">
            {state.message}
          </div>
        )}

        {state.status === "success" && (
          <div className="px-3 pb-6 space-y-5 text-xs">
            
            {/* Property Identity Card */}
            <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 space-y-2">
              <h3 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[#2D5016]" />
                <span>Property Basics</span>
              </h3>

              <div className="space-y-1.5">
                <Row label="Property ID" value={String(state.data.parcel?.properties?.property_id ?? propertyId)} />
                <Row label="Plot Number" value={String(state.data.parcel?.properties?.plot_number ?? "—")} />
                <Row label="Survey Number" value={String(state.data.parcel?.properties?.survey_number ?? "—")} />
                <Row label="Parcel Area" value={state.data.parcel?.properties?.area_m2 ? `${state.data.parcel.properties.area_m2} m²` : "—"} />
                <Row label="Land Type" value={String(state.data.parcel?.properties?.land_type ?? "—")} />
                <Row label="Region" value="Bhopal, Madhya Pradesh" />
                <Row label="Source Dataset" value="UAVPal Demonstration Dataset" />
                <Row label="Data Status" value="DEMO — NOT AN OFFICIAL LAND RECORD" />
              </div>
            </section>

            {/* A. OWNERSHIP & RESIDENTS */}
            {(() => {
              const prop = (state.data.property ?? state.data.parcel?.properties ?? {}) as Record<string, any>;
              const rawType = String(prop.property_type ?? prop.land_type ?? "HOUSE").toUpperCase();
              const isVacant = rawType === "VACANT_PLOT" || rawType === "VACANT PLOT" || rawType === "VACANT";
              let typeLabel = "House";
              if (isVacant) typeLabel = "Vacant Plot";
              else if (rawType.includes("BUILDING") || rawType.includes("COMMERCIAL")) typeLabel = "Building";
              else if (rawType.includes("OTHER")) typeLabel = "Other";

              const currOwner = prop.current_owner_name ?? prop.owner_name ?? "Not available";
              const prevOwner = prop.previous_owner_name ?? "Not available";
              const residents = prop.resident_count;

              return (
                <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 space-y-2">
                  <h3 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5 text-[#2D5016]" />
                    <span>Ownership &amp; Residents</span>
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
              const prop = (state.data.property ?? state.data.parcel?.properties ?? {}) as Record<string, any>;
              const currentYear = new Date().getFullYear();
              const valYear = prop.valuation_year ?? currentYear;

              const formatINR = (val: any) => {
                if (val == null || val === "" || isNaN(Number(val))) return "Not available";
                return "₹" + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 0 });
              };

              const purchaseStr = formatINR(prop.purchase_price_inr);
              const sellingStr = formatINR(prop.estimated_selling_price_inr);

              return (
                <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-[#C4922A]" />
                      <span>Property Value</span>
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

            {/* AI Extracted Features */}
            {state.data.ai_features.length > 0 && (
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[#C4922A]" />
                    <span>AI Feature Extraction</span>
                  </h3>
                  <span className="text-[9px] font-mono bg-[#C4922A]/15 text-[#C4922A] px-1.5 py-0.5 rounded font-bold">
                    PROTOTYPE MODEL
                  </span>
                </div>

                <p className="text-[10px] text-[#8A8A8A] italic">
                  AI-derived feature output — analytical estimation, not official cadastral survey.
                </p>

                <div className="space-y-2">
                  {state.data.ai_features.map((feat, i) => {
                    const fp = feat.properties ?? {};
                    return (
                      <div key={i} className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-lg p-2.5 space-y-1">
                        <Row label="Feature Type" value={String((fp as any).feature_type ?? fp.source_class_name ?? "Building Footprint")} />
                        <Row label="Detected Area" value={fp.area_m2 ? `${fp.area_m2} m²` : "—"} />
                        <Row label="Confidence Score" value={fp.confidence != null ? `${(Number(fp.confidence) * 100).toFixed(0)}%` : "—"} />
                        <Row label="AI Model" value={String(fp.model ?? "Drishti-UAV-v1")} />
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Potential Discrepancy Analysis */}
            {state.data.discrepancies.length > 0 && (
              <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-[10px] font-bold text-[#C4922A] uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-[#C4922A]" />
                    <span>Discrepancy Analysis</span>
                  </h3>
                  <span className="text-[9px] font-mono bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-bold">
                    REQUIRES VERIFICATION
                  </span>
                </div>

                <div className="space-y-2">
                  {state.data.discrepancies.map((d: any, i: number) => (
                    <div key={i} className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-lg p-2.5 space-y-1.5">
                      <div className="font-semibold text-rose-700 text-xs flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                        <span>{String(d.ui_label ?? "Potential discrepancy — Requires verification")}</span>
                      </div>
                      <Row label="Type" value={String(d.type ?? "Area Discrepancy")} />
                      <Row label="Recorded Area" value={d.official_value ? `${d.official_value} m²` : "—"} />
                      <Row label="AI Extracted Area" value={d.ai_value ? `${d.ai_value} m²` : "—"} />
                      <Row label="Area Variance" value={d.difference != null ? `+${d.difference} m² (${d.difference_pct}%)` : "—"} />
                      <p className="text-[10px] text-[#8A8A8A] italic pt-1 border-t border-[#E8E0D0]">
                        {String(d._disclaimer ?? "Not a legal determination. Ground verification required.")}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Historical Epoch Note */}
            <section className="bg-[#EDE8DE]/60 border border-[#E8E0D0] rounded-xl p-3 text-[11px] text-[#6B6B6B]">
              <div className="flex items-center gap-1.5 font-bold text-[#2C2C2C] mb-1">
                <span>🕒 Temporal Analysis</span>
              </div>
              <p>Historical change comparison is unavailable for this parcel. Additional time epochs have not been acquired.</p>
            </section>

          </div>
        )}
      </div>

    </aside>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs py-0.5 border-b border-[#EDE8DE] last:border-0">
      <span className="text-[#6B6B6B]">{label}</span>
      <span className="font-medium text-[#2C2C2C]">{value}</span>
    </div>
  );
}
