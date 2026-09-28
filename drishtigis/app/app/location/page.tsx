"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, MapPin, ArrowRight, ArrowLeft, CheckCircle2, Info, Compass, ShieldCheck } from "lucide-react";
import { searchLocations, type LocationResult } from "@/lib/api/locations";

export default function LocationPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (val.trim().length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const res = await searchLocations(val.trim());
      setResults(res.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCity = (r: LocationResult) => {
    // Navigate to /app/map with selected city coordinates
    router.push(`/app/map?lat=${r.center.lat}&lon=${r.center.lon}&zoom=${r.zoom_level}&city=${encodeURIComponent(r.name)}`);
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      {/* Header */}
      <header className="bg-[#FBF9F5] border-b border-[#E8E0D0] px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center font-bold">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
            </svg>
          </div>
          <span className="font-display font-bold text-lg text-[#2D5016]">
            DrishtiGIS
          </span>
        </Link>

        <Link
          href="/app/map"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]"
        >
          <span>Skip to Map</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-12 flex flex-col items-center">
        
        {/* Title */}
        <div className="text-center space-y-3 mb-8">
          <div className="inline-flex items-center gap-1.5 bg-[#2D5016]/10 text-[#2D5016] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
            <MapPin className="w-3.5 h-3.5" />
            <span>Geographic Scope — India</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-display font-normal text-[#2C2C2C]">
            Choose a Location
          </h1>
          <p className="text-sm text-[#6B6B6B] max-w-lg mx-auto leading-relaxed">
            Select a city or region to explore available geospatial datasets. High-resolution UAV aerial imagery and AI cadastral analytics are active for the <span className="font-semibold text-[#2D5016]">Bhopal validated demonstration region</span>.
          </p>
        </div>

        {/* Search Input Box */}
        <div className="w-full relative mb-8">
          <Search className="w-5 h-5 absolute left-4 top-3.5 text-[#8A8A8A]" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search Indian cities or regions (e.g. Lucknow, Bhopal, Pune)..."
            className="w-full bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl pl-12 pr-4 py-3 text-sm text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016] shadow-sm transition-all"
            autoFocus
          />
          {loading && (
            <span className="absolute right-4 top-3.5 text-xs text-[#8A8A8A]">
              Searching…
            </span>
          )}
        </div>

        {/* Autocomplete Results / Featured Cities */}
        <div className="w-full space-y-4">
          <h2 className="text-xs font-bold text-[#8A8A8A] uppercase tracking-wider">
            {query.trim().length > 0 ? "Search Results" : "Featured Demonstration Regions"}
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            
            {/* Bhopal Prototype Card */}
            <div 
              onClick={() => router.push('/app/map')}
              className="bg-[#FBF9F5] border-2 border-[#2D5016] rounded-xl p-4 cursor-pointer hover:shadow-md transition-all space-y-2 relative"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-base text-[#2D5016]">
                  <MapPin className="w-4 h-4 text-[#2D5016]" />
                  <span>Bhopal</span>
                </div>
                <span className="text-[10px] font-bold bg-[#2D5016] text-[#FBF9F5] px-2 py-0.5 rounded font-mono">
                  VALIDATED DEMO REGION
                </span>
              </div>
              <p className="text-xs text-[#6B6B6B]">Madhya Pradesh</p>

              <div className="pt-2 border-t border-[#E8E0D0] space-y-1 text-xs">
                <div className="flex items-center gap-1.5 text-[#2D5016] font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>UAV aerial raster tile coverage</span>
                </div>
                <div className="flex items-center gap-1.5 text-[#2D5016] font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>AI building extraction & demo parcels</span>
                </div>
              </div>
            </div>

            {/* Lucknow Card */}
            <div 
              onClick={() => router.push('/app/map')}
              className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl p-4 cursor-pointer hover:border-[#2D5016] transition-all space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-base text-[#2C2C2C]">
                  <MapPin className="w-4 h-4 text-[#8A8A8A]" />
                  <span>Lucknow</span>
                </div>
                <span className="text-[10px] font-medium bg-[#EDE8DE] text-[#6B6B6B] px-2 py-0.5 rounded">
                  CONTEXT MAP
                </span>
              </div>
              <p className="text-xs text-[#6B6B6B]">Uttar Pradesh</p>

              <div className="pt-2 border-t border-[#E8E0D0] space-y-1 text-xs">
                <div className="flex items-center gap-1.5 text-[#2D5016] font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Map coverage available</span>
                </div>
                <div className="flex items-center gap-1.5 text-[#8A8A8A]">
                  <Info className="w-3.5 h-3.5" />
                  <span>Detailed property intelligence not yet available</span>
                </div>
              </div>
            </div>

            {/* Dynamic Results */}
            {results.filter(r => r.name !== "Bhopal" && r.name !== "Lucknow").map((r) => (
              <div
                key={`${r.name}-${r.state}`}
                onClick={() => handleSelectCity(r)}
                className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl p-4 cursor-pointer hover:border-[#2D5016] transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-bold text-base text-[#2C2C2C]">
                    <MapPin className="w-4 h-4 text-[#8A8A8A]" />
                    <span>{r.name}</span>
                  </div>
                  <span className="text-[10px] font-medium bg-[#EDE8DE] text-[#6B6B6B] px-2 py-0.5 rounded">
                    CONTEXT MAP
                  </span>
                </div>
                <p className="text-xs text-[#6B6B6B]">{r.state}</p>

                <div className="pt-2 border-t border-[#E8E0D0] space-y-1 text-xs">
                  <div className="flex items-center gap-1.5 text-[#2D5016] font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Map coverage available</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[#8A8A8A]">
                    <Info className="w-3.5 h-3.5" />
                    <span>Detailed property intelligence not yet available</span>
                  </div>
                </div>
              </div>
            ))}

          </div>
        </div>

      </main>

    </div>
  );
}
