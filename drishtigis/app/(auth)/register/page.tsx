import type { Metadata } from "next";
export const metadata: Metadata = { title: "Register — DrishtiGIS" };
export default function RegisterPage() {
  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-cream)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-ui)", padding: "2rem" }}>
      <div style={{ width: "100%", maxWidth: "360px" }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: "1.75rem", color: "var(--color-forest)", marginBottom: "0.5rem" }}>Create Account</h1>
        <p style={{ color: "var(--color-soft-gray)", fontSize: "0.875rem", marginBottom: "2rem" }}>Registration — implementation in progress</p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-soft-gray)" }}>Route: /register</p>
      </div>
    </main>
  );
}
