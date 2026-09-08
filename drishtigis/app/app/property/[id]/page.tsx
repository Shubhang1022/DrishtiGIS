import type { Metadata } from "next";
export const metadata: Metadata = { title: "Property Details \u2014 DrishtiGIS" };
export default function PropertyPage() {
  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-cream)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-ui)", padding: "2rem" }}>
      <div style={{ maxWidth: "480px" }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", color: "var(--color-charcoal)", marginBottom: "0.75rem" }}>Property Details</h1>
        <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem", marginBottom: "0.5rem" }}>Property panel \u2014 implementation in progress</p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-soft-gray)" }}>Route: /app/property/[id]</p>
      </div>
    </main>
  );
}
