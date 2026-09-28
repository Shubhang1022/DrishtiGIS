"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckSquare, CheckCircle2, XCircle, AlertTriangle, ShieldCheck } from "lucide-react";

export default function QAQueuePage() {
  const [approvedList, setApprovedList] = useState<string[]>([]);

  const handleApprove = (id: string) => {
    setApprovedList((prev) => [...prev, id]);
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      <header className="bg-[#1A1A1A] text-[#FBF9F5] px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-xs text-[#8A8A8A] hover:text-white flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Admin Console</span>
          </Link>
          <span className="text-[#8A8A8A]">/</span>
          <span className="font-display font-bold text-base text-white">Discrepancy QA Review Queue</span>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-panel space-y-4">
          <div className="border-b border-[#E8E0D0] pb-3">
            <h1 className="font-bold text-lg text-[#2C2C2C]">Inspector Quality Review Queue</h1>
            <p className="text-xs text-[#6B6B6B]">Review AI-flagged property area variances before publishing to public WebGIS layer.</p>
          </div>

          <div className="space-y-3">
            
            {/* Review Item 1 */}
            <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-[#2D5016]">DRS-BPL-00101</span>
                  <span className="font-bold text-sm text-[#2C2C2C]">Plot 101 — Residential Area Variance (+72 m²)</span>
                </div>
                <p className="text-xs text-[#6B6B6B]">
                  Recorded parcel area: 600 m² &nbsp;|&nbsp; AI footprint area: 672 m² (+12% variance)
                </p>
              </div>

              <div className="flex items-center gap-2">
                {approvedList.includes("DRS-BPL-00101") ? (
                  <span className="bg-[#2D5016]/15 text-[#2D5016] px-3 py-1 rounded font-bold text-xs flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    APPROVED FOR PUBLISHING
                  </span>
                ) : (
                  <>
                    <button
                      onClick={() => handleApprove("DRS-BPL-00101")}
                      className="bg-[#2D5016] hover:bg-[#3A6B1E] text-white px-3 py-1.5 rounded text-xs font-semibold"
                    >
                      Approve Flag
                    </button>
                    <button className="bg-[#EDE8DE] hover:bg-[#E8E0D0] text-[#2C2C2C] px-3 py-1.5 rounded text-xs font-medium">
                      Reject
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Review Item 2 */}
            <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-[#2D5016]">DRS-BPL-00102</span>
                  <span className="font-bold text-sm text-[#2C2C2C]">Plot 102 — Commercial Boundary Variance (+45 m²)</span>
                </div>
                <p className="text-xs text-[#6B6B6B]">
                  Recorded parcel area: 850 m² &nbsp;|&nbsp; AI footprint area: 895 m² (+5.3% variance)
                </p>
              </div>

              <div className="flex items-center gap-2">
                {approvedList.includes("DRS-BPL-00102") ? (
                  <span className="bg-[#2D5016]/15 text-[#2D5016] px-3 py-1 rounded font-bold text-xs flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    APPROVED FOR PUBLISHING
                  </span>
                ) : (
                  <>
                    <button
                      onClick={() => handleApprove("DRS-BPL-00102")}
                      className="bg-[#2D5016] hover:bg-[#3A6B1E] text-white px-3 py-1.5 rounded text-xs font-semibold"
                    >
                      Approve Flag
                    </button>
                    <button className="bg-[#EDE8DE] hover:bg-[#E8E0D0] text-[#2C2C2C] px-3 py-1.5 rounded text-xs font-medium">
                      Reject
                    </button>
                  </>
                )}
              </div>
            </div>

          </div>
        </div>

      </main>

    </div>
  );
}
