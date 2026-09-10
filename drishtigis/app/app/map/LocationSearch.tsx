"use client";

/**
 * DrishtiGIS — Location Search Component
 * =========================================
 * City search input that queries the backend location search endpoint.
 * On selection, calls onSelect(lat, lon, zoom) to pan the map.
 * Never fabricates intelligence availability for non-Bhopal cities.
 */

import { useState, useRef, useCallback } from "react";
import { searchLocations, type LocationResult } from "@/lib/api/locations";

interface LocationSearchProps {
  onSelect: (lat: number, lon: number, zoom: number) => void;
}

export function LocationSearch({ onSelect }: LocationSearchProps) {
  const [query,    setQuery]   = useState("");
  const [results,  setResults] = useState<LocationResult[]>([]);
  const [open,     setOpen]    = useState(false);
  const [loading,  setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const listboxId = "location-search-listbox";

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (val.trim().length < 2) { setResults([]); setOpen(false); return; }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchLocations(val.trim());
        setResults(res.results.slice(0, 8));
        setOpen(res.results.length > 0);
      } catch {
        setResults([]);
        setOpen(false);
      } finally {
        setLoading(false);
      }
    }, 300);
  }, []);

  const handleSelect = useCallback((r: LocationResult) => {
    setQuery(r.name);
    setOpen(false);
    setResults([]);
    onSelect(r.center.lat, r.center.lon, r.zoom_level);
  }, [onSelect]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") { setOpen(false); setQuery(""); }
  }, []);

  return (
    <div style={{ position: "relative", flex: 1, maxWidth: "320px" }}>
      {/* combobox wrapper carries aria-expanded on the container, not the input */}
      <div
        style={{ position: "relative", display: "flex", alignItems: "center" }}
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-owns={listboxId}
        aria-controls={listboxId}
      >
        <span
          style={{
            position: "absolute", left: "0.5rem",
            color: "var(--color-soft-gray)", fontSize: "0.875rem", pointerEvents: "none",
          }}
          aria-hidden="true"
        >
          🔍
        </span>
        <input
          type="search"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Search cities in India…"
          aria-label="Search Indian cities"
          aria-autocomplete="list"
          aria-controls={listboxId}
          style={{
            width:         "100%",
            paddingLeft:   "1.75rem",
            paddingRight:  "0.5rem",
            paddingTop:    "0.35rem",
            paddingBottom: "0.35rem",
            fontSize:      "0.8rem",
            border:        "1px solid var(--color-beige)",
            borderRadius:  "var(--radius)",
            background:    "var(--color-cream)",
            color:         "var(--color-charcoal)",
            outline:       "none",
            fontFamily:    "var(--font-ui)",
          }}
          onFocus={() => { if (results.length > 0) setOpen(true); }}
          onBlur={() => { setTimeout(() => setOpen(false), 150); }}
        />
        {loading && (
          <span style={{ position: "absolute", right: "0.5rem", fontSize: "0.75rem", color: "var(--color-soft-gray)" }}>
            …
          </span>
        )}
      </div>

      {/* Dropdown */}
      {open && results.length > 0 && (
        <ul
          id={listboxId}
          role="listbox"
          aria-label="City search results"
          style={{
            position:     "absolute",
            top:          "calc(100% + 0.25rem)",
            left:         0,
            right:        0,
            background:   "var(--color-cream-light)",
            border:       "1px solid var(--color-beige)",
            borderRadius: "var(--radius)",
            boxShadow:    "var(--shadow-panel)",
            zIndex:       100,
            listStyle:    "none",
            margin:       0,
            padding:      "0.25rem 0",
            maxHeight:    "14rem",
            overflowY:    "auto",
          }}
        >
          {results.map((r) => (
            <li
              key={`${r.name}-${r.state}`}
              role="option"
              aria-selected={false}
              onMouseDown={() => handleSelect(r)}
              style={{
                padding:  "0.4rem 0.75rem",
                cursor:   "pointer",
                fontSize: "0.8rem",
                color:    "var(--color-charcoal)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLLIElement).style.background = "var(--color-beige)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLLIElement).style.background = "transparent";
              }}
            >
              <span style={{ fontWeight: 500 }}>{r.name}</span>
              <span style={{ color: "var(--color-soft-gray)", marginLeft: "0.375rem", fontSize: "0.72rem" }}>
                {r.state}
              </span>
              {r.coverage.imagery_available && (
                <span
                  style={{
                    marginLeft:    "0.375rem",
                    fontSize:      "0.65rem",
                    background:    "var(--color-forest)",
                    color:         "var(--color-cream-light)",
                    borderRadius:  "2px",
                    padding:       "1px 4px",
                    verticalAlign: "middle",
                  }}
                  title="Prototype intelligence data available"
                >
                  prototype
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
