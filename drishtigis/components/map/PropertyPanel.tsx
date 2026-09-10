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
    // Only run when propertyId is non-null
    if (!propertyId) return;
    // Skip if same id already loaded
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId]);

  if (!propertyId) return null;

  const panelStyle: React.CSSProperties = {
    position:      "absolute",
    top:           0,
    right:         0,
    width:         "clamp(280px, 30vw, 360px)",
    height:        "100%",
    background:    "var(--color-cream-light)",
    borderLeft:    "1px solid var(--color-beige)",
    boxShadow:     "-4px 0 16px rgba(0,0,0,0.08)",
    zIndex:        20,
    overflowY:     "auto",
    fontFamily:    "var(--font-ui)",
    display:       "flex",
    flexDirection: "column",
  };

  // PROTOTYPE DISCLAIMER — always rendered first, never hidden
  const disclaimer = (
    <div
      style={{
        background:   "var(--color-beige)",
        border:       "1px solid var(--color-beige-light)",
        borderRadius: "var(--radius-sm)",
        padding:      "0.5rem 0.75rem",
        fontSize:     "0.7rem",
        color:        "var(--color-soft-gray-dark)",
        margin:       "0.75rem",
        lineHeight:   1.5,
      }}
      role="note"
      aria-label="Data disclaimer"
    >
      <strong style={{ color: "var(--color-charcoal)" }}>Demo data only.</strong>{" "}
      {state.status === "success"
        ? state.data._disclaimer
        : "This is prototype demonstration data. Not official government records."}
    </div>
  );

  if (state.status === "idle" || state.status === "loading") {
    return (
      <div style={panelStyle}>
        <PanelHeader propertyId={propertyId} onClose={onClose} />
        {disclaimer}
        <div style={{ padding: "1rem", color: "var(--color-soft-gray)", fontSize: "0.875rem" }}>
          {state.status === "loading" ? "Loading…" : ""}
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div style={panelStyle}>
        <PanelHeader propertyId={propertyId} onClose={onClose} />
        {disclaimer}
        <div
          style={{ padding: "1rem", color: "var(--color-soft-gray)", fontSize: "0.875rem" }}
          role="alert"
        >
          {state.message}
        </div>
      </div>
    );
  }

  const { data }  = state;
  const parcel    = data.parcel?.properties ?? {};
  const property  = data.property as Record<string, unknown> | null;
  const discs     = data.discrepancies as Array<Record<string, unknown>>;
  const aiFeats   = data.ai_features;

  return (
    <div style={panelStyle} role="complementary" aria-label="Property details">
      <PanelHeader propertyId={String(parcel.property_id ?? propertyId)} onClose={onClose} />
      {disclaimer}

      {/* Property basics */}
      <section style={{ padding: "0 0.75rem 0.75rem" }}>
        <Row label="Property ID"   value={String(parcel.property_id   ?? "—")} />
        <Row label="Plot"          value={String(parcel.plot_number    ?? "—")} />
        <Row label="Survey"        value={String(parcel.survey_number  ?? "—")} />
        <Row label="Area (m²)"     value={String(parcel.area_m2       ?? "—")} />
        <Row label="Type"          value={String(parcel.land_type      ?? "—")} />
        <Row label="Status"        value={String(parcel.status         ?? "—")} />
        {property && (
          <>
            <Row label="Address"   value={String(property.address      ?? "—")} />
            <Row label="Record"    value={String(property.record_status ?? "—")} />
            <Row label="Dataset"   value={String(property.source_label ?? "—")} />
          </>
        )}
      </section>

      {/* AI Analysis */}
      {aiFeats.length > 0 && (
        <section style={{ padding: "0 0.75rem 0.75rem" }}>
          <SectionHeading>AI Analysis</SectionHeading>
          <div style={{ fontSize: "0.65rem", color: "var(--color-soft-gray)", marginBottom: "0.5rem", fontStyle: "italic" }}>
            AI-derived — prototype model only. Not an official determination.
          </div>
          {aiFeats.map((feat, i) => {
            const fp = feat.properties ?? {};
            return (
              <div key={i} style={{ background: "var(--color-cream)", borderRadius: "var(--radius-sm)", padding: "0.5rem", marginBottom: "0.375rem", fontSize: "0.75rem" }}>
                <Row label="Feature type"  value={String(fp.feature_type ?? "—")} />
                <Row label="AI area (m²)"  value={String(fp.area_m2 ?? "—")} />
                <Row label="Confidence"    value={fp.confidence != null ? `${(Number(fp.confidence) * 100).toFixed(0)}%` : "—"} />
                <Row label="Model"         value={String(fp.model ?? "—")} />
              </div>
            );
          })}
        </section>
      )}

      {/* Discrepancies */}
      {discs.length > 0 && (
        <section style={{ padding: "0 0.75rem 0.75rem" }}>
          <SectionHeading>Potential Discrepancies</SectionHeading>
          {discs.map((d, i) => (
            <div key={i} style={{ background: "var(--color-cream)", borderRadius: "var(--radius-sm)", padding: "0.5rem", marginBottom: "0.375rem", fontSize: "0.75rem" }}>
              <div style={{ fontWeight: 600, color: "var(--color-ochre-dark)", marginBottom: "0.25rem", fontSize: "0.75rem" }}>
                {String(d.ui_label ?? "Potential discrepancy — Requires verification")}
              </div>
              <Row label="Type"          value={String(d.type           ?? "—")} />
              <Row label="Recorded (m²)" value={String(d.official_value ?? "—")} />
              <Row label="AI area (m²)"  value={String(d.ai_value       ?? "—")} />
              <Row label="Difference"    value={d.difference != null ? `${d.difference} m² (${d.difference_pct}%)` : "—"} />
              <Row label="Severity"      value={String(d.severity       ?? "—")} />
              <Row label="Status"        value={String(d.status         ?? "—")} />
              {/* legal_status is always null — never display legal language */}
              <div style={{ fontSize: "0.65rem", color: "var(--color-soft-gray)", marginTop: "0.375rem", fontStyle: "italic", lineHeight: 1.4 }}>
                {String(d._disclaimer ?? "Not a legal determination. Requires field verification.")}
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

function PanelHeader({ propertyId, onClose }: { propertyId: string; onClose: () => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.75rem", borderBottom: "1px solid var(--color-beige)", flexShrink: 0 }}>
      <span style={{ fontFamily: "var(--font-display)", fontSize: "0.9rem", fontWeight: 600, color: "var(--color-forest)" }}>
        {propertyId}
      </span>
      <button
        onClick={onClose}
        style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--color-soft-gray)", fontSize: "1rem", lineHeight: 1, padding: "0.25rem", borderRadius: "var(--radius-sm)" }}
        aria-label="Close property panel"
      >
        ✕
      </button>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", padding: "0.125rem 0", borderBottom: "1px solid var(--color-cream-dark)" }}>
      <span style={{ color: "var(--color-soft-gray)", flexShrink: 0, marginRight: "0.5rem" }}>{label}</span>
      <span style={{ color: "var(--color-charcoal)", textAlign: "right" }}>{value}</span>
    </div>
  );
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 style={{ fontSize: "0.65rem", fontWeight: 600, color: "var(--color-soft-gray)", letterSpacing: "0.08em", textTransform: "uppercase", margin: "0 0 0.5rem" }}>
      {children}
    </h3>
  );
}
