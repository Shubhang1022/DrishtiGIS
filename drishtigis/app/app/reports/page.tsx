"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, FileText, Download, Printer, CheckSquare, Info, ShieldCheck, Sparkles, AlertTriangle, Globe } from "lucide-react";
import { fetchParcelReport, fetchAreaReport, downloadEvidencePackage } from "@/lib/api/exports";

export default function ReportsPage() {
  const [selectedPropertyId, setSelectedPropertyId] = useState("DRS-BPL-DEMO-001");
  const [includeAI, setIncludeAI] = useState(true);
  const [includeDiscrepancies, setIncludeDiscrepancies] = useState(true);
  const [reportData, setReportData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);

  const loadReport = async (pid: string) => {
    setLoading(true);
    try {
      const data = await fetchParcelReport(pid);
      setReportData(data);
    } catch (err) {
      console.error("Failed to load parcel report:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport(selectedPropertyId);
  }, [selectedPropertyId]);

  const handleExportPDF = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      {/* Top Header */}
      <header className="bg-[#FBF9F5] border-b border-[#E8E0D0] px-4 lg:px-8 py-3 flex items-center justify-between print:hidden">
        <div className="flex items-center gap-3">
          <Link href="/app/map" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]">
            <ArrowLeft className="w-4 h-4" />
            <span>Return to WebGIS Map</span>
          </Link>
          <span className="text-[#8A8A8A]">/</span>
          <div className="flex items-center gap-1.5 font-display font-bold text-sm text-[#2C2C2C]">
            <FileText className="w-4 h-4 text-[#2D5016]" />
            <span>Cadastral Intelligence Dossier Generator</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/exports"
            className="inline-flex items-center gap-2 bg-slate-800 text-white hover:bg-slate-700 px-3.5 py-1.5 rounded-lg text-xs font-semibold"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Center</span>
          </Link>
          <button 
            onClick={handleExportPDF}
            className="inline-flex items-center gap-2 bg-[#2D5016] text-[#FBF9F5] hover:bg-[#3A6B1E] px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-xs"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print / Save PDF</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 lg:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Report Options Panel */}
        <div className="lg:col-span-4 space-y-6 print:hidden">
          
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-5 shadow-panel space-y-4">
            <h2 className="font-bold text-sm text-[#2C2C2C] border-b border-[#E8E0D0] pb-2">
              Report Parameters
            </h2>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Target Property / Plot ID
              </label>
              <select
                value={selectedPropertyId}
                onChange={(e) => setSelectedPropertyId(e.target.value)}
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] font-mono focus:outline-none"
              >
                <option value="DRS-BPL-DEMO-001">DRS-BPL-DEMO-001 (Residential Plot 1001)</option>
                <option value="DRS-BPL-DEMO-002">DRS-BPL-DEMO-002 (Residential Plot 1002)</option>
                <option value="DRS-BPL-DEMO-003">DRS-BPL-DEMO-003 (Residential Plot 1003)</option>
                <option value="DRS-BPL-DEMO-005">DRS-BPL-DEMO-005 (Commercial Plot 1005)</option>
              </select>
            </div>

            <div className="space-y-2 pt-2 border-t border-[#E8E0D0]">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Dossier Sections
              </label>

              <label className="flex items-center gap-2 text-xs text-[#2C2C2C] cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeAI}
                  onChange={(e) => setIncludeAI(e.target.checked)}
                  className="accent-[#2D5016] rounded"
                />
                <span>Include AI Building Extraction Metrics</span>
              </label>

              <label className="flex items-center gap-2 text-xs text-[#2C2C2C] cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeDiscrepancies}
                  onChange={(e) => setIncludeDiscrepancies(e.target.checked)}
                  className="accent-[#2D5016] rounded"
                />
                <span>Include Discrepancy Audit Table</span>
              </label>
            </div>

            <div className="bg-[#EDE8DE] p-3 rounded-lg text-[11px] text-[#6B6B6B] space-y-1">
              <div className="font-bold text-[#2C2C2C] flex items-center gap-1">
                <Info className="w-3.5 h-3.5 text-[#C4922A]" />
                <span>Synthetic Prototype Data</span>
              </div>
              <p>Generated report contains synthetic prototype disclaimers. Official certification requires government surveyor field verification.</p>
            </div>
          </div>
        </div>

        {/* Right Column: Dossier Document Preview */}
        <div className="lg:col-span-8">
          <div className="bg-white border border-[#E8E0D0] rounded-2xl p-8 shadow-xl space-y-6 print:border-none print:shadow-none">
            
            {/* Dossier Document Header */}
            <div className="border-b-2 border-[#2D5016] pb-4 flex justify-between items-start">
              <div>
                <span className="text-[10px] uppercase tracking-widest font-mono text-[#8A8A8A] font-bold">
                  DrishtiGIS Cadastral Intelligence Dossier
                </span>
                <h1 className="text-2xl font-display font-bold text-[#2D5016] mt-1">
                  PARCEL INTELLIGENCE REPORT
                </h1>
                <p className="text-xs text-[#6B6B6B] font-mono mt-0.5">
                  Property ID: {selectedPropertyId} | Region: Bhopal, Madhya Pradesh
                </p>
              </div>

              <div className="text-right font-mono text-[10px] text-[#8A8A8A]">
                <div>Generated: {new Date().toISOString().slice(0, 10)}</div>
                <div>Status: SYNTHETIC_DEMO</div>
              </div>
            </div>

            {/* Disclaimer Box */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-[11px] text-amber-900 leading-relaxed">
              <div className="font-bold flex items-center gap-1.5 mb-0.5 text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>DEMO PROPERTY — NOT OFFICIAL LAND RECORD</span>
              </div>
              Synthetic prototype data — not an official land record. All identifiers, owner names, and property data are synthetic. Spatial building extractions represent AI geometric observations.
            </div>

            {/* Report Contents */}
            {loading ? (
              <div className="p-12 text-center text-xs text-[#8A8A8A]">
                Generating dynamic parcel intelligence dossier...
              </div>
            ) : reportData ? (
              <div className="space-y-6 text-xs text-[#2C2C2C]">
                
                {/* Section 1: Property Details */}
                <section className="bg-[#F7F3EC] p-4 rounded-xl space-y-2 border border-[#E8E0D0]">
                  <h3 className="font-bold text-xs uppercase text-[#2D5016] tracking-wider border-b border-[#E8E0D0] pb-1">
                    1. PROPERTY IDENTIFICATION & CADASTRAL METRICS
                  </h3>
                  <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                    <div>Parcel ID: <span className="font-bold">{reportData.parcel?.parcel_id}</span></div>
                    <div>Plot Number: <span className="font-bold">{reportData.parcel?.plot_number ?? "N/A"}</span></div>
                    <div>Synthetic Owner: <span className="font-bold">{reportData.parcel?.owner_name_synthetic ?? "N/A"}</span></div>
                    <div>Parcel Area: <span className="font-bold">{reportData.parcel?.area_m2} m²</span></div>
                    <div>Land Use: <span className="font-bold">{reportData.parcel?.land_use}</span></div>
                    <div>Record Status: <span className="font-bold text-amber-800">SYNTHETIC_DEMO</span></div>
                  </div>
                </section>

                {/* Section 2: AI Building Analysis */}
                {includeAI && reportData.ai_building_analysis && (
                  <section className="bg-[#F0FAFA] p-4 rounded-xl space-y-2 border border-teal-200">
                    <h3 className="font-bold text-xs uppercase text-teal-900 tracking-wider border-b border-teal-200 pb-1 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-teal-600" />
                      <span>2. AI BUILDING FEATURE EXTRACTION (UAVPal U-Net)</span>
                    </h3>
                    <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                      <div>Buildings Detected: <span className="font-bold text-teal-900">{reportData.ai_building_analysis.building_count}</span></div>
                      <div>Total Detected Area: <span className="font-bold text-teal-900">{reportData.ai_building_analysis.total_building_area_m2} m²</span></div>
                      <div>Coverage Ratio: <span className="font-bold text-teal-900">{(reportData.ai_building_analysis.coverage_ratio * 100).toFixed(1)}%</span></div>
                      <div>Avg Confidence: <span className="font-bold text-teal-900">{(reportData.ai_building_analysis.average_confidence * 100).toFixed(0)}%</span></div>
                    </div>
                  </section>
                )}

                {/* Section 3: Discrepancy Audit */}
                {includeDiscrepancies && reportData.discrepancies && (
                  <section className="bg-amber-50/60 p-4 rounded-xl space-y-2 border border-amber-200">
                    <h3 className="font-bold text-xs uppercase text-amber-900 tracking-wider border-b border-amber-200 pb-1">
                      3. GEOMETRIC DISCREPANCY AUDIT
                    </h3>
                    {reportData.discrepancies.length === 0 ? (
                      <p className="text-slate-600 text-[11px]">No geometric discrepancies detected for this parcel.</p>
                    ) : (
                      <div className="space-y-2 pt-1">
                        {reportData.discrepancies.map((d: any) => (
                          <div key={d.id} className="bg-white p-2.5 rounded border border-amber-200 text-[11px] space-y-1">
                            <div className="flex justify-between font-bold text-amber-900">
                              <span>{d.type}</span>
                              <span className="text-amber-700">{d.severity}</span>
                            </div>
                            <p className="text-slate-700">{d.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {/* Sign-off footer */}
                <div className="pt-6 border-t border-[#E8E0D0] text-[10px] text-[#8A8A8A] flex justify-between items-center">
                  <div>DrishtiGIS Geospatial AI Platform | SIH26012</div>
                  <div>Page 1 of 1</div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
