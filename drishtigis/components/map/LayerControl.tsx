"use client";

/**
 * DrishtiGIS — Layer Visibility Control
 * =======================================
 * Allows toggling individual map layer visibility.
 * Positioned over the map (absolute, top-right below navigation).
 * Accessibility: fieldset/legend pattern, keyboard navigable.
 */

import type { LayerVisibility } from "@/lib/gis/coverage";

interface LayerControlProps {
  visibility: LayerVisibility;
  onChange: (layer: keyof LayerVisibility, visible: boolean) => void;
}

const LAYER_LABELS: Record<keyof LayerVisibility, string> = {
  uavImagery:   "UAV Imagery",
  parcels:      "Parcels",
  aiFeatures:   "AI Features",
  osmBuildings: "OSM Buildings",
  osmRoads:     "OSM Roads",
  osmWaterways: "OSM Waterways",
  osmLanduse:   "OSM Land Use",
};

const LAYER_ORDER: (keyof LayerVisibility)[] = [
  "uavImagery",
  "parcels",
  "aiFeatures",
  "osmRoads",
  "osmWaterways",
  "osmBuildings",
  "osmLanduse",
];

export function LayerControl({ visibility, onChange }: LayerControlProps) {
  return (
    <div
      style={{
        position:        "absolute",
        top:             "3.5rem",
        right:           "0.75rem",
        background:      "rgba(247,243,236,0.95)",
        border:          "1px solid var(--color-beige)",
        borderRadius:    "var(--radius)",
        padding:         "0.5rem 0.75rem",
        zIndex:          10,
        boxShadow:       "var(--shadow-panel)",
        minWidth:        "10rem",
        backdropFilter:  "blur(4px)",
      }}
      role="region"
      aria-label="Map layer controls"
    >
      <fieldset style={{ border: "none", margin: 0, padding: 0 }}>
        <legend
          style={{
            fontSize:    "0.65rem",
            fontWeight:  600,
            color:       "var(--color-soft-gray)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            marginBottom: "0.4rem",
            display:     "block",
          }}
        >
          Layers
        </legend>

        {LAYER_ORDER.map((layer) => (
          <label
            key={layer}
            style={{
              display:        "flex",
              alignItems:     "center",
              gap:            "0.4rem",
              fontSize:       "0.75rem",
              color:          "var(--color-charcoal)",
              cursor:         "pointer",
              padding:        "0.15rem 0",
              userSelect:     "none",
            }}
          >
            <input
              type="checkbox"
              checked={visibility[layer]}
              onChange={(e) => onChange(layer, e.target.checked)}
              aria-label={`Toggle ${LAYER_LABELS[layer]} layer`}
              style={{
                accentColor: "var(--color-forest)",
                width:       "0.875rem",
                height:      "0.875rem",
                cursor:      "pointer",
              }}
            />
            {LAYER_LABELS[layer]}
          </label>
        ))}
      </fieldset>
    </div>
  );
}
