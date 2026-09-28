"use client";

/**
 * DrishtiGIS — Layer Visibility Control
 * =======================================
 * Allows toggling individual map layer visibility.
 * Provides a single consolidated "Buildings" layer entry with source selector.
 */

import { Layers, Compass, Building2, User, ZoomIn, Globe } from "lucide-react";
import type { LayerVisibility, BuildingSourceType } from "@/lib/gis/coverage";
import type { PublishedDatasetItem } from "@/lib/api/datasets";

interface LayerControlProps {
  visibility: LayerVisibility;
  onChange: (layer: keyof LayerVisibility, visible: any) => void;
  onBasemapChange?: (basemap: "standard" | "satellite") => void;
  hasSidebar?: boolean;
  publishedDatasets?: PublishedDatasetItem[];
  activeDatasetIds?: string[];
  onToggleDataset?: (id: string, visible: boolean) => void;
  onZoomToDataset?: (bounds: [number, number, number, number]) => void;
}

export function LayerControl({
  visibility,
  onChange,
  onBasemapChange,
  hasSidebar,
  publishedDatasets = [],
  activeDatasetIds = [],
  onToggleDataset,
  onZoomToDataset,
}: LayerControlProps) {
  const handleBasemap = (type: "standard" | "satellite") => {
    if (onBasemapChange) {
      onBasemapChange(type);
    } else {
      onChange("basemap", type);
    }
  };

  const handleBuildingSourceChange = (source: BuildingSourceType) => {
    onChange("buildingSource", source);
    // Sync legacy properties
    if (source === "ai") {
      onChange("aiFeatures", visibility.buildings);
      onChange("osmBuildings", false);
    } else {
      onChange("aiFeatures", false);
      onChange("osmBuildings", visibility.buildings);
    }
  };

  const handleBuildingsToggle = (checked: boolean) => {
    onChange("buildings", checked);
    if (visibility.buildingSource === "ai") {
      onChange("aiFeatures", checked);
      onChange("osmBuildings", false);
    } else {
      onChange("aiFeatures", false);
      onChange("osmBuildings", checked);
    }
  };

  return (
    <div
      className={`absolute top-4 ${hasSidebar ? "right-4 sm:right-[395px] lg:right-[435px]" : "right-4"} bg-[#FBF9F5]/95 backdrop-blur-md border border-[#E8E0D0] rounded-xl p-3 z-20 shadow-panel w-72 text-xs font-sans select-none transition-all duration-300`}
      role="region"
      aria-label="Map layer controls"
    >
      <fieldset className="border-0 m-0 p-0">
        
        {/* BASEMAP SELECTION */}
        <div className="mb-3 pb-2.5 border-b border-[#E8E0D0]">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5 font-bold text-[#2D5016]">
              <Compass className="w-3.5 h-3.5 text-[#2D5016]" />
              <span className="uppercase text-[10px] tracking-wider">Map Basemap</span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] uppercase font-semibold">
              {visibility.basemap === "satellite" ? "Satellite" : "Standard"}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1 bg-[#EDE8DE] p-1 rounded-lg">
            <button
              type="button"
              onClick={() => handleBasemap("standard")}
              className={`py-1 px-2 rounded-md font-medium text-[11px] text-center transition-all ${
                visibility.basemap === "standard"
                  ? "bg-[#FBF9F5] text-[#2D5016] shadow-xs font-semibold"
                  : "text-[#69635C] hover:text-[#2C2C2C]"
              }`}
            >
              Standard Map
            </button>
            <button
              type="button"
              onClick={() => handleBasemap("satellite")}
              className={`py-1 px-2 rounded-md font-medium text-[11px] text-center transition-all ${
                visibility.basemap === "satellite"
                  ? "bg-[#2D5016] text-[#FBF9F5] shadow-xs font-semibold"
                  : "text-[#69635C] hover:text-[#2C2C2C]"
              }`}
            >
              Satellite
            </button>
          </div>
        </div>

        <legend className="flex items-center justify-between w-full border-b border-[#E8E0D0] pb-2 mb-2">
          <div className="flex items-center gap-1.5 font-bold text-[#2D5016]">
            <Layers className="w-3.5 h-3.5 text-[#2D5016]" />
            <span className="uppercase text-[10px] tracking-wider">Map Layers</span>
          </div>
          <span className="text-[9px] font-mono text-[#8A8A8A] uppercase">Active Layers</span>
        </legend>

        <div className="space-y-1.5">
          
          {/* 1. UAV Imagery */}
          <label className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer transition-colors ${
            visibility.uavImagery ? "bg-[#F7F3EC] text-[#2C2C2C]" : "opacity-60 hover:opacity-100 text-[#8A8A8A]"
          }`}>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={visibility.uavImagery}
                onChange={(e) => onChange("uavImagery", e.target.checked)}
                className="accent-[#2D5016] w-3.5 h-3.5 cursor-pointer rounded"
              />
              <span className="w-2 h-2 rounded-full bg-[#7D9154] inline-block" />
              <span className="font-medium text-xs">UAV High-Res Imagery</span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded">z17+</span>
          </label>

          {/* Published Dynamic Aerial Datasets (Task 9) */}
          {publishedDatasets.length > 0 && (
            <div className="pt-2 border-t border-[#E8E0D0] mt-2 space-y-1">
              <div className="flex items-center justify-between text-[10px] font-bold text-[#2D5016] uppercase tracking-wider mb-1">
                <span className="flex items-center gap-1">
                  <Globe className="w-3 h-3 text-[#10B981]" />
                  <span>Published Datasets ({publishedDatasets.length})</span>
                </span>
              </div>
              <div className="space-y-1 max-h-36 overflow-y-auto">
                {publishedDatasets.map((ds) => {
                  const isActive = activeDatasetIds.includes(ds.dataset_id);
                  return (
                    <div
                      key={ds.dataset_id}
                      className={`flex items-center justify-between p-1.5 rounded-lg border transition-all ${
                        isActive ? "bg-[#F7F3EC] border-[#10B981]/40 text-[#2C2C2C]" : "bg-[#FBF9F5] border-[#E8E0D0] opacity-70"
                      }`}
                    >
                      <label className="flex items-center gap-2 cursor-pointer flex-1 truncate mr-1">
                        <input
                          type="checkbox"
                          checked={isActive}
                          onChange={(e) => onToggleDataset?.(ds.dataset_id, e.target.checked)}
                          className="accent-[#10B981] w-3.5 h-3.5 cursor-pointer rounded"
                        />
                        <span className="w-2 h-2 rounded-full bg-[#10B981] shrink-0" />
                        <span className="font-semibold text-xs truncate" title={ds.name}>{ds.name}</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => onZoomToDataset?.(ds.bounds)}
                        className="p-1 text-[#2D5016] hover:bg-[#EDE8DE] rounded transition-colors shrink-0"
                        title="Zoom map to dataset extent bounds"
                      >
                        <ZoomIn className="w-3.5 h-3.5 text-[#10B981]" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 2. Demo Cadastral Parcels */}
          <label className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer transition-colors ${
            visibility.parcels ? "bg-[#F7F3EC] text-[#2C2C2C]" : "opacity-60 hover:opacity-100 text-[#8A8A8A]"
          }`}>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={visibility.parcels}
                onChange={(e) => onChange("parcels", e.target.checked)}
                className="accent-[#2D5016] w-3.5 h-3.5 cursor-pointer rounded"
              />
              <span className="w-2 h-2 rounded-full bg-[#D4A017] inline-block" />
              <span className="font-medium text-xs">Demo Property Records</span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded">z13+</span>
          </label>

          {/* 3. CONSOLIDATED BUILDINGS LAYER */}
          <div className={`p-2 rounded-xl border transition-all ${
            visibility.buildings
              ? "bg-[#F7F3EC] border-[#2D5016]/30 text-[#2C2C2C] shadow-xs"
              : "bg-[#FBF9F5] border-[#E8E0D0] opacity-70"
          }`}>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={visibility.buildings}
                  onChange={(e) => handleBuildingsToggle(e.target.checked)}
                  className="accent-[#2D5016] w-3.5 h-3.5 cursor-pointer rounded"
                />
                <span className={`w-2.5 h-2.5 rounded-sm inline-block ${
                  visibility.buildingSource === "ai" ? "bg-[#10B981] shadow-xs" : "bg-[#94A3B8]"
                }`} />
                <span className="font-bold text-xs text-[#2C2C2C] flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-[#2D5016]" />
                  <span>Buildings</span>
                </span>
              </label>
              
              <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded">z15+</span>
            </div>

            {/* Source selector inside Buildings */}
            {visibility.buildings && (
              <div className="mt-2 pt-2 border-t border-[#E8E0D0] space-y-1">
                <div className="text-[9px] font-bold text-[#6B6B6B] uppercase tracking-wider">Footprint Source:</div>
                <div className="grid grid-cols-2 gap-1 text-[10px]">
                  <button
                    type="button"
                    onClick={() => handleBuildingSourceChange("ai")}
                    className={`py-1 px-2 rounded-md font-semibold text-center flex items-center justify-center gap-1 transition-all ${
                      visibility.buildingSource === "ai"
                        ? "bg-[#10B981] text-white shadow-xs"
                        : "bg-[#EDE8DE] text-[#69635C] hover:text-[#2C2C2C]"
                    }`}
                  >
                    <span>AI (0.02m UAV)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleBuildingSourceChange("osm")}
                    className={`py-1 px-2 rounded-md font-semibold text-center flex items-center justify-center gap-1 transition-all ${
                      visibility.buildingSource === "osm"
                        ? "bg-[#64748B] text-white shadow-xs"
                        : "bg-[#EDE8DE] text-[#69635C] hover:text-[#2C2C2C]"
                    }`}
                  >
                    <span>OSM Reference</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 4. User Registered Properties */}
          <label className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer transition-colors ${
            visibility.userProperties ? "bg-[#F7F3EC] text-[#2C2C2C]" : "opacity-60 hover:opacity-100 text-[#8A8A8A]"
          }`}>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={visibility.userProperties}
                onChange={(e) => onChange("userProperties", e.target.checked)}
                className="accent-[#7C3AED] w-3.5 h-3.5 cursor-pointer rounded"
              />
              <span className="w-2 h-2 rounded-full bg-[#7C3AED] inline-block" />
              <span className="font-medium text-xs flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-[#7C3AED]" />
                <span>User Properties</span>
              </span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded font-semibold">User</span>
          </label>

          {/* 5. OSM Roads */}
          <label className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer transition-colors ${
            visibility.osmRoads ? "bg-[#F7F3EC] text-[#2C2C2C]" : "opacity-60 hover:opacity-100 text-[#8A8A8A]"
          }`}>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={visibility.osmRoads}
                onChange={(e) => onChange("osmRoads", e.target.checked)}
                className="accent-[#2D5016] w-3.5 h-3.5 cursor-pointer rounded"
              />
              <span className="w-2 h-2 rounded-full bg-[#C4922A] inline-block" />
              <span className="font-medium text-xs">OSM Roads</span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded">z13+</span>
          </label>

          {/* 6. OSM Waterways */}
          <label className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer transition-colors ${
            visibility.osmWaterways ? "bg-[#F7F3EC] text-[#2C2C2C]" : "opacity-60 hover:opacity-100 text-[#8A8A8A]"
          }`}>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={visibility.osmWaterways}
                onChange={(e) => onChange("osmWaterways", e.target.checked)}
                className="accent-[#2D5016] w-3.5 h-3.5 cursor-pointer rounded"
              />
              <span className="w-2 h-2 rounded-full bg-[#3B82F6] inline-block" />
              <span className="font-medium text-xs">OSM Waterways</span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded">z13+</span>
          </label>

          {/* 7. OSM Land Use */}
          <label className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer transition-colors ${
            visibility.osmLanduse ? "bg-[#F7F3EC] text-[#2C2C2C]" : "opacity-60 hover:opacity-100 text-[#8A8A8A]"
          }`}>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={visibility.osmLanduse}
                onChange={(e) => onChange("osmLanduse", e.target.checked)}
                className="accent-[#2D5016] w-3.5 h-3.5 cursor-pointer rounded"
              />
              <span className="w-2 h-2 rounded-full bg-[#6B7C45] inline-block" />
              <span className="font-medium text-xs">OSM Land Use</span>
            </div>
            <span className="text-[9px] font-mono text-[#8A8A8A] bg-[#EDE8DE] px-1 rounded">z14+</span>
          </label>

        </div>

        {/* Legend Classification Footer */}
        <div className="mt-3 pt-2 border-t border-[#E8E0D0] text-[10px] text-[#6B6B6B] flex items-center justify-between">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-[#10B981]" /> AI Footprint
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-[#64748B]" /> OSM Reference
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-[#7C3AED]" /> User Pin
          </span>
        </div>
      </fieldset>
    </div>
  );
}
