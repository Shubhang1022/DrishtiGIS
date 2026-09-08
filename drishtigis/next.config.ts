import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // MapLibre GL JS v6 is ESM-only and browser-only.
  // The primary SSR guard is next/dynamic with { ssr: false } in the component.
  // Next.js 16 uses Turbopack by default — no webpack config needed.
  // Empty turbopack config suppresses the "webpack config but no turbopack" warning.
  turbopack: {},

  // GeoJSON files are imported as JS modules via require().
  // Next.js + webpack/Turbopack handle this natively via resolveJsonModule in tsconfig.
};

export default nextConfig;
