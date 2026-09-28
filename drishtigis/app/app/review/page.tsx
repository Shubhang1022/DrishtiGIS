"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Map as MapIcon,
  Filter as FunnelIcon,
  RefreshCw as ArrowPathIcon,
  ShieldCheck,
  FileSearch as DocumentMagnifyingGlassIcon,
  Edit3 as PencilSquareIcon,
  Download as ArrowDownTrayIcon,
} from "lucide-react";

import {
  getReviewQueue,
  getReviewStats,
  exportReviewedGeoJSON,
} from "@/lib/api/reviews";
import type {
  ReviewItem,
  ReviewStats,
  ReviewStatus,
  ReviewIssueType,
  ReviewSeverity,
} from "@/lib/types/review";

export default function ReviewQueuePage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedIssueType, setSelectedIssueType] = useState<string>("ALL");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchQueueData = async () => {
    setLoading(true);
    setError(null);
    try {
      const filterParams: any = {};
      if (selectedStatus !== "ALL") filterParams.status = selectedStatus;
      if (selectedIssueType !== "ALL") filterParams.issue_type = selectedIssueType;
      if (selectedSeverity !== "ALL") filterParams.severity = selectedSeverity;

      const [queueRes, statsRes] = await Promise.all([
        getReviewQueue(filterParams),
        getReviewStats(),
      ]);

      setReviews(queueRes.items);
      setStats(statsRes);
    } catch (err: any) {
      console.error("Failed to load review queue:", err);
      setError("Unable to connect to backend review queue service. Please verify server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueData();
  }, [selectedStatus, selectedIssueType, selectedSeverity]);

  const filteredItems = reviews.filter((item) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      item.review_id.toLowerCase().includes(query) ||
      (item.parcel_id && item.parcel_id.toLowerCase().includes(query)) ||
      (item.entity_id && item.entity_id.toLowerCase().includes(query)) ||
      item.issue_type.toLowerCase().includes(query)
    );
  });

  const handleExportGeoJSON = async () => {
    try {
      const geojson = await exportReviewedGeoJSON("Bhopal");
      const blob = new Blob([JSON.stringify(geojson, null, 2)], {
        type: "application/geo+json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DrishtiGIS_Reviewed_Geometry_${new Date().toISOString().slice(0, 10)}.geojson`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to export reviewed GIS geometry.");
    }
  };

  const getStatusBadge = (status: ReviewStatus) => {
    switch (status) {
      case "OPEN":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20"><Clock className="w-3.5 h-3.5 mr-1" />OPEN</span>;
      case "IN_REVIEW":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20"><PencilSquareIcon className="w-3.5 h-3.5 mr-1" />IN REVIEW</span>;
      case "FIELD_VERIFICATION_REQUIRED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20"><DocumentMagnifyingGlassIcon className="w-3.5 h-3.5 mr-1" />FIELD VERIFICATION</span>;
      case "ACCEPTED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle2 className="w-3.5 h-3.5 mr-1" />ACCEPTED</span>;
      case "REJECTED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20"><XCircle className="w-3.5 h-3.5 mr-1" />REJECTED</span>;
      case "RESOLVED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"><ShieldCheck className="w-3.5 h-3.5 mr-1" />RESOLVED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs bg-gray-700 text-gray-300">{status}</span>;
    }
  };

  const getSeverityBadge = (severity: ReviewSeverity) => {
    switch (severity) {
      case "HIGH":
        return <span className="text-xs font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">HIGH</span>;
      case "MEDIUM":
        return <span className="text-xs font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">MEDIUM</span>;
      case "LOW":
        return <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">LOW</span>;
      default:
        return <span className="text-xs text-gray-400">{severity}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <ClipboardCheck className="w-8 h-8 text-cyan-400" />
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Surveyor Review & Field Verification Queue
              </h1>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Inspect AI-derived features, review geometric discrepancies, validate cadastral topology, and record field observations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExportGeoJSON}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors shadow-lg shadow-cyan-900/20"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              Export Reviewed GIS
            </button>
            <Link
              href="/app/map"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition-colors"
            >
              <MapIcon className="w-4 h-4" />
              WebGIS View
            </Link>
          </div>
        </div>

        {/* Disclaimer Banner */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <span className="font-semibold text-amber-300 uppercase tracking-wide mr-2">
              Demonstration Prototype:
            </span>
            All parcel boundaries and property attributes are synthetic prototype data. AI building extractions are spatial observations only.
            This workflow supports ground-truthing and cadastral verification, but does NOT constitute official legal property determinations.
          </div>
        </div>

        {/* Workflow Metrics */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-slate-400 uppercase font-semibold">Total Issues</div>
              <div className="text-xl font-bold text-slate-100 mt-1">{stats.total_issues}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-amber-400 uppercase font-semibold">Open</div>
              <div className="text-xl font-bold text-amber-400 mt-1">{stats.open}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-blue-400 uppercase font-semibold">In Review</div>
              <div className="text-xl font-bold text-blue-400 mt-1">{stats.in_review}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-purple-400 uppercase font-semibold">Field Verification</div>
              <div className="text-xl font-bold text-purple-400 mt-1">{stats.field_verification_required}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-emerald-400 uppercase font-semibold">Accepted</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">{stats.accepted}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-rose-400 uppercase font-semibold">Rejected</div>
              <div className="text-xl font-bold text-rose-400 mt-1">{stats.rejected}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-cyan-400 uppercase font-semibold">Edits Saved</div>
              <div className="text-xl font-bold text-cyan-400 mt-1">{stats.geometry_adjustments}</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-xs text-emerald-300 uppercase font-semibold">Field Verified</div>
              <div className="text-xl font-bold text-emerald-300 mt-1">{stats.field_verified}</div>
            </div>
          </div>
        )}

        {/* Filter Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase">
              <FunnelIcon className="w-4 h-4" /> Filters:
            </div>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-medium focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="FIELD_VERIFICATION_REQUIRED">Field Verification Required</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="REJECTED">Rejected</option>
              <option value="RESOLVED">Resolved</option>
            </select>

            {/* Issue Type Filter */}
            <select
              value={selectedIssueType}
              onChange={(e) => setSelectedIssueType(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-medium focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Issue Types</option>
              <option value="BUILDING_CROSSES_PARCEL_BOUNDARY">Building Crosses Parcel Boundary</option>
              <option value="MULTIPLE_BUILDINGS_IN_PARCEL">Multiple Buildings in Parcel</option>
              <option value="NO_PARCEL_MATCH">No Parcel Match</option>
              <option value="ACCESS_REVIEW_REQUIRED">Access Review Required</option>
              <option value="LAND_USE_REVIEW">Land-Use Review</option>
              <option value="HISTORICAL_CHANGE_REVIEW">Historical Change Review</option>
            </select>

            {/* Severity Filter */}
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-medium focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Severities</option>
              <option value="HIGH">High Severity</option>
              <option value="MEDIUM">Medium Severity</option>
              <option value="LOW">Low Severity</option>
            </select>
          </div>

          {/* Search Box */}
          <div className="flex items-center gap-2 w-full md:w-64">
            <input
              type="text"
              placeholder="Search Review ID or Parcel..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={fetchQueueData}
              title="Refresh Queue"
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg transition-colors"
            >
              <ArrowPathIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Review Queue Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-3">
              <ArrowPathIcon className="w-8 h-8 animate-spin text-cyan-400" />
              <span>Loading review queue items...</span>
            </div>
          ) : error ? (
            <div className="p-12 text-center text-rose-400">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
              <span>{error}</span>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <span>No review queue items match the selected criteria.</span>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-3 px-4">Review ID</th>
                    <th className="py-3 px-4">Parcel / Entity</th>
                    <th className="py-3 px-4">Issue Type</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Source</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredItems.map((item) => (
                    <tr key={item.review_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-cyan-400">
                        {item.review_id}
                      </td>
                      <td className="py-3 px-4 text-slate-200">
                        {item.parcel_id ? (
                          <span className="font-mono text-slate-300">{item.parcel_id}</span>
                        ) : (
                          <span className="text-slate-400">{item.entity_id}</span>
                        )}
                        <div className="text-[10px] text-slate-500">{item.city}, {item.state}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-medium">
                        {item.issue_type.replace(/_/g, " ")}
                      </td>
                      <td className="py-3 px-4">
                        {getSeverityBadge(item.severity)}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                          {item.source}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {getStatusBadge(item.status)}
                      </td>
                      <td className="py-3 px-4 text-right space-x-2">
                        {item.parcel_id && (
                          <Link
                            href={`/app/map?parcel=${item.parcel_id}&review=${item.review_id}`}
                            className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 rounded transition-colors"
                          >
                            <MapIcon className="w-3.5 h-3.5" /> Inspect on Map
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
