"use client";

import Link from "next/link";
import { ArrowLeft, History, Info, Calendar, Sliders, Layers } from "lucide-react";

export default function HistoryPage() {
  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      {/* Top Header */}
      <header className="bg-[#FBF9F5] border-b border-[#E8E0D0] px-4 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app/map" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]">
            <ArrowLeft className="w-4 h-4" />
            <span>Return to WebGIS Map</span>
          </Link>
          <span className="text-[#8A8A8A]">/</span>
          <div className="flex items-center gap-1.5 font-display font-bold text-sm text-[#2C2C2C]">
            <History className="w-4 h-4 text-[#2D5016]" />
            <span>Temporal Change Analysis</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#8A8A8A] font-mono">Bhopal Prototype Zone</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 lg:p-8 flex flex-col space-y-6">
        
        {/* Honest Status Disclaimer Banner */}
        <div className="bg-[#EDE8DE] border border-[#E8E0D0] rounded-xl p-4 flex items-start gap-3 text-xs text-[#6B6B6B]">
          <Info className="w-5 h-5 text-[#C4922A] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold text-[#2C2C2C]">
              Historical Imagery Status — Single Temporal Epoch Available
            </div>
            <p>
              Historical imagery and multi-temporal change detection are not yet active for the Bhopal prototype area. A second time epoch (Epoch T2) has not been acquired by UAV survey. The visual split interface shell below demonstrates the production workflow when multi-temporal data is connected.
            </p>
          </div>
        </div>

        {/* Dual Temporal Viewer Interface Shell */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 shadow-panel flex flex-col space-y-4">
          
          {/* Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E8E0D0] pb-3 text-xs">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-[#F7F3EC] px-3 py-1.5 rounded-lg border border-[#E8E0D0]">
                <Calendar className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="font-semibold text-[#2C2C2C]">Epoch 1: UAV Baseline (March 2024)</span>
              </div>
              <span className="text-[#8A8A8A] font-bold">VS</span>
              <div className="flex items-center gap-2 bg-[#EDE8DE] opacity-60 px-3 py-1.5 rounded-lg border border-[#E8E0D0]">
                <Calendar className="w-3.5 h-3.5 text-[#8A8A8A]" />
                <span className="font-semibold text-[#6B6B6B]">Epoch 2: Future Survey (Pending)</span>
              </div>
            </div>

            <div className="flex items-center gap-2 text-[#8A8A8A]">
              <Sliders className="w-3.5 h-3.5" />
              <span>Split Slider 50%</span>
            </div>
          </div>

          {/* Dual Canvas Grid Placeholder */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-[420px]">
            
            {/* Left Viewer (Epoch 1) */}
            <div className="relative rounded-xl border border-[#E8E0D0] overflow-hidden bg-[#1A1A1A] flex flex-col items-center justify-center text-white">
              <div 
                className="absolute inset-0 bg-cover bg-center opacity-80"
                style={{
                  backgroundImage: `url('https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?q=80&w=1200&auto=format&fit=crop')`,
                }}
              />
              <div className="absolute top-3 left-3 bg-[#2D5016] text-[#FBF9F5] px-2.5 py-1 rounded text-xs font-bold shadow">
                Epoch T1 — Baseline UAV 2024
              </div>
            </div>

            {/* Right Viewer (Epoch 2 - Unavailable) */}
            <div className="relative rounded-xl border border-[#E8E0D0] overflow-hidden bg-[#EDE8DE] flex flex-col items-center justify-center text-center p-6 space-y-3">
              <History className="w-10 h-10 text-[#8A8A8A]" />
              <div className="space-y-1">
                <h3 className="font-bold text-sm text-[#2C2C2C]">Epoch T2 Survey Pending</h3>
                <p className="text-xs text-[#6B6B6B] max-w-xs mx-auto">
                  Multi-temporal change analysis will automatically compare building footprints & vegetation index once T2 imagery is uploaded.
                </p>
              </div>
              <span className="text-[10px] font-mono bg-[#E8E0D0] text-[#6B6B6B] px-2 py-1 rounded">
                Awaiting Epoch T2 UAV Scan
              </span>
            </div>

          </div>

        </div>

      </main>

    </div>
  );
}
