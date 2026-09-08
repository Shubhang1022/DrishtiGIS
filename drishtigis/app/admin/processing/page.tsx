import type { Metadata } from "next";
export const metadata: Metadata = { title: "Processing — DrishtiGIS Admin" };
export default function ProcessingPage() {
  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-cream)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-ui)", padding: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: "480px" }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", color: "var(--color-charcoal)", marginBottom: "0.75rem" }}>Processing Pipeline</h1>
        <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem", marginBottom: "0.5rem" }}>Processing workflow — implementation in progress</p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-soft-gray)" }}>Route: /admin/processing</p>
      </div>
    </main>
  );
}
