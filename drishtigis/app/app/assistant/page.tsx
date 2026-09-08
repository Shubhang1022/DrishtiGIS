import type { Metadata } from "next";
export const metadata: Metadata = { title: "Ask DrishtiGIS" };
export default function AssistantPage() {
  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-cream)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-ui)", padding: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: "480px" }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", color: "var(--color-charcoal)", marginBottom: "0.75rem" }}>Ask DrishtiGIS</h1>
        <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem", marginBottom: "0.5rem" }}>AI property assistant — implementation in progress</p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-soft-gray)" }}>Route: /app/assistant</p>
      </div>
    </main>
  );
}
