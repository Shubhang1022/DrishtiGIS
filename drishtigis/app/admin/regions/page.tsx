"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Globe, 
  MapPin, 
  Plus, 
  ArrowLeft, 
  RefreshCw, 
  CheckCircle2, 
  Database,
  Building2,
  AlertCircle
} from "lucide-react";
import { useAuth } from "@/lib/auth/Context";
import { fetchRegions, createRegion } from "@/lib/api/auth";

export default function AdminRegionsPage() {
  const { token } = useAuth();
  const [regions, setRegions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [showModal, setShowModal] = useState(false);
  const [regionId, setRegionId] = useState("");
  const [stateName, setStateName] = useState("");
  const [cityName, setCityName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadRegions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRegions();
      setRegions(data);
    } catch (err: any) {
      setError(err.message || "Failed to load governance regions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRegions();
  }, []);

  const handleCreateRegion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    try {
      const newRegion = await createRegion(token, {
        region_id: regionId.trim().toLowerCase().replace(/\s+/g, "_"),
        country: "India",
        state: stateName,
        city: cityName,
        description,
        status: "ACTIVE",
        bounding_box: [77.3, 23.2, 77.5, 23.3]
      });
      setRegions(prev => [...prev, newRegion.region || newRegion]);
      setShowModal(false);
      setRegionId("");
      setStateName("");
      setCityName("");
      setDescription("");
    } catch (err: any) {
      alert(err.message || "Failed to register region");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      {/* Console Header */}
      <header className="bg-[#1A1A1A] text-[#FBF9F5] px-4 lg:px-8 py-3.5 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-white/70 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="w-8 h-8 rounded-lg bg-[#2D5016] flex items-center justify-center font-bold">
            <Globe className="w-4 h-4 text-[#FBF9F5]" />
          </div>
          <div>
            <h1 className="font-display font-bold text-base text-white leading-none">
              Region & Territorial Governance
            </h1>
            <p className="text-[10px] text-[#8A8A8A]">Pan-India Multilevel Spatial Jurisdiction Framework</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <Link href="/admin/datasets" className="text-[#FBF9F5]/80 hover:text-white transition-colors">
            Datasets
          </Link>
          <Link href="/admin/regions" className="text-white font-semibold border-b border-[#2D5016]">
            Regions
          </Link>
          <Link href="/admin/users" className="text-[#FBF9F5]/80 hover:text-white transition-colors">
            Users
          </Link>
          <Link href="/app/map" className="px-3 py-1 bg-[#2D5016] text-white rounded font-medium text-xs hover:bg-[#3A6B1E] transition-colors">
            Exit Console
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        {/* Top Control Bar */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-panel space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-bold text-base text-[#2D5016]">
                Registered Jurisdictional Regions ({regions.length})
              </h2>
              <p className="text-xs text-[#6B6B6B]">
                Organized under India &rarr; State &rarr; City &rarr; Spatial Bounds.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={loadRegions}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-[#F7F3EC] border border-[#E8E0D0] hover:border-[#2D5016] rounded-lg text-xs font-semibold text-[#2C2C2C] transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>

              <button
                onClick={() => setShowModal(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#2D5016] hover:bg-[#3A6B1E] text-white rounded-lg text-xs font-semibold transition-colors shadow-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Register New Region</span>
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Regions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {regions.map((reg) => (
            <div key={reg.region_id} className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-5 shadow-panel space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-[#2D5016]" />
                  <span className="font-bold text-sm text-[#2C2C2C]">{reg.city}, {reg.state}</span>
                </div>
                <span className="bg-[#2D5016]/15 text-[#2D5016] px-2 py-0.5 rounded font-bold text-[10px]">
                  {reg.status || "ACTIVE"}
                </span>
              </div>

              <div className="font-mono text-xs text-[#2D5016] font-semibold bg-[#F7F3EC] px-2.5 py-1 rounded border border-[#E8E0D0]">
                ID: {reg.region_id}
              </div>

              <p className="text-xs text-[#6B6B6B] leading-relaxed">
                {reg.description || `Territorial boundary for urban GIS parcel extraction in ${reg.city}.`}
              </p>

              <div className="border-t border-[#E8E0D0] pt-3 flex items-center justify-between text-[11px] text-[#8A8A8A]">
                <div className="flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5" />
                  <span>Country: {reg.country || "India"}</span>
                </div>
                <div className="flex items-center gap-1 text-[#2D5016] font-semibold">
                  <Database className="w-3.5 h-3.5" />
                  <span>Dataset Scope</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Register Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
              <h3 className="font-bold text-base text-[#2D5016]">
                Register Governance Region
              </h3>
              <p className="text-xs text-[#6B6B6B]">
                Add a new administrative territorial zone for multi-region dataset governance.
              </p>

              <form onSubmit={handleCreateRegion} className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-[#2C2C2C] block mb-1">State / UT</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Uttar Pradesh, Maharashtra, Karnataka"
                    value={stateName}
                    onChange={(e) => setStateName(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#2C2C2C] block mb-1">City / Municipal Zone</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Lucknow, Pune, Bengaluru"
                    value={cityName}
                    onChange={(e) => setCityName(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#2C2C2C] block mb-1">Region Identifier Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. lucknow_up, pune_mh, blr_ka"
                    value={regionId}
                    onChange={(e) => setRegionId(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] font-mono focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#2C2C2C] block mb-1">Description</label>
                  <textarea
                    rows={3}
                    placeholder="Brief description of the drone survey extent or cadastral jurisdiction..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-[#E8E0D0] rounded-lg text-xs font-semibold text-[#6B6B6B] hover:bg-[#F7F3EC]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 bg-[#2D5016] text-white rounded-lg text-xs font-semibold hover:bg-[#3A6B1E] disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : "Register Region"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </main>

    </div>
  );
}
