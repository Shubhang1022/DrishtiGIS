"use client";

import React, { useState, useEffect } from "react";
import {
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  FileCheck,
  Compass,
  History,
  Shield,
  Pencil,
  RotateCcw,
  Check,
  Send,
  MapPin,
  Layers,
} from "lucide-react";

import {
  getReviewDetail,
  getReviewQueue,
  updateReviewStatus,
  submitGeometryEdit,
  recordFieldVerification,
} from "@/lib/api/reviews";
import type {
  ReviewItem,
  ReviewAuditTrail,
  FieldVerificationRecord,
  ReviewStatus,
  VerificationMethod,
} from "@/lib/types/review";

interface ReviewModePanelProps {
  parcelId?: string;
  reviewId?: string;
  onCloseReview?: () => void;
  onGeometryEdit?: (revisedGeometry: any) => void;
}

export function ReviewModePanel({
  parcelId,
  reviewId,
  onCloseReview,
  onGeometryEdit,
}: ReviewModePanelProps) {
  const [reviewItem, setReviewItem] = useState<ReviewItem | null>(null);
  const [auditTrail, setAuditTrail] = useState<ReviewAuditTrail[]>([]);
  const [verifications, setVerifications] = useState<FieldVerificationRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Geometry Edit State
  const [showOriginal, setShowOriginal] = useState<boolean>(false);
  const [isEditingGeom, setIsEditingGeom] = useState<boolean>(false);
  const [geomError, setGeomError] = useState<string | null>(null);
  const [recompSuccess, setRecompSuccess] = useState<string | null>(null);

  // Field Verification State
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verifMethod, setVerifMethod] = useState<VerificationMethod>("GNSS");
  const [verifFeature, setVerifFeature] = useState<string>("Observed boundary");
  const [verifObservation, setVerifObservation] = useState<string>("");
  const [verifNotes, setVerifNotes] = useState<string>("");

  // Review Status State
  const [selectedStatus, setSelectedStatus] = useState<ReviewStatus>("IN_REVIEW");
  const [reviewerNotes, setReviewerNotes] = useState<string>("");

  const loadReviewDetails = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getReviewDetail(id);
      setReviewItem(res.item);
      setAuditTrail(res.audit_trail);
      setVerifications(res.field_verifications);
      setSelectedStatus(res.item.status);
      setReviewerNotes(res.item.reviewer_notes ?? "");
    } catch (err: any) {
      console.error("Failed to fetch review detail:", err);
      setError("Review item detail could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (reviewId) {
      loadReviewDetails(reviewId);
    } else if (parcelId) {
      // Auto-lookup review for parcel
      getReviewQueue({ city: "Bhopal" })
        .then((data) => {
          const match = data.items?.find((i: ReviewItem) => i.parcel_id === parcelId);
          if (match) {
            loadReviewDetails(match.review_id);
          } else {
            setLoading(false);
            setError(`No active review item found for parcel ${parcelId}.`);
          }
        })
        .catch(() => {
          setLoading(false);
          setError("Failed to query reviews.");
        });
    }
  }, [reviewId, parcelId]);

  const handleStatusUpdate = async () => {
    if (!reviewItem) return;
    try {
      const res = await updateReviewStatus(reviewItem.review_id, selectedStatus, "Surveyor-01", reviewerNotes);
      setReviewItem(res.item);
      await loadReviewDetails(reviewItem.review_id);
      alert(`Review status updated to ${selectedStatus}.`);
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  const handleGeometrySubmit = async () => {
    if (!reviewItem) return;
    setGeomError(null);
    setRecompSuccess(null);

    const targetGeom = reviewItem.reviewed_geometry || reviewItem.original_geometry;
    if (!targetGeom) {
      setGeomError("No valid geometry available to submit.");
      return;
    }

    try {
      const res = await submitGeometryEdit(
        reviewItem.review_id,
        targetGeom,
        "Surveyor-01",
        "Surveyor boundary adjustment applied."
      );
      setReviewItem(res.item);
      setRecompSuccess("Geometry validated! Spatial relationships recomputed automatically.");
      setIsEditingGeom(false);
      if (onGeometryEdit) onGeometryEdit(targetGeom);
      await loadReviewDetails(reviewItem.review_id);
    } catch (err: any) {
      setGeomError(err.message || "Geometry requires correction before approval.");
    }
  };

  const handleVerificationSubmit = async () => {
    if (!reviewItem || !verifObservation.trim()) {
      alert("Please provide a neutral observation description.");
      return;
    }
    try {
      await recordFieldVerification(reviewItem.review_id, {
        verification_method: verifMethod,
        observed_feature: verifFeature,
        observation: verifObservation,
        notes: verifNotes,
        reviewer: "Field-Surveyor-01",
      });
      alert("Field verification observation recorded successfully!");
      setIsVerifying(false);
      setVerifObservation("");
      await loadReviewDetails(reviewItem.review_id);
    } catch (err: any) {
      alert(`Failed to record field verification: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-xs text-[#8A8A8A] space-y-2">
        <div className="w-6 h-6 rounded-full border-2 border-[#E8E0D0] border-t-cyan-600 animate-spin mx-auto" />
        <p>Loading surveyor review workflow...</p>
      </div>
    );
  }

  if (error || !reviewItem) {
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 space-y-2">
        <div className="flex items-center gap-1.5 font-bold">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Review Unavailable</span>
        </div>
        <p>{error ?? "Select a valid review item from the queue to start review mode."}</p>
        {onCloseReview && (
          <button
            onClick={onCloseReview}
            className="px-3 py-1 bg-white border border-rose-300 rounded text-[11px] font-medium text-rose-700 hover:bg-rose-100"
          >
            Back to Details
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4 text-xs font-sans">
      {/* Top Banner */}
      <div className="bg-cyan-950/90 text-cyan-100 border border-cyan-800 rounded-xl p-3.5 space-y-2 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="font-bold text-sm text-cyan-200">SURVEYOR REVIEW MODE</h3>
              <p className="text-[10px] text-cyan-400/80 font-mono">{reviewItem.review_id}</p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/20 border border-cyan-400/30 text-cyan-300">
            {reviewItem.status}
          </span>
        </div>

        {onCloseReview && (
          <button
            onClick={onCloseReview}
            className="w-full text-center py-1 text-[11px] bg-cyan-900/60 hover:bg-cyan-900 border border-cyan-700/50 rounded text-cyan-200 font-medium transition-colors"
          >
            Exit Review Mode
          </button>
        )}
      </div>

      {/* Synthetic & AI Disclaimer */}
      <div className="bg-amber-50 border border-amber-300 rounded-xl p-3 text-[11px] text-amber-900 leading-relaxed">
        <div className="font-bold flex items-center gap-1.5 mb-1 text-amber-800">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          <span>DEMO PROPERTY — NOT OFFICIAL LAND RECORD</span>
        </div>
        Spatial relationships represent visual AI/GIS observations on synthetic prototype data. All reviewer edits store reviewed state separate from original AI data.
      </div>

      {/* Issue Summary */}
      <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
        <h4 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-[#2D5016]" />
          <span>ISSUE & EVIDENCE SUMMARY</span>
        </h4>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex justify-between border-b border-[#E8E0D0] pb-1">
            <span className="text-[#8A8A8A]">Issue Type:</span>
            <span className="font-semibold text-[#2C2C2C]">{reviewItem.issue_type}</span>
          </div>
          <div className="flex justify-between border-b border-[#E8E0D0] pb-1">
            <span className="text-[#8A8A8A]">Severity:</span>
            <span className="font-bold text-amber-600">{reviewItem.severity}</span>
          </div>
          <div className="flex justify-between border-b border-[#E8E0D0] pb-1">
            <span className="text-[#8A8A8A]">Source Classification:</span>
            <span className="font-mono text-cyan-800">{reviewItem.source}</span>
          </div>
          <div className="flex justify-between border-b border-[#E8E0D0] pb-1">
            <span className="text-[#8A8A8A]">Parcel ID:</span>
            <span className="font-mono text-[#2C2C2C]">{reviewItem.parcel_id ?? "N/A"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#8A8A8A]">Location:</span>
            <span className="text-[#2C2C2C]">{reviewItem.city}, {reviewItem.state}</span>
          </div>
        </div>
      </section>

      {/* Geometry Editing Section */}
      <section className="bg-slate-900 text-slate-100 border border-slate-800 rounded-xl p-3.5 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
            <Pencil className="w-3.5 h-3.5" />
            <span>CADASTRAL GEOMETRY EDITING</span>
          </h4>
          <span className="text-[10px] font-mono text-slate-400">
            {reviewItem.geometry_changed ? "REVIEWED_AI_GEOMETRY" : "AI_DERIVED_UAVPAL"}
          </span>
        </div>

        {/* Toggle Original vs Reviewed */}
        <div className="flex items-center justify-between bg-slate-950 p-2 rounded-lg border border-slate-800 text-[11px]">
          <span className="text-slate-400">Layer View Mode:</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowOriginal(true)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                showOriginal ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-400"
              }`}
            >
              Show Original AI
            </button>
            <button
              onClick={() => setShowOriginal(false)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                !showOriginal ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-400"
              }`}
            >
              Show Reviewed
            </button>
          </div>
        </div>

        {geomError && (
          <div className="p-2 bg-rose-950/80 border border-rose-800 text-rose-200 text-[11px] rounded">
            {geomError}
          </div>
        )}

        {recompSuccess && (
          <div className="p-2 bg-emerald-950/80 border border-emerald-800 text-emerald-200 text-[11px] rounded">
            {recompSuccess}
          </div>
        )}

        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={handleGeometrySubmit}
            className="flex-1 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs rounded transition-colors flex items-center justify-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5" />
            Validate & Save Reviewed Geometry
          </button>
        </div>
      </section>

      {/* Field Verification Section */}
      <section className="bg-purple-950/40 border border-purple-900/60 rounded-xl p-3.5 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-[10px] font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-purple-400" />
            <span>GROUND-TRUTHING & FIELD VERIFICATION</span>
          </h4>
          <button
            onClick={() => setIsVerifying(!isVerifying)}
            className="text-[10px] text-purple-400 hover:text-purple-300 underline font-medium"
          >
            {isVerifying ? "Cancel" : "+ Record Observation"}
          </button>
        </div>

        {isVerifying && (
          <div className="space-y-2.5 pt-1">
            <div>
              <label className="text-[10px] text-purple-300 font-semibold block mb-1">
                Verification Method:
              </label>
              <select
                value={verifMethod}
                onChange={(e) => setVerifMethod(e.target.value as VerificationMethod)}
                className="w-full bg-slate-900 border border-purple-800 text-purple-100 rounded px-2 py-1 text-xs"
              >
                <option value="GNSS">GNSS RTK Receiver</option>
                <option value="ON_SITE">On-Site Inspection</option>
                <option value="CORS">CORS Station Survey</option>
                <option value="SURVEY_RECORD">Official Survey Record</option>
                <option value="FIELD_PHOTO">Field Photograph Evidence</option>
                <option value="AUTHORITY_RECORD">Authority Record</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-purple-300 font-semibold block mb-1">
                Observed Feature:
              </label>
              <input
                type="text"
                value={verifFeature}
                onChange={(e) => setVerifFeature(e.target.value)}
                className="w-full bg-slate-900 border border-purple-800 text-purple-100 rounded px-2 py-1 text-xs"
              />
            </div>

            <div>
              <label className="text-[10px] text-purple-300 font-semibold block mb-1">
                Field Observation (Neutral):
              </label>
              <textarea
                value={verifObservation}
                onChange={(e) => setVerifObservation(e.target.value)}
                placeholder="e.g. Observed boundary differs from preliminary AI-derived boundary..."
                className="w-full bg-slate-900 border border-purple-800 text-purple-100 rounded px-2 py-1 text-xs h-16"
              />
            </div>

            <button
              onClick={handleVerificationSubmit}
              className="w-full py-1.5 bg-purple-700 hover:bg-purple-600 text-white font-medium text-xs rounded transition-colors flex items-center justify-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              Submit Field Verification Observation
            </button>
          </div>
        )}

        {verifications.length > 0 && (
          <div className="space-y-1.5 pt-1">
            <span className="text-[10px] font-semibold text-purple-300 uppercase">
              Recorded Field Verifications ({verifications.length}):
            </span>
            {verifications.map((v) => (
              <div key={v.verification_id} className="bg-slate-900/80 p-2 rounded border border-purple-900/50 text-[11px] text-purple-200 space-y-0.5">
                <div className="flex justify-between font-bold text-purple-300">
                  <span>{v.verification_method}</span>
                  <span className="font-mono text-[10px]">{v.timestamp.slice(0, 10)}</span>
                </div>
                <p>{v.observation}</p>
                <div className="text-[9px] text-purple-400">By: {v.reviewer}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Review Status Decision Section */}
      <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-3">
        <h4 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-[#2D5016]" />
          <span>REVIEW DECISION & STATUS</span>
        </h4>

        <div className="space-y-2">
          <div>
            <label className="text-[10px] text-[#8A8A8A] font-semibold block mb-1">
              Set Review Status:
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as ReviewStatus)}
              className="w-full bg-white border border-[#E8E0D0] text-[#2C2C2C] rounded px-2.5 py-1.5 text-xs font-semibold"
            >
              <option value="OPEN">OPEN</option>
              <option value="IN_REVIEW">IN REVIEW</option>
              <option value="FIELD_VERIFICATION_REQUIRED">FIELD VERIFICATION REQUIRED</option>
              <option value="ACCEPTED">ACCEPTED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] text-[#8A8A8A] font-semibold block mb-1">
              Reviewer Notes / Rationale:
            </label>
            <textarea
              value={reviewerNotes}
              onChange={(e) => setReviewerNotes(e.target.value)}
              placeholder="Record technical findings, evidence verification notes..."
              className="w-full bg-white border border-[#E8E0D0] text-[#2C2C2C] rounded px-2.5 py-1.5 text-xs h-16"
            />
          </div>

          <button
            onClick={handleStatusUpdate}
            className="w-full py-1.5 bg-[#2D5016] hover:bg-[#234010] text-white font-medium text-xs rounded transition-colors flex items-center justify-center gap-1.5 shadow-xs"
          >
            <FileCheck className="w-3.5 h-3.5" />
            Save Review Decision
          </button>
        </div>
      </section>

      {/* Audit Trail Timeline */}
      <section className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
        <h4 className="text-[10px] font-bold text-[#8A8A8A] uppercase tracking-wider flex items-center gap-1.5">
          <History className="w-3.5 h-3.5 text-[#2D5016]" />
          <span>AUDIT TRAIL LOG</span>
        </h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {auditTrail.map((audit) => (
            <div key={audit.audit_id} className="bg-white p-2 rounded border border-[#E8E0D0] space-y-1 text-[10px]">
              <div className="flex justify-between font-bold text-[#2C2C2C]">
                <span>{audit.action}</span>
                <span className="font-mono text-[#8A8A8A]">{audit.timestamp.slice(0, 16).replace("T", " ")}</span>
              </div>
              <div className="text-[#6B6B6B]">
                Status: <span className="font-semibold text-cyan-800">{audit.previous_status}</span> → <span className="font-semibold text-emerald-800">{audit.new_status}</span>
              </div>
              {audit.notes && <p className="text-[#2C2C2C] italic">{audit.notes}</p>}
              <div className="text-[9px] text-[#8A8A8A]">By: {audit.reviewer}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
