import type { Metadata } from "next";
import Link from "next/link";
import { 
  Search, 
  MapPin, 
  ArrowRight, 
  Play, 
  Layers, 
  Building2, 
  Route as RoadIcon, 
  Trees, 
  Grid, 
  AlertTriangle, 
  Sparkles, 
  History, 
  Compass, 
  Bot, 
  ChevronDown,
  Building,
  ShieldCheck,
  Globe2
} from "lucide-react";

export const metadata: Metadata = {
  title: "DrishtiGIS — A Clearer View of a Brighter Tomorrow",
  description:
    "India-scale geospatial intelligence platform powered by aerial imagery, GIS, and AI for cadastral mapping and urban parcel intelligence.",
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F6F2EA] text-[#23211E] flex flex-col font-sans selection:bg-[#0E5A3A] selection:text-[#F6F2EA]">
      
      {/* ── Top Navigation Bar (Exact 84px height) ───────────────────────── */}
      <header className="h-[84px] sticky top-0 z-50 bg-[#F6F2EA]/95 backdrop-blur-md border-b border-[#E4DBCF] px-6 lg:px-12 flex items-center justify-between">
        <div className="max-w-[1440px] mx-auto w-full flex items-center justify-between gap-6">
          
          {/* Left: DrishtiGIS Brand Logo */}
          <Link href="/" className="flex items-center gap-3 shrink-0 group">
            <div className="w-10 h-10 rounded-xl bg-[#0E5A3A] text-[#F6F2EA] flex items-center justify-center shadow-xs group-hover:bg-[#2E6A4E] transition-colors">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="font-display font-bold text-xl text-[#0E5A3A] tracking-tight leading-none">
                DrishtiGIS
              </span>
              <span className="text-[10px] text-[#69635C] font-medium tracking-wide mt-1">
                Maps Today. Better Tomorrows.
              </span>
            </div>
          </Link>

          {/* Center: Nav Links */}
        

          {/* Right: Search, Location Dropdown & Get Started CTA */}
          <div className="flex items-center gap-3.5 shrink-0">
            
          

            {/* Location Selector */}
          
            {/* Get Started CTA Button */}
            <Link
              href="/app/map"
              className="inline-flex items-center gap-2 bg-[#0E5A3A] text-[#F6F2EA] hover:bg-[#2E6A4E] px-5 py-2.5 rounded-xl font-semibold text-xs transition-all shadow-xs"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

          </div>

        </div>
      </header>

      {/* ── Hero Section (12-Column Grid: Left 42%, Right 58%) ───────────── */}
      <section className="pt-8 lg:pt-14 pb-16 px-6 lg:px-12 max-w-[1440px] mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          
          {/* Left Column (42% / 5 Cols) */}
          <div className="lg:col-span-5 flex flex-col items-start space-y-6">
            
            {/* Category Eyebrow with Golden Accent Line */}
            <div className="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[#0E5A3A]">
              <span className="w-7 h-[2px] bg-[#B7862E]" />
              <span>GEOSPATIAL INTELLIGENCE FOR A MORE LIVABLE TOMORROW</span>
            </div>

            {/* Exact 4-Line Editorial Headline */}
            <h1 className="font-display font-normal text-[#23211E] text-5xl md:text-6xl lg:text-[76px] leading-[0.93] tracking-tight">
              A Clearer<br />
              <span className="font-serif-italic font-normal text-[#0E5A3A]">View</span> of a<br />
              Brighter<br />
              <span className="font-serif-italic font-normal text-[#B7862E]">Tomorrow.</span>
            </h1>

            {/* Description Paragraph (520px max width, 3 lines) */}
            <p className="text-base text-[#69635C] leading-[1.65] max-w-[520px]">
              AI-powered urban parcel mapping, cadastral intelligence and geospatial analytics for transparent, sustainable and people-centric cities.
            </p>

            {/* CTA Buttons (56px height, 16px radius, 20px gap, no shadows) */}
            <div className="flex flex-wrap items-center gap-5 pt-2">
              <Link
                href="/app/map"
                className="inline-flex items-center justify-center gap-3 bg-[#0E5A3A] hover:bg-[#2E6A4E] text-[#F6F2EA] px-7 h-[56px] rounded-[16px] font-semibold text-sm transition-all"
              >
                <span>Explore the Map</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <Link
                href="/app/location"
                className="inline-flex items-center justify-center gap-2.5 bg-[#F6F2EA] hover:bg-[#E4DBCF]/60 text-[#23211E] border border-[#E4DBCF] px-6 h-[56px] rounded-[16px] font-medium text-sm transition-all"
              >
                <div className="w-6 h-6 rounded-full bg-[#0E5A3A]/10 flex items-center justify-center text-[#0E5A3A]">
                  <Play className="w-3 h-3 fill-current ml-0.5" />
                </div>
                <span>Watch Video</span>
              </Link>
            </div>

          </div>

          {/* Right Column (58% / 7 Cols) — Hero Aerial Visual */}
          <div className="lg:col-span-7 relative">
            
            {/* Aerial Canvas Container with 32px Radius */}
            <div className="relative rounded-[32px] overflow-hidden border border-[#E4DBCF] bg-[#1A1A1A] shadow-2xl group">
              <img
                src="/hero-artwork.jpg"
                alt="DrishtiGIS Urban Parcel Intelligence - Real Cities Real Change"
                className="w-full h-auto object-cover object-center rounded-[32px] block transition-transform duration-700 group-hover:scale-[1.01]"
              />
            </div>
          </div>

        </div>
      </section>

      {/* ── Metrics & Institutional Trust Strip ───────────────────────────── */}
      <section className="bg-[#E4DBCF]/40 border-y border-[#E4DBCF] py-8 px-6 lg:px-12">
        <div className="max-w-[1440px] mx-auto flex flex-col lg:flex-row items-center justify-between gap-8">
          
          {/* Key Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 lg:gap-12 w-full lg:w-auto">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center font-bold text-lg">
                🏷️
              </div>
              <div>
                <div className="text-xl font-bold font-display text-[#23211E]">1K+</div>
                <div className="text-xs text-[#69635C]">Parcels Mapped</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center font-bold text-lg">
                🎯
              </div>
              <div>
                <div className="text-xl font-bold font-display text-[#23211E]">98%</div>
                <div className="text-xs text-[#69635C]">Detection Accuracy</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center font-bold text-lg">
                🏙️
              </div>
              <div>
                <div className="text-xl font-bold font-display text-[#23211E]">10+</div>
                <div className="text-xs text-[#69635C]">Cities Supported</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center font-bold text-lg">
                👥
              </div>
              <div>
                <div className="text-xl font-bold font-display text-[#23211E]">Smarter</div>
                <div className="text-xs text-[#69635C]">Urban Governance</div>
              </div>
            </div>
          </div>

          {/* Government Trust Badges */}
          <div className="flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left border-t lg:border-t-0 border-[#E4DBCF] pt-6 lg:pt-0 w-full lg:w-auto justify-end">
            <span className="text-[11px] font-semibold text-[#69635C] uppercase tracking-wider max-w-[140px] leading-tight">
              Trusted by government and institutions
            </span>
            <div className="flex flex-wrap items-center justify-center gap-4 opacity-90">
              <div className="flex items-center gap-2 bg-[#F6F2EA] border border-[#E4DBCF] px-3 py-1.5 rounded-md text-xs font-semibold text-[#23211E]">
                <ShieldCheck className="w-4 h-4 text-[#0E5A3A]" />
                <div>
                  <span className="block text-[10px] leading-none font-bold">Ministry of Housing</span>
                  <span className="text-[8px] text-[#69635C]">and Urban Affairs</span>
                </div>
              </div>
              <div className="flex items-center gap-2 bg-[#F6F2EA] border border-[#E4DBCF] px-3 py-1.5 rounded-md text-xs font-bold text-[#23211E]">
                <Globe2 className="w-4 h-4 text-[#B7862E]" />
                <span>Digital India</span>
              </div>
              <div className="flex items-center gap-2 bg-[#F6F2EA] border border-[#E4DBCF] px-3 py-1.5 rounded-md text-xs font-bold text-[#23211E]">
                <Building className="w-4 h-4 text-[#2E6A4E]" />
                <span>Smart Cities Mission</span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ── "From Aerial Data to Real Impact" Features Section ───────────── */}
      <section id="product" className="py-20 px-6 lg:px-12 max-w-[1440px] mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          
          {/* Left Title */}
          <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-mono text-[#B7862E] font-bold">01</span>
              <div className="h-px bg-[#E4DBCF] flex-1" />
              <span className="text-xs font-bold uppercase tracking-widest text-[#0E5A3A]">
                — WHAT WE DO
              </span>
            </div>

            <h2 className="text-3xl md:text-4xl font-display font-normal text-[#23211E] leading-tight">
              From{" "}
              <span className="font-serif-italic font-normal text-[#0E5A3A]">
                Aerial Data
              </span>{" "}
              to{" "}
              <span className="font-serif-italic text-[#0E5A3A]">
                Real Impact
              </span>
            </h2>

            <p className="text-sm text-[#69635C] leading-relaxed">
              DrishtiGIS turns aerial imagery and cadastral data into actionable intelligence — helping governments and urban planners build transparent, efficient and sustainable cities.
            </p>

            <Link
              href="/app/location"
              className="inline-flex items-center gap-2 text-xs font-bold text-[#0E5A3A] hover:text-[#2E6A4E] uppercase tracking-wider group"
            >
              <span>Learn More</span>
              <div className="w-6 h-6 rounded-full bg-[#0E5A3A]/10 flex items-center justify-center group-hover:translate-x-1 transition-transform">
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>
          </div>

          {/* Right 3x2 Feature Cards Grid */}
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            <div className="bg-[#F6F2EA] border border-[#E4DBCF] rounded-xl p-5 hover:shadow-md transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#23211E]">AI Feature Extraction</h3>
              <p className="text-xs text-[#69635C] leading-relaxed">
                Automatically detect buildings, roads and urban features from aerial imagery.
              </p>
            </div>

            <div className="bg-[#F6F2EA] border border-[#E4DBCF] rounded-xl p-5 hover:shadow-md transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#23211E]">Cadastral Intelligence</h3>
              <p className="text-xs text-[#69635C] leading-relaxed">
                Link detected features with official parcel data using spatial analysis.
              </p>
            </div>

            <div className="bg-[#F6F2EA] border border-[#E4DBCF] rounded-xl p-5 hover:shadow-md transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#B7862E]/10 text-[#B7862E] flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#23211E]">Discrepancy Detection</h3>
              <p className="text-xs text-[#69635C] leading-relaxed">
                Identify boundary, area and structural inconsistencies.
              </p>
            </div>

            <div className="bg-[#F6F2EA] border border-[#E4DBCF] rounded-xl p-5 hover:shadow-md transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center">
                <History className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#23211E]">Historical Analysis</h3>
              <p className="text-xs text-[#69635C] leading-relaxed">
                Compare multi-temporal imagery to detect changes over time.
              </p>
            </div>

            <div className="bg-[#F6F2EA] border border-[#E4DBCF] rounded-xl p-5 hover:shadow-md transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center">
                <Compass className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#23211E]">Interactive WebGIS</h3>
              <p className="text-xs text-[#69635C] leading-relaxed">
                A powerful, easy-to-use map interface for every stakeholder.
              </p>
            </div>

            <div className="bg-[#F6F2EA] border border-[#E4DBCF] rounded-xl p-5 hover:shadow-md transition-all space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#0E5A3A]/10 text-[#0E5A3A] flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#23211E]">AI Assistant</h3>
              <p className="text-xs text-[#69635C] leading-relaxed">
                Ask questions, get insights and understand your property with natural language.
              </p>
            </div>
          </div>

        </div>

        {/* Pan-India Architecture & Validation Scope Note */}
        <div className="mt-12 bg-[#F6F2EA] border border-[#E4DBCF] rounded-2xl p-6 lg:p-8 space-y-3">
          <div className="flex items-center gap-2 font-bold text-sm text-[#0E5A3A] uppercase tracking-wider">
            <Globe2 className="w-4 h-4 text-[#0E5A3A]" />
            <span>Pan-India Architecture & Regional Validation Scope</span>
          </div>
          <p className="text-xs text-[#69635C] leading-relaxed">
            <strong className="text-[#23211E]">Pan-India Architecture:</strong> DrishtiGIS is built around region-aware datasets, dynamic CRS projection handling, multi-tier dataset governance, and spatial analytics workflows designed to scale across multiple Indian states, cities, and municipal jurisdictions.
          </p>
          <p className="text-xs text-[#69635C] leading-relaxed pt-1 border-t border-[#E4DBCF]">
            <strong className="text-[#23211E]">Current Demonstration Validation:</strong> The current working demonstration is validated using UAVPal aerial imagery and synthetic demonstration parcel data for <strong>Bhopal, Madhya Pradesh</strong>.
          </p>
        </div>
      </section>

      {/* ── Quote & Smarter Tomorrow Banner Section ──────────────────────── */}
      <section className="py-12 px-6 lg:px-12 max-w-[1440px] mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 bg-[#E4DBCF]/60 border border-[#E4DBCF] rounded-2xl p-8 lg:p-12 relative overflow-hidden flex flex-col justify-between min-h-[320px]">
            <span className="text-6xl font-display text-[#B7862E]/40 font-bold leading-none select-none">
              “
            </span>
            <div className="relative z-10 my-4">
              <h3 className="text-2xl md:text-3xl font-display font-normal text-[#23211E] italic leading-tight max-w-lg">
                Accurate Maps. Transparent Records. Stronger Communities.
              </h3>
            </div>
            <div className="flex items-center justify-between text-xs text-[#69635C] border-t border-[#E4DBCF] pt-4 z-10">
              <span className="font-mono tracking-wider">PAN-INDIA ARCHITECTURE &nbsp;&middot;&nbsp; CADASTRAL AI PLATFORM</span>
              <span>DrishtiGIS Vision</span>
            </div>
            <div 
              className="absolute right-0 bottom-0 opacity-15 pointer-events-none w-80 h-60 bg-contain bg-no-repeat bg-right-bottom"
              style={{
                backgroundImage: `url('https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?q=80&w=800&auto=format&fit=crop')`,
              }}
            />
          </div>

          <div className="lg:col-span-5 bg-[#0E5A3A] text-[#F6F2EA] rounded-2xl p-8 lg:p-10 flex flex-col justify-between space-y-6 shadow-xl relative overflow-hidden">
            <div>
              <span className="text-[10px] font-mono tracking-widest text-[#B7862E] uppercase block mb-3">
                — A SMARTER TOMORROW
              </span>
              <h3 className="text-2xl md:text-3xl font-display font-bold leading-snug">
                Built on Data, Designed for People.
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs text-[#F6F2EA]/90">
              <div className="flex items-center gap-2 bg-[#2E6A4E]/60 px-3 py-2 rounded-lg border border-white/10">
                <span>🏛️</span>
                <span className="font-medium">Better Governance</span>
              </div>
              <div className="flex items-center gap-2 bg-[#2E6A4E]/60 px-3 py-2 rounded-lg border border-white/10">
                <span>🗺️</span>
                <span className="font-medium">Efficient Planning</span>
              </div>
              <div className="flex items-center gap-2 bg-[#2E6A4E]/60 px-3 py-2 rounded-lg border border-white/10">
                <span>🌱</span>
                <span className="font-medium">Sustainable Growth</span>
              </div>
              <div className="flex items-center gap-2 bg-[#2E6A4E]/60 px-3 py-2 rounded-lg border border-white/10">
                <span>🏙️</span>
                <span className="font-medium">More Livable Cities</span>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-white/10">
              <span className="text-xs text-[#F6F2EA]/70">Explore GIS Intelligence</span>
              <Link
                href="/app/map"
                className="w-10 h-10 rounded-full bg-[#2E6A4E] hover:bg-[#7D9154] text-[#F6F2EA] flex items-center justify-center transition-all shadow"
              >
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="mt-auto bg-[#F6F2EA] border-t border-[#E4DBCF] py-12 px-6 lg:px-12">
        <div className="max-w-[1440px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-[#69635C]">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded bg-[#0E5A3A] text-[#F6F2EA] flex items-center justify-center font-bold">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
              </svg>
            </div>
            <div>
              <span className="font-display font-bold text-sm text-[#0E5A3A] block">DrishtiGIS</span>
              <span className="text-[11px] text-[#69635C]">Maps for a More Livable India.</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6 font-medium">
            <Link href="#product" className="hover:text-[#0E5A3A]">Product</Link>
            <Link href="#use-cases" className="hover:text-[#0E5A3A]">Use Cases</Link>
            <Link href="#technology" className="hover:text-[#0E5A3A]">Technology</Link>
            <Link href="#impact" className="hover:text-[#0E5A3A]">Impact</Link>
            <Link href="#resources" className="hover:text-[#0E5A3A]">Resources</Link>
            <Link href="#about" className="hover:text-[#0E5A3A]">About</Link>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3 text-[#69635C]">
              <svg className="w-4 h-4 hover:text-[#0E5A3A] cursor-pointer fill-current" viewBox="0 0 24 24">
                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
              </svg>
              <svg className="w-4 h-4 hover:text-[#0E5A3A] cursor-pointer fill-current" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
              <svg className="w-4 h-4 hover:text-[#0E5A3A] cursor-pointer fill-current" viewBox="0 0 24 24">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
            </div>

            <div className="flex items-center gap-1.5 bg-[#E4DBCF] border border-[#E4DBCF] px-3 py-1.5 rounded-full text-[11px] font-medium text-[#23211E]">
              <span>🌱 Made for a Stronger, Greener Bharat</span>
              <span className="text-sm ml-0.5">🇮🇳</span>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
