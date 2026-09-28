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
  onSelect: (lat: number, lon: number, zoom: number, bounds?: [[number, number], [number, number]], result?: LocationResult) => void;
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
    }, 200);
  }, []);

  const handleSelect = useCallback((r: LocationResult) => {
    setQuery(`${r.name}, ${r.state}`);
    setOpen(false);
    setResults([]);
    onSelect(r.center.lat, r.center.lon, r.zoom_level, r.bounds, r);
  }, [onSelect]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") { setOpen(false); setQuery(""); }
  }, []);

  return (
    <div style={{ position: "relative", flex: 1, maxWidth: "340px" }}>
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
            position: "absolute", left: "0.6rem", top: "50%", transform: "translateY(-50%)",
            color: "#69635C", fontSize: "0.85rem", pointerEvents: "none",
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
          placeholder="Search Indian cities (e.g. Bhopal, Lucknow)..."
          aria-label="Search Indian cities"
          aria-autocomplete="list"
          aria-controls={listboxId}
          style={{
            width:         "100%",
            paddingLeft:   "2rem",
            paddingRight:  "0.5rem",
            paddingTop:    "0.35rem",
            paddingBottom: "0.35rem",
            fontSize:      "0.8rem",
            border:        "1px solid #E4DBCF",
            borderRadius:  "10px",
            background:    "#F6F2EA",
            color:         "#23211E",
            outline:       "none",
            fontFamily:    "var(--font-sans, sans-serif)",
          }}
          onFocus={() => { if (results.length > 0) setOpen(true); }}
          onBlur={() => { setTimeout(() => setOpen(false), 200); }}
        />
        {loading && (
          <span style={{ position: "absolute", right: "0.6rem", top: "50%", transform: "translateY(-50%)", fontSize: "0.75rem", color: "#69635C" }}>
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
            top:          "calc(100% + 0.35rem)",
            left:         0,
            right:        0,
            background:   "#F6F2EA",
            border:       "1px solid #E4DBCF",
            borderRadius: "14px",
            boxShadow:    "0 10px 25px -5px rgba(0,0,0,0.1)",
            zIndex:       100,
            listStyle:    "none",
            margin:       0,
            padding:      "0.35rem 0",
            maxHeight:    "16rem",
            overflowY:    "auto",
          }}
        >
          {results.map((r) => {
            const hasData = r.coverage.coverage_source !== "none" || r.coverage.imagery_available;
            return (
              <li
                key={`${r.name}-${r.state}`}
                role="option"
                aria-selected={false}
                onMouseDown={() => handleSelect(r)}
                style={{
                  padding:  "0.5rem 0.75rem",
                  cursor:   "pointer",
                  fontSize: "0.8rem",
                  color:    "#23211E",
                  borderBottom: "1px solid #E4DBCF/40",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between"
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLLIElement).style.background = "#EDE8DE";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLLIElement).style.background = "transparent";
                }}
              >
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <div style={{ fontWeight: 600, display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <span>{r.name}</span>
                    <span style={{ color: "#69635C", fontWeight: 400, fontSize: "0.75rem" }}>({r.state})</span>
                  </div>
                  <span style={{ color: "#69635C", fontSize: "0.7rem", marginTop: "2px" }}>
                    {hasData ? "● Prototype intelligence active" : "Map & Context Available"}
                  </span>
                </div>
                {hasData ? (
                  <span
                    style={{
                      fontSize:      "0.65rem",
                      fontWeight:    600,
                      background:    "#0E5A3A",
                      color:         "#F6F2EA",
                      borderRadius:  "4px",
                      padding:       "2px 6px",
                      whiteSpace:    "nowrap"
                    }}
                    title="Prototype dataset & AI intelligence available"
                  >
                    Prototype
                  </span>
                ) : (
                  <span
                    style={{
                      fontSize:      "0.65rem",
                      background:    "rgba(228,219,207,0.8)",
                      color:         "#69635C",
                      borderRadius:  "4px",
                      padding:       "2px 6px",
                      whiteSpace:    "nowrap"
                    }}
                  >
                    OSM Context
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
