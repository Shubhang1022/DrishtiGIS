"use client";

/**
 * DrishtiGIS — Coverage Unavailability Indicator
 * ================================================
 * Non-intrusive notice shown when the map is outside Bhopal's coverage area.
 * Communicates honestly that detailed AI/property analysis is not available
 * for the current map view — never fabricates or implies data that doesn't exist.
 */

interface CoverageIndicatorProps {
  /** True when the map center is near Bhopal (within threshold) */
  nearBhopal: boolean;
}

export function CoverageIndicator({ nearBhopal }: CoverageIndicatorProps) {
  if (nearBhopal) return null;

  return (
    <div
      style={{
        position:       "absolute",
        bottom:         "2.5rem",
        left:           "0.75rem",
        background:     "rgba(44,44,44,0.78)",
        color:          "#f7f3ec",
        borderRadius:   "var(--radius)",
        padding:        "0.375rem 0.75rem",
        fontSize:       "0.72rem",
        maxWidth:       "280px",
        lineHeight:     1.4,
        pointerEvents:  "none",
        zIndex:         8,
        backdropFilter: "blur(3px)",
      }}
      role="status"
      aria-live="polite"
      aria-label="Coverage availability notice"
    >
      Detailed AI/property analysis is not yet available for this area.
      Showing India-wide map context.
    </div>
  );
}
