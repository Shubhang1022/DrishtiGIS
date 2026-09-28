"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  UploadCloud,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  X,
  RefreshCw,
  FileCheck,
  Building,
  MapPin
} from "lucide-react";
import { uploadDataset, DatasetUploadResponse } from "@/lib/api/datasets";

const MAX_UPLOAD_SIZE_MB = 100;
const MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".tif", ".tiff", ".geojson", ".gpkg", ".zip"];

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export default function DatasetUploadPage() {
  const [datasetName, setDatasetName] = useState("");
  const [stateName, setStateName] = useState("Madhya Pradesh");
  const [cityName, setCityName] = useState("Bhopal");
  const [regionId, setRegionId] = useState("bhopal_mp");
  const [datasetType, setDatasetType] = useState("uav_raster");

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<DatasetUploadResponse | null>(null);

  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    setUploadError(null);

    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError(
        `Invalid file format '${ext}'. Allowed formats: ${ALLOWED_EXTENSIONS.join(", ")}`
      );
      setSelectedFile(null);
      return;
    }

    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setValidationError(
        `File size (${formatFileSize(file.size)}) exceeds maximum limit of ${MAX_UPLOAD_SIZE_MB} MB.`
      );
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    if (!datasetName) {
      const nameWithoutExt = file.name.substring(0, file.name.lastIndexOf(".")) || file.name;
      setDatasetName(nameWithoutExt.replace(/[^a-zA-Z0-9_-]/g, "_"));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  }, [datasetName]);

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setValidationError(null);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setValidationError("Please select or drop a valid geospatial dataset file to upload.");
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await uploadDataset(selectedFile, datasetName, regionId, stateName, cityName, datasetType);
      setUploadResult(res);
      setIsUploading(false);
    } catch (err: any) {
      setIsUploading(false);
      setUploadError(err.message || "Upload failed. Please check network connection and admin authorization.");
    }
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
          <span className="font-display font-bold text-base text-white">Upload Geospatial Dataset</span>
        </div>
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto p-4 lg:p-8">
        
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-panel space-y-6">
          <div className="border-b border-[#E8E0D0] pb-3 flex items-center justify-between">
            <div>
              <h1 className="font-bold text-lg text-[#2C2C2C]">Ingest New Geospatial Dataset</h1>
              <p className="text-xs text-[#6B6B6B]">Upload GeoTIFF orthomosaics, GeoJSON vectors, GPKG, or zipped GIS archives for automated pipeline processing.</p>
            </div>
            <div className="bg-[#2D5016]/10 text-[#2D5016] text-[11px] font-mono px-2.5 py-1 rounded-full font-semibold">
              Max {MAX_UPLOAD_SIZE_MB} MB
            </div>
          </div>

          {uploadResult ? (
            <div className="bg-[#2D5016]/10 border border-[#2D5016] rounded-xl p-6 text-center space-y-4">
              <CheckCircle2 className="w-12 h-12 text-[#2D5016] mx-auto" />
              <div>
                <h2 className="font-bold text-base text-[#2D5016]">Upload Successful — Dataset Registered</h2>
                <p className="text-xs text-[#6B6B6B] mt-1 max-w-md mx-auto">
                  Dataset <span className="font-mono font-bold text-[#2C2C2C]">{uploadResult.dataset_id}</span> has been received and registered. Asynchronous background geospatial processing & tiling has been queued. <strong>Processing has not yet completed.</strong>
                </p>
              </div>

              <div className="bg-white/80 border border-[#2D5016]/20 rounded-lg p-3 text-left max-w-md mx-auto text-xs space-y-1 font-mono text-[#2C2C2C]">
                <div><span className="text-[#6B6B6B]">Dataset Name:</span> {datasetName || uploadResult.filename}</div>
                <div><span className="text-[#6B6B6B]">Filename:</span> {uploadResult.filename}</div>
                <div><span className="text-[#6B6B6B]">Size:</span> {formatFileSize(uploadResult.size_bytes)}</div>
                <div><span className="text-[#6B6B6B]">Target Region:</span> {uploadResult.region_id}</div>
              </div>

              <div className="pt-2 flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setUploadResult(null);
                    setSelectedFile(null);
                    setDatasetName("");
                  }}
                  className="bg-white border border-[#E8E0D0] text-[#2C2C2C] px-4 py-2 rounded-lg text-xs font-semibold hover:bg-[#F7F3EC]"
                >
                  Upload Another Dataset
                </button>
                <Link href="/admin/datasets" className="bg-[#2D5016] text-white px-4 py-2 rounded-lg text-xs font-semibold hover:bg-[#3A6B1E]">
                  View Dataset Inventory →
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              
              <div className="space-y-1">
                <label className="text-xs font-semibold text-[#2C2C2C] block">Dataset Name</label>
                <input
                  type="text"
                  required
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  placeholder="e.g. Bhopal_Sector3_Orthomosaic_2024"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#2C2C2C] block">State</label>
                  <input
                    type="text"
                    value={stateName}
                    onChange={(e) => setStateName(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#2C2C2C] block">Target City</label>
                  <input
                    type="text"
                    value={cityName}
                    onChange={(e) => setCityName(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#2C2C2C] block">Region ID</label>
                  <input
                    type="text"
                    value={regionId}
                    onChange={(e) => setRegionId(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs font-mono text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-[#2C2C2C] block">Dataset Format Type</label>
                <select
                  value={datasetType}
                  onChange={(e) => setDatasetType(e.target.value)}
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                >
                  <option value="uav_raster">UAV Raster Orthomosaic (.tif, .tiff, COG)</option>
                  <option value="cadastral_vector">Cadastral Vector Polygons (.geojson, .gpkg)</option>
                  <option value="ai_footprints">AI Building Footprints (.geojson)</option>
                  <option value="gis_archive">GIS Archive Bundle (.zip)</option>
                </select>
              </div>

              {/* Drag and Drop Zone */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".tif,.tiff,.geojson,.gpkg,.zip"
                onChange={handleFileChange}
                className="hidden"
              />

              {!selectedFile ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center space-y-2 cursor-pointer transition-colors ${
                    isDragActive
                      ? "border-[#2D5016] bg-[#2D5016]/10"
                      : "border-[#E8E0D0] hover:border-[#2D5016] bg-[#F7F3EC]"
                  }`}
                >
                  <UploadCloud className="w-10 h-10 text-[#2D5016] mx-auto" />
                  <div className="font-bold text-xs text-[#2C2C2C]">
                    Drag and drop GeoTIFF, GeoJSON, or ZIP files here
                  </div>
                  <div className="text-[11px] text-[#6B6B6B]">
                    or <span className="text-[#2D5016] font-semibold underline">browse files</span> on your device
                  </div>
                  <div className="text-[10px] text-[#8A8A8A] pt-1">
                    Maximum allowed file size: <span className="font-bold">{MAX_UPLOAD_SIZE_MB} MB</span> (Configured limit). Supported formats: .tif, .tiff, .geojson, .gpkg, .zip
                  </div>
                </div>
              ) : (
                <div className="bg-[#F7F3EC] border border-[#2D5016]/40 rounded-xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="bg-[#2D5016] text-white p-2 rounded-lg">
                      <FileCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-xs text-[#2C2C2C]">{selectedFile.name}</div>
                      <div className="text-[11px] text-[#6B6B6B]">
                        Size: {formatFileSize(selectedFile.size)} • Format: {selectedFile.name.split(".").pop()?.toUpperCase()}
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    disabled={isUploading}
                    className="p-1 text-[#8A8A8A] hover:text-[#B91C1C] rounded transition-colors"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Validation or Upload Error Banner */}
              {(validationError || uploadError) && (
                <div className="bg-[#B91C1C]/10 border border-[#B91C1C] text-[#B91C1C] rounded-xl p-3.5 text-xs flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{validationError || uploadError}</span>
                  </div>
                  {uploadError && (
                    <button
                      type="button"
                      onClick={handleUploadSubmit}
                      className="shrink-0 text-[11px] font-bold underline flex items-center gap-1 hover:text-[#991B1B]"
                    >
                      <RefreshCw className="w-3 h-3" /> Retry
                    </button>
                  )}
                </div>
              )}

              <button
                type="submit"
                disabled={isUploading || !selectedFile}
                className="w-full bg-[#2D5016] hover:bg-[#3A6B1E] disabled:bg-[#8A8A8A] text-white font-semibold text-xs py-3 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Uploading & Validating Geospatial CRS…</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    <span>Upload & Start Pipeline</span>
                  </>
                )}
              </button>

            </form>
          )}

        </div>

      </main>

    </div>
  );
}
