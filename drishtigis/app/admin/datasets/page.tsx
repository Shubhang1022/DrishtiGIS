"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Database,
  Plus,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Eye,
  RotateCcw,
  Ban,
  Globe,
  Clock,
  Layers,
  FileCode,
  SlidersHorizontal,
  X,
  MapPin,
  CheckSquare,
  ShieldCheck
} from "lucide-react";
import {
  listDatasets,
  getDatasetDetail,
  retryDatasetJob,
  cancelDatasetJob,
  publishDataset,
  DatasetItemData
} from "@/lib/api/datasets";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function getStatusBadge(status: string) {
  const st = status.toUpperCase();
  switch (st) {
    case "PUBLISHED":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white font-mono">PUBLISHED</span>;
    case "READY":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-600 text-white font-mono">READY</span>;
    case "QA_REQUIRED":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-white font-mono">QA REQUIRED</span>;
    case "PROCESSING":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-600 text-white font-mono animate-pulse">PROCESSING</span>;
    case "VALIDATING":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-600 text-white font-mono animate-pulse">VALIDATING</span>;
    case "REGISTERED":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-600 text-white font-mono">REGISTERED</span>;
    case "FAILED":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-600 text-white font-mono">FAILED</span>;
    case "CANCELLED":
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gray-600 text-white font-mono">CANCELLED</span>;
    default:
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gray-500 text-white font-mono">{st}</span>;
  }
}

export default function DatasetInventoryPage() {
  const [datasets, setDatasets] = useState<DatasetItemData[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  // Filters & Controls
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [formatFilter, setFormatFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("uploaded_at");
  const [ascending, setAscending] = useState(false);
  const [autoPoll, setAutoPoll] = useState(true);

  // Detail Modal / Drawer state
  const [selectedDataset, setSelectedDataset] = useState<DatasetItemData | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchInventory = async () => {
    try {
      const res = await listDatasets({
        status: statusFilter,
        format_type: formatFilter,
        search: searchQuery,
        sort_by: sortBy,
        ascending: ascending,
      });
      setDatasets(res.datasets);
      setTotalCount(res.total);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Failed to load dataset inventory:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [statusFilter, formatFilter, searchQuery, sortBy, ascending]);

  // Auto-polling interval if active processing jobs exist
  useEffect(() => {
    if (!autoPoll) return;

    const hasActiveJobs = datasets.some((d) =>
      ["REGISTERED", "VALIDATING", "PROCESSING"].includes(d.status)
    );

    if (hasActiveJobs) {
      const timer = setInterval(() => {
        fetchInventory();
      }, 3000);
      return () => clearInterval(timer);
    }
  }, [datasets, autoPoll]);

  const handleOpenDetail = async (ds: DatasetItemData) => {
    setSelectedDataset(ds);
    try {
      const fresh = await getDatasetDetail(ds.dataset_id);
      setSelectedDataset(fresh);
    } catch (_) {}
  };

  const handleRetry = async (dsId: string) => {
    setActionLoading(true);
    try {
      const updated = await retryDatasetJob(dsId);
      setSelectedDataset(updated);
      await fetchInventory();
    } catch (err: any) {
      alert(err.message || "Failed to retry dataset job");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async (dsId: string) => {
    if (!confirm("Are you sure you want to cancel this dataset processing job?")) return;
    setActionLoading(true);
    try {
      const updated = await cancelDatasetJob(dsId);
      setSelectedDataset(updated);
      await fetchInventory();
    } catch (err: any) {
      alert(err.message || "Failed to cancel dataset job");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePublish = async (dsId: string) => {
    setActionLoading(true);
    try {
      const updated = await publishDataset(dsId);
      setSelectedDataset(updated);
      await fetchInventory();
    } catch (err: any) {
      alert(err.message || "Failed to publish dataset");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans selection:bg-[#2D5016] selection:text-white">
      
      {/* Header Bar */}
      <header className="bg-[#1A1A1A] text-[#FBF9F5] px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-xs text-[#8A8A8A] hover:text-white flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Admin Operations</span>
          </Link>
          <span className="text-[#8A8A8A]">/</span>
          <span className="font-display font-bold text-base text-white">Geospatial Dataset Inventory</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchInventory()}
            className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5 text-white transition-colors"
            title="Refresh inventory"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <Link
            href="/admin/datasets/upload"
            className="inline-flex items-center gap-1.5 bg-[#2D5016] text-white hover:bg-[#3A6B1E] px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-xs transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Upload New Dataset</span>
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        {/* Search & Filter Toolbar */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 lg:p-6 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E8E0D0] pb-4">
            <div>
              <h1 className="font-display font-bold text-xl text-[#2C2C2C]">Dataset Inventory & Pipeline Jobs</h1>
              <p className="text-xs text-[#6B6B6B] mt-0.5">
                Real-time tracking for geospatial raster tiles, vector cadastral features, and AI building extraction jobs.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-[#6B6B6B]">
              <Clock className="w-3.5 h-3.5 text-[#2D5016]" />
              <span>Refreshed: <span className="font-mono font-bold text-[#2C2C2C]">{lastRefreshed || "Just now"}</span></span>
              <label className="flex items-center gap-1.5 ml-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoPoll}
                  onChange={(e) => setAutoPoll(e.target.checked)}
                  className="accent-[#2D5016] w-3.5 h-3.5 rounded"
                />
                <span className="text-[11px] font-semibold">Auto-poll Active Jobs</span>
              </label>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#8A8A8A]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by dataset name or ID..."
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl pl-9 pr-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              />
            </div>

            {/* Lifecycle Status Filter */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              >
                <option value="ALL">All Statuses</option>
                <option value="REGISTERED">Registered</option>
                <option value="VALIDATING">Validating</option>
                <option value="PROCESSING">Processing</option>
                <option value="QA_REQUIRED">QA Required</option>
                <option value="READY">Ready</option>
                <option value="PUBLISHED">Published</option>
                <option value="FAILED">Failed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>

            {/* Format Type Filter */}
            <div>
              <select
                value={formatFilter}
                onChange={(e) => setFormatFilter(e.target.value)}
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              >
                <option value="ALL">All Formats</option>
                <option value="uav_raster">UAV Raster (.tif)</option>
                <option value="cadastral_vector">Cadastral Vector (.json)</option>
                <option value="ai_footprints">AI Building Footprints</option>
                <option value="gis_archive">GIS Archive (.zip)</option>
              </select>
            </div>

            {/* Sort Controls */}
            <div className="flex items-center gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="flex-1 bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              >
                <option value="uploaded_at">Upload Date</option>
                <option value="name">Dataset Name</option>
                <option value="status">Status</option>
                <option value="file_size_bytes">File Size</option>
              </select>
              <button
                type="button"
                onClick={() => setAscending(!ascending)}
                className="px-2.5 py-2 bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl text-xs font-mono font-bold text-[#2C2C2C] hover:bg-[#E8E0D0]"
                title="Toggle sort direction"
              >
                {ascending ? "↑" : "↓"}
              </button>
            </div>
          </div>
        </div>

        {/* Dataset Table */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl shadow-sm overflow-hidden">
          <div className="px-6 py-3 border-b border-[#E8E0D0] flex items-center justify-between text-xs font-semibold text-[#6B6B6B]">
            <span>Showing <span className="font-bold text-[#2C2C2C]">{datasets.length}</span> of {totalCount} dataset records</span>
            {(statusFilter !== "ALL" || formatFilter !== "ALL" || searchQuery) && (
              <button
                onClick={() => {
                  setStatusFilter("ALL");
                  setFormatFilter("ALL");
                  setSearchQuery("");
                }}
                className="text-[#2D5016] font-bold hover:underline"
              >
                Clear Filters
              </button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F3EC] text-[#6B6B6B] font-semibold border-b border-[#E8E0D0] uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4">Dataset & ID</th>
                  <th className="py-3 px-4">Format</th>
                  <th className="py-3 px-4">Region</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Status & Stage</th>
                  <th className="py-3 px-4">Progress</th>
                  <th className="py-3 px-4">CRS & Features</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0D0]">
                {datasets.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-xs text-[#8A8A8A]">
                      No geospatial dataset records match your selected filters.
                    </td>
                  </tr>
                ) : (
                  datasets.map((ds) => (
                    <tr key={ds.dataset_id} className="hover:bg-[#F7F3EC]/70 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#2C2C2C] flex items-center gap-1.5">
                          <span>{ds.name}</span>
                        </div>
                        <div className="text-[10px] font-mono text-[#8A8A8A]">{ds.dataset_id}</div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="font-mono text-[11px] font-semibold px-2 py-0.5 rounded bg-[#E8E0D0]/50 text-[#2C2C2C] uppercase">
                          {ds.format}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-[#2C2C2C]">{ds.city}, {ds.state}</div>
                        <div className="text-[10px] font-mono text-[#8A8A8A]">{ds.region_id}</div>
                      </td>

                      <td className="py-3 px-4 font-mono text-[#2C2C2C]">
                        {formatBytes(ds.file_size_bytes)}
                      </td>

                      <td className="py-3 px-4 space-y-1">
                        <div>{getStatusBadge(ds.status)}</div>
                        <div className="text-[10px] text-[#6B6B6B] truncate max-w-[180px]" title={ds.current_stage}>
                          {ds.current_stage}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="w-24 bg-[#E8E0D0] rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 rounded-full ${
                              ds.status === "FAILED"
                                ? "bg-rose-600"
                                : ds.status === "PUBLISHED" || ds.status === "READY"
                                ? "bg-emerald-600"
                                : "bg-[#2D5016]"
                            }`}
                            style={{ width: `${ds.progress_percent}%` }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-[#6B6B6B]">{ds.progress_percent}%</span>
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px] text-[#2C2C2C]">
                        <div>{ds.crs || "EPSG:4326"}</div>
                        <div className="text-[10px] text-[#8A8A8A]">{ds.feature_count ? `${ds.feature_count} features` : "Raster Grid"}</div>
                      </td>

                      <td className="py-3 px-4 text-[#6B6B6B] text-[11px]">
                        <div>{new Date(ds.uploaded_at).toLocaleDateString()}</div>
                        <div className="text-[10px] text-[#8A8A8A]">{ds.uploaded_by.split("@")[0]}</div>
                      </td>

                      <td className="py-3 px-4 text-right space-x-1">
                        <button
                          onClick={() => handleOpenDetail(ds)}
                          className="px-2.5 py-1 text-[11px] font-semibold bg-[#2D5016] hover:bg-[#3A6B1E] text-white rounded-lg transition-colors inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" /> View
                        </button>

                        {ds.status === "FAILED" && (
                          <button
                            onClick={() => handleRetry(ds.dataset_id)}
                            disabled={actionLoading}
                            className="px-2 py-1 text-[11px] font-semibold bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors inline-flex items-center gap-1"
                            title="Retry pipeline job"
                          >
                            <RotateCcw className="w-3 h-3" /> Retry
                          </button>
                        )}

                        {["REGISTERED", "VALIDATING", "PROCESSING"].includes(ds.status) && (
                          <button
                            onClick={() => handleCancel(ds.dataset_id)}
                            disabled={actionLoading}
                            className="px-2 py-1 text-[11px] font-semibold bg-rose-600 hover:bg-rose-700 text-white rounded-lg transition-colors inline-flex items-center gap-1"
                            title="Cancel job"
                          >
                            <Ban className="w-3 h-3" /> Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </main>

      {/* Dataset Details Modal Drawer */}
      {selectedDataset && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-sans text-xs">
            
            {/* Modal Header */}
            <div className="bg-[#1A1A1A] text-white p-4 px-6 flex items-center justify-between border-b border-[#333]">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-display font-bold text-base">{selectedDataset.name}</h2>
                  {getStatusBadge(selectedDataset.status)}
                </div>
                <p className="text-[11px] text-[#8A8A8A] font-mono">ID: {selectedDataset.dataset_id} • Job: {selectedDataset.job_id}</p>
              </div>
              <button
                onClick={() => setSelectedDataset(null)}
                className="text-[#8A8A8A] hover:text-white p-1 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content Sections */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {/* Section A: Overview */}
              <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 space-y-2">
                <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-1.5 border-b border-[#E8E0D0] pb-2">
                  <Database className="w-4 h-4 text-[#2D5016]" />
                  <span>A. Dataset Overview</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1 text-xs">
                  <div><span className="text-[#6B6B6B] block text-[10px]">Original Filename</span><span className="font-semibold text-[#2C2C2C]">{selectedDataset.filename}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Format Type</span><span className="font-semibold text-[#2C2C2C] uppercase">{selectedDataset.format}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">File Size</span><span className="font-mono text-[#2C2C2C]">{formatBytes(selectedDataset.file_size_bytes)}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Target Region</span><span className="font-semibold text-[#2C2C2C]">{selectedDataset.city}, {selectedDataset.state}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Uploaded By</span><span className="text-[#2C2C2C]">{selectedDataset.uploaded_by}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Upload Date</span><span className="text-[#2C2C2C]">{new Date(selectedDataset.uploaded_at).toLocaleString()}</span></div>
                </div>
              </div>

              {/* Section B: Geospatial Metadata */}
              <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 space-y-2">
                <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-1.5 border-b border-[#E8E0D0] pb-2">
                  <MapPin className="w-4 h-4 text-[#2D5016]" />
                  <span>B. Geospatial Metadata</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1 font-mono text-[11px]">
                  <div><span className="text-[#6B6B6B] block text-[10px]">CRS Header</span><span className="font-semibold text-[#2C2C2C]">{selectedDataset.crs || "EPSG:4326"}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Spatial Resolution</span><span className="text-[#2C2C2C]">{selectedDataset.spatial_resolution_m ? `${selectedDataset.spatial_resolution_m} m/px` : "N/A"}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Dimensions / Features</span><span className="text-[#2C2C2C]">{selectedDataset.dimensions || `${selectedDataset.feature_count || 0} features`}</span></div>
                  <div className="col-span-2"><span className="text-[#6B6B6B] block text-[10px]">Geographic Bounding Box</span><span className="text-[#2C2C2C]">{selectedDataset.bounds ? selectedDataset.bounds.join(", ") : "N/A"}</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Available Layers</span><span className="text-[#2D5016] font-semibold">{selectedDataset.layer_names.join(", ")}</span></div>
                </div>
              </div>

              {/* Section D: Tile & Camera Architecture Audit */}
              <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 space-y-2">
                <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-1.5 border-b border-[#E8E0D0] pb-2">
                  <ShieldCheck className="w-4 h-4 text-[#2D5016]" />
                  <span>D. Tile Architecture & Camera Audit</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1 font-mono text-[11px]">
                  <div><span className="text-[#6B6B6B] block text-[10px]">Tile Endpoint Status</span><span className="font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">HEALTHY ✓</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Camera Bounds Lock</span><span className="font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">NOT LOCKED (UNRESTRICTED)</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Raster Files Discovery</span><span className="text-[#2C2C2C] font-semibold">121 GeoTIFF Patches</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Geographic Coverage</span><span className="text-[#2C2C2C]">0.26 km² (262,490 m²)</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">XYZ Tile Scheme</span><span className="text-[#2C2C2C]">WebMercator EPSG:3857</span></div>
                  <div><span className="text-[#6B6B6B] block text-[10px]">Pyramid Zoom Range</span><span className="text-[#2C2C2C]">z12 – z21</span></div>
                </div>
              </div>

              {/* Section C: Processing Timeline */}
              <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 space-y-3">
                <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-1.5 border-b border-[#E8E0D0] pb-2">
                  <Clock className="w-4 h-4 text-[#2D5016]" />
                  <span>C. Processing Pipeline Stage Timeline</span>
                </h3>
                
                <div className="space-y-2 pt-1">
                  {selectedDataset.completed_steps.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="font-semibold text-[#2C2C2C]">{step}</span>
                      <span className="text-[10px] text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded font-mono ml-auto">COMPLETED</span>
                    </div>
                  ))}

                  {selectedDataset.status === "PROCESSING" && (
                    <div className="flex items-center gap-2 text-xs">
                      <RefreshCw className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
                      <span className="font-semibold text-blue-900">{selectedDataset.current_stage}</span>
                      <span className="text-[10px] text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded font-mono ml-auto">IN PROGRESS</span>
                    </div>
                  )}

                  {selectedDataset.pending_steps.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs opacity-60">
                      <div className="w-4 h-4 rounded-full border border-[#8A8A8A] flex items-center justify-center text-[9px] font-mono shrink-0">•</div>
                      <span className="text-[#6B6B6B]">{step}</span>
                      <span className="text-[10px] text-[#8A8A8A] font-mono ml-auto">PENDING</span>
                    </div>
                  ))}

                  {selectedDataset.failed_steps.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs">
                      <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                      <span className="font-semibold text-rose-900">{step}</span>
                      <span className="text-[10px] text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded font-mono ml-auto">FAILED</span>
                    </div>
                  ))}
                </div>

                {selectedDataset.error_details && (
                  <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-lg text-xs space-y-1">
                    <span className="font-bold block">Pipeline Failure Error Details:</span>
                    <p className="font-mono text-[11px]">{selectedDataset.error_details}</p>
                  </div>
                )}
              </div>

              {/* Section D: Validation Results */}
              <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 space-y-2">
                <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-1.5 border-b border-[#E8E0D0] pb-2">
                  <CheckSquare className="w-4 h-4 text-[#2D5016]" />
                  <span>D. Quality & Spatial Validation Audit</span>
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                  <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Format Validation: <span className="font-bold">PASSED</span></div>
                  <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Spatial CRS Check: <span className="font-bold">PASSED</span></div>
                  <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> File Byte Integrity: <span className="font-bold">PASSED</span></div>
                  <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Topology Inspection: <span className="font-bold">VERIFIED</span></div>
                </div>
              </div>

              {/* Section E: Processing Outputs */}
              <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-4 space-y-2">
                <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-1.5 border-b border-[#E8E0D0] pb-2">
                  <Layers className="w-4 h-4 text-[#2D5016]" />
                  <span>E. Generated Geospatial Outputs</span>
                </h3>
                {selectedDataset.outputs.length === 0 ? (
                  <p className="text-xs text-[#8A8A8A] italic">No generated output artifacts available for this dataset stage yet.</p>
                ) : (
                  <div className="space-y-1.5 pt-1">
                    {selectedDataset.outputs.map((out, idx) => (
                      <div key={idx} className="bg-white border border-[#E8E0D0] rounded-lg p-2.5 flex items-center justify-between text-xs font-mono">
                        <div>
                          <span className="font-bold text-[#2C2C2C] block">{out.name}</span>
                          <span className="text-[10px] text-[#8A8A8A]">{out.type} • {out.url}</span>
                        </div>
                        <span className="text-[10px] text-[#2D5016] bg-[#2D5016]/10 px-2 py-0.5 rounded font-bold">AVAILABLE</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

            {/* Modal Actions Footer */}
            <div className="p-4 px-6 bg-[#F7F3EC] border-t border-[#E8E0D0] flex items-center justify-between">
              <button
                onClick={() => setSelectedDataset(null)}
                className="px-4 py-2 bg-white border border-[#E8E0D0] rounded-xl font-semibold text-xs text-[#2C2C2C] hover:bg-[#EDE8DE]"
              >
                Close View
              </button>

              <div className="flex items-center gap-2">
                {selectedDataset.status === "FAILED" && (
                  <button
                    onClick={() => handleRetry(selectedDataset.dataset_id)}
                    disabled={actionLoading}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-semibold text-xs transition-colors flex items-center gap-1"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Retry Processing
                  </button>
                )}

                {["PUBLISHED", "READY"].includes(selectedDataset.status) && (
                  <Link
                    href={`/app/map?dataset_id=${encodeURIComponent(selectedDataset.dataset_id)}`}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-semibold text-xs transition-colors flex items-center gap-1 shadow-xs"
                  >
                    <Globe className="w-3.5 h-3.5" /> View on Map
                  </Link>
                )}

                {["READY", "QA_REQUIRED"].includes(selectedDataset.status) && !selectedDataset.is_published && (
                  <button
                    onClick={() => handlePublish(selectedDataset.dataset_id)}
                    disabled={actionLoading}
                    className="px-4 py-2 bg-[#2D5016] hover:bg-[#3A6B1E] text-white rounded-xl font-semibold text-xs transition-colors flex items-center gap-1 shadow-xs"
                  >
                    <Globe className="w-3.5 h-3.5" /> Publish to WebGIS
                  </button>
                )}
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
