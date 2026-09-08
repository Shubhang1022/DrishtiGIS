import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "DrishtiGIS \u2014 A Clearer View of a Brighter Tomorrow",
};

export default function LandingPage() {
  return (
    <main
      style={{
        minHeight: "100dvh",
        background: "var(--color-cream)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "var(--font-ui)",
      }}
    >
      <h1
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(2rem, 5vw, 3.5rem)",
          color: "var(--color-charcoal)",
          textAlign: "center",
          lineHeight: 1.15,
          marginBottom: "1rem",
          maxWidth: "700px",
        }}
      >
        A Clearer View of a Brighter Tomorrow.
      </h1>
      <p
        style={{
          color: "var(--color-soft-gray)",
          fontSize: "1.125rem",
          textAlign: "center",
          maxWidth: "520px",
          marginBottom: "2.5rem",
          lineHeight: 1.6,
        }}
      >
        AI-powered urban geospatial intelligence. Aerial imagery, cadastral
        analysis, and discrepancy detection \u2014 in one map-first platform.
      </p>
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
        <Link
          href="/app/map"
          style={{
            display: "inline-block",
            background: "var(--color-forest)",
            color: "var(--color-cream-light)",
            padding: "0.75rem 1.75rem",
            borderRadius: "var(--radius)",
            fontWeight: 600,
            fontSize: "0.95rem",
            textDecoration: "none",
            transition: "opacity 150ms",
          }}
        >
          Explore DrishtiGIS \u2192
        </Link>
        <Link
          href="/login"
          style={{
            display: "inline-block",
            background: "transparent",
            color: "var(--color-charcoal)",
            padding: "0.75rem 1.75rem",
            borderRadius: "var(--radius)",
            fontWeight: 500,
            fontSize: "0.95rem",
            textDecoration: "none",
            border: "1px solid var(--color-beige)",
          }}
        >
          Sign In
        </Link>
      </div>
      <div
        style={{
          marginTop: "3rem",
          fontSize: "0.7rem",
          color: "var(--color-soft-gray)",
          textAlign: "center",
        }}
      >
        Prototype Dataset \u2014 Bhopal, Madhya Pradesh &nbsp;&middot;&nbsp; SIH26012
      </div>
    </main>
  );
}
