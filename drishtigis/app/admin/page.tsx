"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Database,
  UploadCloud,
  Cpu,
  CheckSquare,
  Globe,
  ArrowRight,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Layers,
  Activity,
  Server,
  FileCode,
  Search,
  Filter,
  Building2,
  ExternalLink,
  MapPin,
  RefreshCw,
  PieChart,
  BarChart3,
  TrendingUp,
  AlertTriangle
} from "lucide-react";
import { useAuth } from "@/lib/auth/Context";
import {
  fetchAnalyticsSummary,
  fetchAdminProperties,
  AnalyticsSummaryData,
  AdminPropertyItem
} from "@/lib/api/datasets";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function formatINR(val?: number | null): string {
  if (val === null || val === undefined) return "Not available";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(val);
}

export default function AdminDashboardPage() {
  const { user } = useAuth();

  const [analytics, setAnalytics] = useState<AnalyticsSummaryData | null>(null);
  const [properties, setProperties] = useState<AdminPropertyItem[]>([]);
  const [totalProps, setTotalProps] = useState(0);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);
  const [loadingProps, setLoadingProps] = useState(true);
  const [healthStatus, setHealthStatus] = useState<"healthy" | "degraded" | "checking">("checking");

  // Property Table Filters
  const [propSearch, setPropSearch] = useState("");
  const [propTypeFilter, setPropTypeFilter] = useState("ALL");

  const loadDashboardData = async () => {
    setLoadingAnalytics(true);
    setLoadingProps(true);

    try {
      const summary = await fetchAnalyticsSummary();
      setAnalytics(summary);
      setHealthStatus("healthy");
    } catch (err) {
      console.error("Analytics fetch error:", err);
      setHealthStatus("degraded");
    } finally {
      setLoadingAnalytics(false);
    }

    try {
      const propData = await fetchAdminProperties({
        search: propSearch,
        property_type: propTypeFilter,
      });
      setProperties(propData.properties);
      setTotalProps(propData.total);
    } catch (err) {
      console.error("Properties fetch error:", err);
    } finally {
      setLoadingProps(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [propSearch, propTypeFilter]);

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans selection:bg-[#2D5016] selection:text-white">
      
      {/* Top Operations Header Bar */}
      <header className="bg-[#1A1A1A] text-[#FBF9F5] px-4 lg:px-8 py-3.5 flex items-center justify-between border-b border-white/10 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#2D5016] text-white flex items-center justify-center font-bold shadow-xs">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-base text-white leading-none">
                Geospatial Operations Center
              </span>
              <span className="text-[10px] bg-[#2D5016] text-white font-mono px-2 py-0.5 rounded font-bold uppercase">
                Admin Console
              </span>
            </div>
            <span className="text-[11px] text-[#8A8A8A] block mt-0.5">
              Monitor datasets, processing pipelines, regional coverage, and cadastral intelligence.
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="hidden md:flex items-center gap-2 text-[#8A8A8A] border-r border-[#333] pr-4">
            <Server className="w-3.5 h-3.5 text-emerald-400" />
            <span>Health:</span>
            <span className="font-mono font-bold text-emerald-400 uppercase">{healthStatus}</span>
          </div>

          <div className="hidden lg:block text-[#8A8A8A] border-r border-[#333] pr-4">
            <span>Admin:</span> <span className="text-white font-semibold">{user?.email || "admin@drishtigis.in"}</span>
          </div>

          <button
            onClick={() => loadDashboardData()}
            className="p-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
            title="Refresh dashboard data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingAnalytics ? "animate-spin" : ""}`} />
          </button>

          <Link href="/app/map" className="px-3 py-1.5 bg-[#2D5016] text-white rounded-lg font-semibold text-xs hover:bg-[#3A6B1E] transition-all shadow-xs flex items-center gap-1">
            <span>Exit Console</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </header>

      {/* Main Console Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-8">
        
        {/* Navigation Quick Bar */}
        <div className="flex items-center justify-between bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl px-6 py-3 shadow-xs text-xs font-semibold text-[#2C2C2C]">
          <div className="flex items-center gap-6">
            <Link href="/admin/datasets" className="hover:text-[#2D5016] flex items-center gap-1.5 font-bold">
              <Database className="w-4 h-4 text-[#2D5016]" />
              <span>Dataset Inventory</span>
            </Link>
            <Link href="/admin/datasets/upload" className="hover:text-[#2D5016] flex items-center gap-1.5">
              <UploadCloud className="w-4 h-4 text-[#2D5016]" />
              <span>Ingest Dataset</span>
            </Link>
            <Link href="/admin/regions" className="hover:text-[#2D5016] flex items-center gap-1.5">
              <Globe className="w-4 h-4 text-[#2D5016]" />
              <span>Governance Regions</span>
            </Link>
            <Link href="/admin/users" className="hover:text-[#2D5016] flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-[#2D5016]" />
              <span>User Governance</span>
            </Link>
          </div>

          <div className="text-[11px] text-[#8A8A8A] font-mono">
            Environment: <span className="text-[#2D5016] font-bold">SIH26012 Prototype</span>
          </div>
        </div>

        {/* 1. Analytics Summary Cards */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-display font-bold text-base text-[#2C2C2C] flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#2D5016]" />
              <span>Geospatial Operations Analytics Summary</span>
            </h2>
            <span className="text-xs text-[#6B6B6B]">Live metrics from backend stores</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            {/* Card 1 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Total Ingested Datasets</span>
              <div className="text-2xl font-bold font-mono text-[#2C2C2C]">
                {analytics?.total_datasets ?? 0}
              </div>
              <div className="text-[10px] text-[#2D5016] font-semibold">100% Persisted in Store</div>
            </div>

            {/* Card 2 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Active Processing Jobs</span>
              <div className="text-2xl font-bold font-mono text-blue-700">
                {analytics?.active_processing_jobs ?? 0}
              </div>
              <div className="text-[10px] text-blue-800 font-semibold">Async Background Execution</div>
            </div>

            {/* Card 3 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Completed / Ready</span>
              <div className="text-2xl font-bold font-mono text-emerald-700">
                {analytics?.completed_datasets ?? 0}
              </div>
              <div className="text-[10px] text-emerald-800 font-semibold">QA Verified & Ready</div>
            </div>

            {/* Card 4 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Failed Pipeline Jobs</span>
              <div className="text-2xl font-bold font-mono text-rose-700">
                {analytics?.failed_jobs ?? 0}
              </div>
              <div className="text-[10px] text-rose-800 font-semibold">Safe Retry Eligible</div>
            </div>

            {/* Card 5 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Awaiting QA Review</span>
              <div className="text-2xl font-bold font-mono text-amber-700">
                {analytics?.qa_required_count ?? 0}
              </div>
              <div className="text-[10px] text-amber-800 font-semibold">Surveyor Review Queue</div>
            </div>

            {/* Card 6 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Published to WebGIS</span>
              <div className="text-2xl font-bold font-mono text-purple-700">
                {analytics?.published_datasets ?? 0}
              </div>
              <div className="text-[10px] text-purple-800 font-semibold">Public XYZ / Feature Feeds</div>
            </div>

            {/* Card 7 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Total Ingested Data Volume</span>
              <div className="text-xl font-bold font-mono text-[#2C2C2C]">
                {formatBytes(analytics?.total_ingested_size_bytes ?? 0)}
              </div>
              <div className="text-[10px] text-[#2D5016] font-semibold">Raster & Vector Files</div>
            </div>

            {/* Card 8 */}
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 space-y-1 shadow-sm">
              <span className="text-xs text-[#6B6B6B] block">Total Mapped Features</span>
              <div className="text-xl font-bold font-mono text-[#2C2C2C]">
                {analytics?.total_mapped_features?.toLocaleString() ?? 0}
              </div>
              <div className="text-[10px] text-[#2D5016] font-semibold">AI Buildings & Parcels</div>
            </div>

          </div>
        </div>

        {/* 2. Operations & Format Breakdown Visualizations */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Status Breakdown Bar */}
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm space-y-4 md:col-span-2">
            <div className="flex items-center justify-between border-b border-[#E8E0D0] pb-3">
              <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-2">
                <PieChart className="w-4 h-4 text-[#2D5016]" />
                <span>Dataset Ingestion Status Distribution</span>
              </h3>
              <span className="text-xs text-[#6B6B6B] font-mono">Bhopal Prototype Region</span>
            </div>

            {analytics ? (
              <div className="space-y-3 pt-1 text-xs">
                {Object.entries(analytics.by_status).map(([st, count]) => {
                  const pct = Math.round((count / (analytics.total_datasets || 1)) * 100);
                  return (
                    <div key={st} className="space-y-1">
                      <div className="flex items-center justify-between text-[#2C2C2C]">
                        <span className="font-bold font-mono uppercase">{st}</span>
                        <span className="font-mono text-[#6B6B6B]">{count} dataset(s) ({pct}%)</span>
                      </div>
                      <div className="w-full bg-[#E8E0D0] h-2.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            st === "PUBLISHED"
                              ? "bg-emerald-600"
                              : st === "READY"
                              ? "bg-teal-600"
                              : st === "PROCESSING"
                              ? "bg-blue-600"
                              : st === "FAILED"
                              ? "bg-rose-600"
                              : "bg-[#2D5016]"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-xs text-[#8A8A8A] italic py-8 text-center">Loading analytics charts...</div>
            )}
          </div>

          {/* Regional Coverage Breakdown */}
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm space-y-4">
            <div className="border-b border-[#E8E0D0] pb-3">
              <h3 className="font-bold text-sm text-[#2C2C2C] flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#2D5016]" />
                <span>Regional Dataset Coverage</span>
              </h3>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-[#F7F3EC] border border-[#2D5016]/30 rounded-xl p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#2C2C2C]">Bhopal, Madhya Pradesh</span>
                  <span className="text-[10px] bg-[#2D5016] text-white font-mono px-2 py-0.5 rounded font-bold">PROTOTYPE</span>
                </div>
                <div className="text-[11px] text-[#6B6B6B] space-y-0.5 font-mono">
                  <p>&bull; UAV Tiles: <span className="text-[#2C2C2C] font-bold">30 GeoTIFFs (0.02m)</span></p>
                  <p>&bull; AI Footprints: <span className="text-[#2C2C2C] font-bold">834 Buildings</span></p>
                  <p>&bull; Demo Parcels: <span className="text-[#2C2C2C] font-bold">35 Cadastral Polygons</span></p>
                  <p>&bull; OSM Roads & Landuse: <span className="text-[#2C2C2C] font-bold">3,031 Vector Features</span></p>
                </div>
              </div>

              <div className="text-[11px] text-[#8A8A8A] bg-[#EDE8DE]/40 p-2.5 rounded-lg border border-[#E8E0D0]">
                Notice: Additional governance regions (Indore, Gwalior, Jabalpur) are pending administrative onboarding.
              </div>
            </div>
          </div>

        </div>

        {/* 3. Property & Cadastral Intelligence Table */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E8E0D0] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#2D5016]" />
                <h2 className="font-display font-bold text-lg text-[#2C2C2C]">Property & Cadastral Intelligence Table</h2>
              </div>
              <p className="text-xs text-[#6B6B6B] mt-0.5">
                Inspect synthetic demo parcels and user-submitted property markers with strict privacy safeguards and INR valuation formatting.
              </p>
            </div>

            <div className="text-xs font-semibold text-[#6B6B6B]">
              Showing <span className="font-bold text-[#2C2C2C]">{properties.length}</span> of {totalProps} properties
            </div>
          </div>

          {/* Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#8A8A8A]" />
              <input
                type="text"
                value={propSearch}
                onChange={(e) => setPropSearch(e.target.value)}
                placeholder="Search Property ID, Survey No, or Owner Name..."
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl pl-9 pr-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              />
            </div>

            <div>
              <select
                value={propTypeFilter}
                onChange={(e) => setPropTypeFilter(e.target.value)}
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              >
                <option value="ALL">All Property Types</option>
                <option value="residential">Residential</option>
                <option value="commercial">Commercial</option>
                <option value="vacant_plot">Vacant Plot</option>
                <option value="house">House / Family Unit</option>
                <option value="building">Commercial Building</option>
              </select>
            </div>

            <div className="text-right">
              <button
                onClick={() => {
                  setPropSearch("");
                  setPropTypeFilter("ALL");
                }}
                className="px-3 py-2 bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl font-bold text-[#2C2C2C] hover:bg-[#E8E0D0]"
              >
                Reset Filters
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto border border-[#E8E0D0] rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F3EC] text-[#6B6B6B] font-semibold border-b border-[#E8E0D0] uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-3">Property ID</th>
                  <th className="py-3 px-3">Survey / Plot No</th>
                  <th className="py-3 px-3">Type</th>
                  <th className="py-3 px-3">Area (m²)</th>
                  <th className="py-3 px-3">Owner Name</th>
                  <th className="py-3 px-3">Residents</th>
                  <th className="py-3 px-3">Purchase Price (INR)</th>
                  <th className="py-3 px-3">Est. Selling Price (INR)</th>
                  <th className="py-3 px-3">AI Buildings</th>
                  <th className="py-3 px-3">Coverage</th>
                  <th className="py-3 px-3">Data Source</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0D0]">
                {loadingProps ? (
                  <tr>
                    <td colSpan={12} className="py-8 text-center text-xs text-[#8A8A8A] italic">Loading property intelligence records...</td>
                  </tr>
                ) : properties.length === 0 ? (
                  <tr>
                    <td colSpan={12} className="py-8 text-center text-xs text-[#8A8A8A]">No properties match search filter.</td>
                  </tr>
                ) : (
                  properties.map((p) => (
                    <tr key={p.property_id} className="hover:bg-[#F7F3EC]/70 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-[#2C2C2C]">{p.property_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-[#2C2C2C]">{p.plot_number}</td>
                      <td className="py-2.5 px-3 uppercase text-[11px] font-mono text-[#6B6B6B]">{p.property_type}</td>
                      <td className="py-2.5 px-3 font-mono text-[#2C2C2C]">{Math.round(p.parcel_area_m2)} m²</td>
                      <td className="py-2.5 px-3 font-semibold text-[#2C2C2C]">{p.owner_name}</td>
                      <td className="py-2.5 px-3 text-[#6B6B6B]">{p.resident_count ?? "N/A"}</td>
                      <td className="py-2.5 px-3 font-mono text-[#2C2C2C]">{formatINR(p.purchase_price_inr)}</td>
                      <td className="py-2.5 px-3 font-mono text-[#2D5016] font-bold">{formatINR(p.estimated_selling_price_inr)}</td>
                      <td className="py-2.5 px-3 font-mono text-[#2C2C2C]">{p.ai_building_count} ({Math.round(p.ai_detected_area_m2)} m²)</td>
                      <td className="py-2.5 px-3 font-mono text-[11px]">{Math.round(p.coverage_ratio * 100)}%</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          p.data_source === "SYNTHETIC_DEMO"
                            ? "bg-amber-100 text-amber-900 border border-amber-300"
                            : "bg-purple-100 text-purple-900 border border-purple-300"
                        }`}>
                          {p.data_source}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Link
                          href={`/app/map?parcel=${encodeURIComponent(p.property_id)}`}
                          className="px-2.5 py-1 text-[11px] font-semibold bg-[#2D5016] hover:bg-[#3A6B1E] text-white rounded transition-colors inline-flex items-center gap-1"
                        >
                          <MapPin className="w-3 h-3" /> Map
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="text-[11px] text-[#8A8A8A] bg-[#EDE8DE]/40 p-3 rounded-xl border border-[#E8E0D0] space-y-1">
            <span className="font-bold text-[#2C2C2C] block">Mandatory Data Integrity Notice:</span>
            <p>
              All synthetic demonstration records carry explicit synthetic disclaimers. User profile submissions do not constitute official land title records. Private user phone numbers and unconsented addresses are strictly redacted.
            </p>
          </div>
        </div>

      </main>

    </div>
  );
}
