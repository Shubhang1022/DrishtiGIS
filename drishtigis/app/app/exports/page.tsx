"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Download,
  FileText,
  Map as MapIcon,
  Layers,
  Globe,
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  Package,
  ShieldCheck,
  ArrowRight,
  RefreshCw,
  Info,
} from "lucide-react";

import {
  getExportFormats,
  downloadGISExport,
  downloadEvidencePackage,
  fetchAreaReport,
} from "@/lib/api/exports";
import type { ExportFormatsResponse } from "@/lib/types/export";

export default function ExportCenterPage() {
  const [formatsInfo, setFormatsInfo] = useState<ExportFormatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);
  const [areaReport, setAreaReport] = useState<Record<string, any> | null>(null);

  // Wizard state
  const [selectedCity, setSelectedCity] = useState<string>("Bhopal");
  const [selectedLayers, setSelectedLayers] = useState<string[]>([
    "parcels",
    "buildings",
    "roads",
    "landuse",
    "discrepancies",
    "reviews",
  ]);
  const [selectedFormat, setSelectedFormat] = useState<string>("GeoJSON");
  const [selectedCRS, setSelectedCRS] = useState<string>("EPSG:4326");

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [info, report] = await Promise.all([
          getExportFormats(),
          fetchAreaReport("Bhopal"),
        ]);
        setFormatsInfo(info);
        setAreaReport(report);
      } catch (err) {
        console.error("Failed to load export options:", err);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const toggleLayer = (layerId: string) => {
    setSelectedLayers((prev) =>
      prev.includes(layerId)
        ? prev.filter((l) => l !== layerId)
        : [...prev, layerId]
    );
  };

  const handleDownload = async () => {
    if (selectedLayers.length === 0) {
      alert("Please select at least one GIS layer to export.");
      return;
    }

    setExporting(true);
    try {
      await downloadGISExport({
        city: selectedCity,
        layers: selectedLayers,
        output_format: selectedFormat,
        output_crs: selectedCRS,
      });
    } catch (err: any) {
      alert(`Export generation failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const handleEvidencePackageDownload = async () => {
    setExporting(true);
    try {
      await downloadEvidencePackage(selectedCity);
    } catch (err: any) {
      alert(`Evidence package download failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <Download className="w-8 h-8 text-cyan-400" />
              <h1 className="text-2xl font-bold tracking-tight text-white">
                DrishtiGIS Export & Report Center
              </h1>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Export validated GIS vector layers, cadastral dossiers, surveyor reports, and structured evidence packages.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/app/reports"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition-colors"
            >
              <FileText className="w-4 h-4" />
              Intelligence Dossiers
            </Link>
            <Link
              href="/app/map"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors shadow-lg shadow-cyan-900/20"
            >
              <MapIcon className="w-4 h-4" />
              WebGIS View
            </Link>
          </div>
        </div>

        {/* Synthetic Safety Banner */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <span className="font-semibold text-amber-300 uppercase tracking-wide mr-2">
              DEMONSTRATION PROTOTYPE:
            </span>
            All exported parcel layers retain explicit source attributes (<code className="font-mono text-amber-300">SYNTHETIC_DEMO</code>) and mandatory disclaimers:
            <em className="text-amber-200 block mt-1">"Synthetic prototype data — not an official land record. All identifiers and parcel data are synthetic."</em>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: 7-Step Export Wizard */}
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6 shadow-xl">
              <h2 className="text-base font-bold text-white border-b border-slate-800 pb-3 flex items-center justify-between">
                <span>GIS EXPORT WIZARD</span>
                <span className="text-xs font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
                  STEP-BY-STEP CONFIGURATION
                </span>
              </h2>

              {/* Step 1: Select Region */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                  1. Select Region / Coverage Area
                </label>
                <select
                  value={selectedCity}
                  onChange={(e) => setSelectedCity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="Bhopal">Bhopal, Madhya Pradesh (UAV Coverage — 30 GeoTIFFs, 834 AI Buildings, 35 Parcels)</option>
                  <option value="Lucknow" disabled>Lucknow, Uttar Pradesh (Coverage Onboarding Pending)</option>
                  <option value="New Delhi" disabled>New Delhi (Coverage Onboarding Pending)</option>
                </select>
              </div>

              {/* Step 2: Select Layers */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                  2. Select Exportable GIS Layers
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  {[
                    { id: "parcels", name: "Demonstration Parcels", source: "SYNTHETIC_DEMO", desc: "35 synthetic parcel boundaries" },
                    { id: "buildings", name: "AI Building Footprints", source: "AI_DERIVED_UAVPAL", desc: "834 U-Net ResNet18 extractions" },
                    { id: "roads", name: "Road Transport Network", source: "REFERENCE_GIS", desc: "2,933 OpenStreetMap roads" },
                    { id: "landuse", name: "Observed Land Use", source: "REFERENCE_GIS", desc: "98 land-use pattern polygons" },
                    { id: "discrepancies", name: "Spatial Discrepancies", source: "AI_DERIVED_UAVPAL", desc: "243 geometric boundary observations" },
                    { id: "reviews", name: "Reviewed Geometries", source: "REVIEWED_AI_GEOMETRY", desc: "Surveyor verified & adjusted layers" },
                  ].map((layer) => {
                    const active = selectedLayers.includes(layer.id);
                    return (
                      <div
                        key={layer.id}
                        onClick={() => toggleLayer(layer.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          active
                            ? "bg-cyan-950/50 border-cyan-500/60 text-cyan-100"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-center justify-between font-semibold text-xs mb-1">
                          <span>{layer.name}</span>
                          <input
                            type="checkbox"
                            checked={active}
                            onChange={() => {}}
                            className="accent-cyan-500"
                          />
                        </div>
                        <div className="text-[10px] text-slate-400">{layer.desc}</div>
                        <span className="inline-block text-[9px] font-mono mt-1.5 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {layer.source}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Step 3: Select Format */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                  3. Select Output GIS Format
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { id: "GeoJSON", name: "GeoJSON (.geojson)", desc: "RFC 7946 Standard WebGIS Format" },
                    { id: "GeoPackage", name: "OGC GeoPackage (.gpkg)", desc: "Multi-layer SQLite Production GIS DB" },
                    { id: "ZIP", name: "Multi-Layer ZIP Package", desc: "Layer files + metadata.json" },
                  ].map((fmt) => (
                    <button
                      key={fmt.id}
                      onClick={() => setSelectedFormat(fmt.id)}
                      className={`p-3 text-left rounded-lg border transition-all ${
                        selectedFormat === fmt.id
                          ? "bg-cyan-950/60 border-cyan-400 text-cyan-100"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div className="font-bold text-xs">{fmt.name}</div>
                      <div className="text-[10px] text-slate-400 mt-1">{fmt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 4: Select CRS */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                  4. Select Coordinate Reference System (CRS)
                </label>
                <select
                  value={selectedCRS}
                  onChange={(e) => setSelectedCRS(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                >
                  <option value="EPSG:4326">EPSG:4326 — WGS 84 Geographic Coordinates (Latitude/Longitude)</option>
                  <option value="EPSG:32643">EPSG:32643 — UTM Zone 43N (Metric Projected for Bhopal)</option>
                  <option value="EPSG:3857">EPSG:3857 — Web Mercator (Metric Display Projected)</option>
                </select>
              </div>

              {/* Step 5 & 6 & 7: Metadata Preview & Export Button */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-3">
                <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Export Metadata Preview</span>
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div className="text-[11px] text-slate-300 space-y-1 font-mono">
                  <div>Region: <span className="text-white">Bhopal, Madhya Pradesh</span></div>
                  <div>Output Format: <span className="text-white">{selectedFormat}</span></div>
                  <div>Selected Layers ({selectedLayers.length}): <span className="text-cyan-300">{selectedLayers.join(", ")}</span></div>
                  <div>Target CRS: <span className="text-white">{selectedCRS}</span></div>
                </div>

                <button
                  onClick={handleDownload}
                  disabled={exporting}
                  className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-bold text-xs rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-cyan-900/30"
                >
                  {exporting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Validating & Generating Export File...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      <span>Generate & Download GIS Export File</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Evidence Package & Area Intelligence Card */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Evidence Package Card */}
            <div className="bg-gradient-to-b from-slate-900 to-slate-950 border border-purple-800/50 rounded-xl p-5 space-y-4 shadow-xl">
              <div className="flex items-center gap-2 text-purple-300 font-bold text-sm">
                <Package className="w-5 h-5 text-purple-400" />
                <span>OFFICIAL EVIDENCE PACKAGE</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generate a complete portable ZIP archive containing structured metadata, layer GeoJSON files, parcel dossiers, review audit logs, and README disclaimers.
              </p>

              <div className="bg-slate-950 p-3 rounded-lg text-[10px] font-mono text-purple-200/90 border border-purple-900/40 space-y-1">
                <div>/metadata/dataset.json</div>
                <div>/layers/parcels.geojson</div>
                <div>/layers/buildings.geojson</div>
                <div>/reports/area_intelligence_report.json</div>
                <div>/review/review_history.json</div>
                <div>README.md</div>
              </div>

              <button
                onClick={handleEvidencePackageDownload}
                disabled={exporting}
                className="w-full py-2.5 bg-purple-700 hover:bg-purple-600 text-white font-semibold text-xs rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-purple-900/30"
              >
                <Package className="w-4 h-4" />
                <span>Download Evidence Package (.zip)</span>
              </button>
            </div>

            {/* Dynamic Area Stats Summary */}
            {areaReport && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Globe className="w-4 h-4 text-cyan-400" />
                  <span>Area Dataset Intelligence</span>
                </h3>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between border-b border-slate-800 pb-1">
                    <span className="text-slate-400">UAV Orthomosaic:</span>
                    <span className="font-mono text-slate-200">{areaReport.dataset_overview?.imagery_tiles_count} GeoTIFF Tiles</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-1">
                    <span className="text-slate-400">AI Buildings:</span>
                    <span className="font-mono text-cyan-300">{areaReport.ai_building_extraction_metrics?.total_buildings_detected} Footprints</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-1">
                    <span className="text-slate-400">Demo Parcels:</span>
                    <span className="font-mono text-amber-300">{areaReport.parcel_cadastral_metrics?.total_demonstration_parcels} Synthetic Parcels</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-1">
                    <span className="text-slate-400">OSM Roads:</span>
                    <span className="font-mono text-slate-200">{areaReport.road_network_metrics?.total_road_segments} Segments ({areaReport.road_network_metrics?.total_road_length_km} km)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">OSM Land Use:</span>
                    <span className="font-mono text-slate-200">{areaReport.observed_landuse_metrics?.total_polygons} Polygons</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
