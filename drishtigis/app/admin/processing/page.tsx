"use client";

import Link from "next/link";
import { ArrowLeft, Cpu, CheckCircle2, Clock, AlertTriangle, RefreshCw } from "lucide-react";

export default function ProcessingQueuePage() {
  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      <header className="bg-[#1A1A1A] text-[#FBF9F5] px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-xs text-[#8A8A8A] hover:text-white flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Admin Console</span>
          </Link>
          <span className="text-[#8A8A8A]">/</span>
          <span className="font-display font-bold text-base text-white">GIS Tiling & AI Extraction Pipeline</span>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-panel space-y-4">
          <div className="flex items-center justify-between border-b border-[#E8E0D0] pb-3">
            <div>
              <h1 className="font-bold text-lg text-[#2C2C2C]">Pipeline Task Processing Queue</h1>
              <p className="text-xs text-[#6B6B6B]">Live background jobs for pyramid tile generation and building footprint segmentation.</p>
            </div>
            <button className="flex items-center gap-1.5 bg-[#EDE8DE] hover:bg-[#E8E0D0] px-3 py-1.5 rounded text-xs font-semibold">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh Status</span>
            </button>
          </div>

          <div className="space-y-3">
            
            {/* Task 1 */}
            <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-[#2D5016]">TASK-9042</span>
                  <span className="font-bold text-sm text-[#2C2C2C]">Bhopal COG Tile Pyramid Generation</span>
                </div>
                <p className="text-xs text-[#6B6B6B]">Generating XYZ raster tiles zoom 17 to 22 from 5cm Orthomosaic.</p>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <span className="bg-[#2D5016]/15 text-[#2D5016] px-2.5 py-1 rounded font-bold">
                  100% COMPLETED
                </span>
                <span className="text-[#8A8A8A] font-mono">1.4s</span>
              </div>
            </div>

            {/* Task 2 */}
            <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-[#C4922A]">TASK-9043</span>
                  <span className="font-bold text-sm text-[#2C2C2C]">U-Net Building Footprint Segmentation</span>
                </div>
                <p className="text-xs text-[#6B6B6B]">Extracting building geometry vectors & area polygons.</p>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <span className="bg-amber-100 text-amber-800 px-2.5 py-1 rounded font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-600 animate-ping" />
                  PROCESSING (85%)
                </span>
                <span className="text-[#8A8A8A] font-mono">4.2s</span>
              </div>
            </div>

          </div>
        </div>

      </main>

    </div>
  );
}
