/**
 * DrishtiGIS — Design System Preview
 * Used during development to verify design tokens render correctly.
 * Not a production page.
 */
export default function DesignSystemPage() {
  const swatches = [
    { name: "cream",       color: "var(--color-cream)",       label: "#F7F3EC" },
    { name: "beige",       color: "var(--color-beige)",       label: "#E8E0D0" },
    { name: "forest",      color: "var(--color-forest)",      label: "#2D5016" },
    { name: "olive",       color: "var(--color-olive)",       label: "#6B7C45" },
    { name: "ochre",       color: "var(--color-ochre)",       label: "#C4922A" },
    { name: "gold",        color: "var(--color-gold)",        label: "#D4A017" },
    { name: "charcoal",    color: "var(--color-charcoal)",    label: "#2C2C2C" },
    { name: "soft-gray",   color: "var(--color-soft-gray)",   label: "#8A8A8A" },
  ];

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "var(--color-cream)",
        padding: "2rem",
        fontFamily: "var(--font-ui)",
      }}
    >
      <h1
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "2rem",
          color: "var(--color-charcoal)",
          marginBottom: "0.25rem",
        }}
      >
        DrishtiGIS Design System
      </h1>
      <p style={{ color: "var(--color-soft-gray)", marginBottom: "2rem" }}>
        Token verification page — development only
      </p>

      {/* Colour swatches */}
      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-ui)", fontSize: "0.875rem", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-soft-gray)", marginBottom: "1rem" }}>
          Colour Tokens
        </h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
          {swatches.map((s) => (
            <div key={s.name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
              <div
                className="ds-swatch"
                style={{ background: s.color }}
                aria-label={`${s.name} colour swatch`}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--color-charcoal)" }}>{s.name}</span>
              <span style={{ fontSize: "0.625rem", color: "var(--color-soft-gray)" }}>{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Typography */}
      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-ui)", fontSize: "0.875rem", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-soft-gray)", marginBottom: "1rem" }}>
          Typography
        </h2>
        <p style={{ fontFamily: "var(--font-display)", fontSize: "2.5rem", color: "var(--color-charcoal)", lineHeight: 1.2 }}>
          A Clearer View of a Brighter Tomorrow.
        </p>
        <p style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", color: "var(--color-forest)", lineHeight: 1.3, fontStyle: "italic" }}>
          Display / Editorial Serif
        </p>
        <p style={{ fontFamily: "var(--font-ui)", fontSize: "1rem", color: "var(--color-charcoal)", marginTop: "1rem" }}>
          UI sans-serif — property details, map controls, body text, forms.
        </p>
        <p style={{ fontFamily: "var(--font-ui)", fontSize: "0.875rem", color: "var(--color-soft-gray)" }}>
          Small UI text — labels, captions, metadata.
        </p>
      </section>

      {/* Timing tokens */}
      <section>
        <h2 style={{ fontFamily: "var(--font-ui)", fontSize: "0.875rem", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-soft-gray)", marginBottom: "0.5rem" }}>
          Animation Durations
        </h2>
        {[
          ["micro",  "var(--duration-micro)",  "120–180ms — micro interactions"],
          ["normal", "var(--duration-normal)", "200–300ms — normal transitions"],
          ["map",    "var(--duration-map)",    "400–700ms — map transitions"],
          ["major",  "var(--duration-major)",  "500–800ms — major transitions"],
        ].map(([name, val, desc]) => (
          <p key={name} style={{ fontSize: "0.875rem", color: "var(--color-charcoal)", margin: "0.25rem 0" }}>
            <code style={{ fontFamily: "monospace", color: "var(--color-forest)" }}>--duration-{name}</code>
            {" = "}<code style={{ color: "var(--color-ochre)" }}>{val}</code>
            {" — "}{desc}
          </p>
        ))}
      </section>
    </main>
  );
}
