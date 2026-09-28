"use client";

/**
 * DrishtiGIS — Coverage Indicator Component
 * ============================================
 * Displays a non-intrusive notification badge when the map viewport moves
 * outside the Bhopal prototype area (e.g. to Lucknow, Ludhiana, Delhi).
 *
 * Core requirement:
 *   Does NOT block map usage. Communicates that OSM base map & contextual
 *   data are available, but detailed AI property intelligence is currently
 *   limited to the Bhopal prototype area.
 */

import { Info, MapPin } from "lucide-react";

interface CoverageIndicatorProps {
  nearBhopal: boolean;
}

export function CoverageIndicator({ nearBhopal }: CoverageIndicatorProps) {
  // If user is inside the Bhopal prototype area, show subtle prototype active badge
  if (nearBhopal) {
    return (
      <div 
        className="absolute bottom-4 left-4 z-10 bg-[#2D5016]/90 backdrop-blur-md text-[#FBF9F5] border border-[#3A6B1E] px-3 py-1.5 rounded-lg text-xs font-medium shadow-lg flex items-center gap-2 pointer-events-auto"
        role="status"
        aria-live="polite"
      >
        <span className="w-2 h-2 rounded-full bg-[#7D9154] animate-pulse" />
        <span>Bhopal Prototype Area — Detailed Intelligence Active</span>
      </div>
    );
  }

  // Outside Bhopal prototype area
  return (
    <div 
      className="absolute bottom-4 left-4 z-10 bg-[#FBF9F5]/95 backdrop-blur-md border border-[#E8E0D0] px-3.5 py-2 rounded-xl text-xs text-[#2C2C2C] shadow-lg flex items-center gap-2.5 max-w-md pointer-events-auto transition-all"
      role="status"
      aria-live="polite"
    >
      <div className="w-6 h-6 rounded-full bg-[#C4922A]/15 text-[#C4922A] flex items-center justify-center shrink-0">
        <Info className="w-3.5 h-3.5" />
      </div>
      <div>
        <div className="font-semibold text-xs text-[#2C2C2C]">
          Map & Context Coverage Active
        </div>
        <div className="text-[11px] text-[#6B6B6B]">
          Detailed AI property intelligence is currently available for the <span className="font-medium text-[#2D5016]">Bhopal prototype area</span>.
        </div>
      </div>
    </div>
  );
}
