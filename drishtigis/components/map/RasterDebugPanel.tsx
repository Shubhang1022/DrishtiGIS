"use client";

import { useState, useEffect } from "react";
import { Terminal, CheckCircle2, XCircle, RefreshCw, ZoomIn } from "lucide-react";
import type { PublishedDatasetItem } from "@/lib/api/datasets";
import { API_BASE } from "@/lib/api/client";

interface RasterDebugPanelProps {
  publishedDatasets: PublishedDatasetItem[];
  selectedDatasetId: string | null;
  onSelectDataset: (id: string) => void;
  onZoomToDataset?: (bounds: [number, number, number, number]) => void;
  isMapLoaded: boolean;
  registeredSources: string[];
  registeredLayers: string[];
}

export function RasterDebugPanel({
  publishedDatasets,
  selectedDatasetId,
  onSelectDataset,
  onZoomToDataset,
  isMapLoaded,
  registeredSources,
  registeredLayers,
}: RasterDebugPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [tileCheckStatus, setTileCheckStatus] = useState<{
    status: number | string;
    contentType: string;
    sizeBytes: number;
    ok: boolean;
  } | null>(null);
  const [checking, setChecking] = useState(false);

  const selectedDataset = publishedDatasets.find((d) => d.dataset_id === selectedDatasetId) || publishedDatasets[0];

  useEffect(() => {
    if (!selectedDataset) return;
    let isMounted = true;
    setChecking(true);

    const checkTile = async () => {
      try {
        const tileUrl = `${API_BASE}/api/v1/datasets/${selectedDataset.dataset_id}/tiles/18/187445/113651.png`;
        const res = await fetch(tileUrl);
        const contentType = res.headers.get("content-type") || "unknown";
        const blob = await res.blob();
        if (isMounted) {
          setTileCheckStatus({
            status: res.status,
            contentType,
            sizeBytes: blob.size,
            ok: res.ok,
          });
        }
      } catch (err: any) {
        if (isMounted) {
          setTileCheckStatus({
            status: err.message || "Network Error",
            contentType: "N/A",
            sizeBytes: 0,
            ok: false,
          });
        }
      } finally {
        if (isMounted) setChecking(false);
      }
    };

    checkTile();
    return () => {
      isMounted = false;
    };
  }, [selectedDataset]);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50 bg-[#2D5016] text-[#FBF9F5] px-3 py-1.5 rounded-lg text-xs font-mono font-bold shadow-2xl flex items-center gap-2 hover:bg-[#3B661E] border border-white/20"
        title="Open WebGIS Raster Diagnostics Debug Panel"
      >
        <Terminal className="w-3.5 h-3.5 text-[#10B981]" />
        <span>Raster Diagnostics</span>
      </button>
    );
  }

  const sourceId = selectedDataset ? `dataset-raster-source-${selectedDataset.dataset_id}` : "";
  const layerId = selectedDataset ? `dataset-raster-layer-${selectedDataset.dataset_id}` : "";
  const isSourceRegistered = registeredSources.includes(sourceId);
  const isLayerRegistered = registeredLayers.includes(layerId);

  return (
    <div className="fixed bottom-4 right-4 z-50 bg-[#1E293B] text-[#F8FAFC] border border-[#334155] rounded-xl p-4 shadow-2xl w-96 font-mono text-xs max-h-[85vh] overflow-y-auto select-none">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#334155] pb-2 mb-3">
        <div className="flex items-center gap-2 font-bold text-[#10B981]">
          <Terminal className="w-4 h-4" />
          <span>Raster Diagnostics (Task 11)</span>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-[#94A3B8] hover:text-white text-sm font-bold px-1.5 py-0.5 rounded hover:bg-[#334155]"
        >
          ✕
        </button>
      </div>

      {/* Dataset Selector */}
      <div className="mb-3">
        <label className="block text-[10px] text-[#94A3B8] uppercase tracking-wider mb-1">Select Published Dataset:</label>
        <select
          value={selectedDataset?.dataset_id || ""}
          onChange={(e) => onSelectDataset(e.target.value)}
          className="w-full bg-[#0F172A] border border-[#475569] rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-[#10B981]"
        >
          {publishedDatasets.map((d) => (
            <option key={d.dataset_id} value={d.dataset_id}>
              {d.name} ({d.dataset_id})
            </option>
          ))}
        </select>
      </div>

      {selectedDataset ? (
        <div className="space-y-2 text-[11px]">
          
          <div className="bg-[#0F172A] p-2.5 rounded-lg border border-[#334155] space-y-1">
            <div className="flex justify-between">
              <span className="text-[#94A3B8]">Dataset ID:</span>
              <span className="text-[#38BDF8] font-bold">{selectedDataset.dataset_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94A3B8]">Status / Published:</span>
              <span className="text-[#10B981] font-bold">READY / PUBLISHED ✓</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94A3B8]">Format / Region:</span>
              <span className="text-white">{selectedDataset.format} ({selectedDataset.region_id})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94A3B8]">Spatial CRS:</span>
              <span className="text-[#F59E0B] font-bold">{selectedDataset.crs}</span>
            </div>
          </div>

          {/* Extent Bounds */}
          <div className="bg-[#0F172A] p-2.5 rounded-lg border border-[#334155]">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[#94A3B8] uppercase text-[10px]">WGS84 Bounds:</span>
              <button
                onClick={() => onZoomToDataset?.(selectedDataset.bounds)}
                className="bg-[#10B981] text-black px-2 py-0.5 rounded text-[10px] font-bold hover:bg-[#34D399] flex items-center gap-1"
              >
                <ZoomIn className="w-3 h-3" />
                <span>Zoom To Extent</span>
              </button>
            </div>
            <p className="text-[10px] text-[#34D399] font-mono break-all">
              [{selectedDataset.bounds.map((n) => n.toFixed(4)).join(", ")}]
            </p>
          </div>

          {/* MapLibre Source & Layer Registration */}
          <div className="bg-[#0F172A] p-2.5 rounded-lg border border-[#334155] space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[#94A3B8]">MapLibre Engine Loaded:</span>
              {isMapLoaded ? (
                <span className="text-[#10B981] flex items-center gap-1 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> YES
                </span>
              ) : (
                <span className="text-[#EF4444] flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" /> NO
                </span>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#94A3B8]">Source Registered:</span>
              {isSourceRegistered ? (
                <span className="text-[#10B981] flex items-center gap-1 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> YES
                </span>
              ) : (
                <span className="text-[#F59E0B] flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" /> PENDING
                </span>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#94A3B8]">Layer Registered:</span>
              {isLayerRegistered ? (
                <span className="text-[#10B981] flex items-center gap-1 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> YES
                </span>
              ) : (
                <span className="text-[#F59E0B] flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" /> PENDING
                </span>
              )}
            </div>
          </div>

          {/* Tile Network Response Test */}
          <div className="bg-[#0F172A] p-2.5 rounded-lg border border-[#334155] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[#94A3B8]">Tile HTTP Request:</span>
              {checking ? (
                <RefreshCw className="w-3 h-3 text-[#38BDF8] animate-spin" />
              ) : tileCheckStatus?.ok ? (
                <span className="text-[#10B981] font-bold">HTTP {tileCheckStatus.status} OK</span>
              ) : (
                <span className="text-[#EF4444] font-bold">HTTP {tileCheckStatus?.status || "FAIL"}</span>
              )}
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-[#94A3B8]">MIME Type:</span>
              <span className="text-white">{tileCheckStatus?.contentType || "N/A"}</span>
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-[#94A3B8]">Tile Size:</span>
              <span className="text-white">{tileCheckStatus?.sizeBytes || 0} bytes</span>
            </div>
          </div>

          {/* TileJSON & Tile Endpoint Links */}
          <div className="text-[10px] text-[#94A3B8] space-y-1 pt-1">
            <div>
              <span className="block text-white font-bold">TileJSON Endpoint:</span>
              <span className="text-[#38BDF8] underline break-all">{selectedDataset.tilejson_url}</span>
            </div>
            <div>
              <span className="block text-white font-bold">XYZ Tile Template:</span>
              <span className="text-[#38BDF8] underline break-all">{selectedDataset.tiles_url}</span>
            </div>
          </div>

        </div>
      ) : (
        <p className="text-[#94A3B8] text-center py-4">No published datasets available.</p>
      )}
    </div>
  );
}
