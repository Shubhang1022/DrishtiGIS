import type { Metadata } from "next";
export const metadata: Metadata = { title: "Historical Imagery — DrishtiGIS" };
export default function HistoryPage() {
  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-cream)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-ui)", padding: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: "480px" }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", color: "var(--color-charcoal)", marginBottom: "0.75rem" }}>Historical Imagery</h1>
        <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem", marginBottom: "0.5rem" }}>Historical comparison — implementation in progress</p>
        <p style={{ color: "var(--color-soft-gray)", fontSize: "0.75rem", marginBottom: "1rem" }}>Historical imagery is not available for the current prototype dataset. A second time epoch has not been acquired.</p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-soft-gray)" }}>Route: /app/history</p>
      </div>
    </main>
  );
}
