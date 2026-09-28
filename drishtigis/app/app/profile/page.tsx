"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  User, 
  Phone, 
  Home, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  ArrowLeft,
  Eye,
  EyeOff,
  UserCheck,
  Building2,
  Plus,
  Trash2,
  MapPin,
  Move
} from "lucide-react";
import { useAuth } from "@/lib/auth/Context";
import { fetchUserProfile, saveUserProfile, type UserProfileData } from "@/lib/api/userProfile";
import { fetchUserProperties, createUserProperty, deleteUserProperty, type UserPropertyData } from "@/lib/api/userProperties";

export default function ProfilePage() {
  const { user, token } = useAuth();

  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form Fields
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [houseNumber, setHouseNumber] = useState("");
  const [streetLocality, setStreetLocality] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [pincode, setPincode] = useState("");
  const [organization, setOrganization] = useState("");
  const [showNamePublicly, setShowNamePublicly] = useState(false);
  const [showAddressPublicly, setShowAddressPublicly] = useState(false);
  const [showPhonePublicly, setShowPhonePublicly] = useState(false);

  // Registered User Properties state
  const [myProperties, setMyProperties] = useState<UserPropertyData[]>([]);
  const [showAddPropModal, setShowAddPropModal] = useState(false);
  const [newPropTitle, setNewPropTitle] = useState("");
  const [newPropType, setNewPropType] = useState("house");
  const [newPropHouseNo, setNewPropHouseNo] = useState("");
  const [newPropLocality, setNewPropLocality] = useState("");
  const [newPropDesc, setNewPropDesc] = useState("");
  const [newPropLat, setNewPropLat] = useState("23.259933");
  const [newPropLon, setNewPropLon] = useState("77.412613");
  const [newPropIsPublic, setNewPropIsPublic] = useState(false);
  const [propSaving, setPropSaving] = useState(false);

  useEffect(() => {
    if (token) {
      setLoading(true);
      fetchUserProfile(token).then((data) => {
        if (data) {
          setProfile(data);
          setFullName(data.full_name || user?.name || "");
          setPhoneNumber(data.phone_number || "");
          setHouseNumber(data.house_number || "");
          setStreetLocality(data.street_locality || "");
          setCity(data.city || user?.city || "");
          setState(data.state || user?.state || "");
          setPincode(data.pincode || "");
          setOrganization(data.organization || user?.organization || "");
          setShowNamePublicly(Boolean(data.show_name_publicly));
          setShowAddressPublicly(Boolean(data.show_address_publicly));
          setShowPhonePublicly(Boolean(data.show_phone_publicly));
        }
        setLoading(false);
      });

      fetchUserProperties(token).then((props) => {
        setMyProperties(props);
      });
    }
  }, [token, user]);

  const handleDisableAllVisibility = () => {
    setShowNamePublicly(false);
    setShowAddressPublicly(false);
    setShowPhonePublicly(false);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const updated = await saveUserProfile(token, {
        full_name: fullName,
        phone_number: phoneNumber,
        house_number: houseNumber,
        street_locality: streetLocality,
        city,
        state,
        pincode,
        organization,
        show_name_publicly: showNamePublicly,
        show_address_publicly: showAddressPublicly,
        show_phone_publicly: showPhonePublicly,
      });
      setProfile(updated);
      setSuccessMsg("User profile details updated successfully!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save profile details");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setPropSaving(true);
    try {
      const created = await createUserProperty(token, {
        title: newPropTitle || "My Property",
        property_type: newPropType,
        house_number: newPropHouseNo,
        street_locality: newPropLocality,
        description: newPropDesc,
        latitude: parseFloat(newPropLat) || 23.259933,
        longitude: parseFloat(newPropLon) || 77.412613,
        is_public: newPropIsPublic,
        show_name_publicly: showNamePublicly,
        show_address_publicly: showAddressPublicly,
        show_phone_publicly: showPhonePublicly,
        phone_number: phoneNumber,
      });
      setMyProperties((prev) => [...prev, created]);
      setShowAddPropModal(false);
      setNewPropTitle("");
      setNewPropHouseNo("");
      setNewPropLocality("");
      setNewPropDesc("");
    } catch (err: any) {
      alert(err.message || "Failed to register property");
    } finally {
      setPropSaving(false);
    }
  };

  const handleDeleteProp = async (propId: string) => {
    if (!token) return;
    if (confirm("Are you sure you want to delete this property marker?")) {
      const ok = await deleteUserProperty(token, propId);
      if (ok) {
        setMyProperties((prev) => prev.filter((p) => p.id !== propId));
      }
    }
  };

  // Compute profile completion percentage
  const fields = [fullName, phoneNumber, houseNumber, streetLocality, city, state, pincode, organization];
  const filledFields = fields.filter((f) => f && f.trim().length > 0).length;
  const completionPct = Math.round((filledFields / fields.length) * 100);

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans selection:bg-[#2D5016] selection:text-white">
      
      {/* Top Header */}
      <header className="h-14 bg-[#FBF9F5] border-b border-[#E8E0D0] px-6 flex items-center justify-between shadow-xs shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/app/map" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Map Workspace</span>
          </Link>
          <span className="text-[#8A8A8A] text-xs">/</span>
          <span className="font-display font-bold text-sm text-[#2C2C2C]">My Profile Dashboard</span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-0.5 rounded bg-[#EDE8DE] border border-[#E8E0D0] font-mono font-bold text-[#2D5016]">
            {user?.role || "USER"}
          </span>
          <span className="text-[#8A8A8A] hidden sm:inline">{user?.email}</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-8 space-y-6">
        
        {/* Title & Status Bar */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center font-bold text-xl shadow-md">
              {user?.name ? user.name.charAt(0).toUpperCase() : "U"}
            </div>
            <div>
              <h1 className="font-display font-bold text-xl text-[#2C2C2C]">{user?.name || "Authenticated User"}</h1>
              <p className="text-xs text-[#6B6B6B] flex items-center gap-1.5 mt-0.5">
                <UserCheck className="w-3.5 h-3.5 text-[#2D5016]" />
                <span>Account ID: <code className="font-mono text-[11px]">{user?.user_id}</code></span>
              </p>
            </div>
          </div>

          <div className="sm:text-right space-y-1 bg-[#F7F3EC] p-3 rounded-xl border border-[#E8E0D0]">
            <div className="flex items-center gap-2 justify-between sm:justify-end text-xs font-semibold text-[#2C2C2C]">
              <span>Profile Completion</span>
              <span className="text-[#2D5016] font-bold font-mono">{completionPct}%</span>
            </div>
            <div className="w-44 h-2 bg-[#E8E0D0] rounded-full overflow-hidden">
              <div 
                className="h-full bg-[#2D5016] transition-all duration-500 rounded-full"
                style={{ width: `${completionPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        {successMsg && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl p-3.5 text-xs flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-3.5 text-xs flex items-center gap-2 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Live Public Map Feature Preview Box */}
        <div className="bg-[#EDE8DE] border border-[#E8E0D0] rounded-2xl p-4 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-[#2C2C2C] flex items-center gap-1.5">
              <Eye className="w-4 h-4 text-[#2D5016]" />
              <span>Public Map Feature Information Preview (What Other Users Can See)</span>
            </span>
            <button
              type="button"
              onClick={handleDisableAllVisibility}
              className="px-2.5 py-1 text-[11px] font-semibold bg-rose-100 hover:bg-rose-200 text-rose-800 border border-rose-300 rounded-lg transition-colors"
            >
              Disable All Public Visibility
            </button>
          </div>
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl p-3 text-[11px] font-mono space-y-1">
            <p className="font-bold text-[#2D5016]">PROPERTY / MAP FEATURE CARD</p>
            <p className="text-[#6B6B6B]">&bull; Building ID: <span className="text-[#2C2C2C]">BLD-BPL-00834</span> (AI Feature)</p>
            <p className="text-[#6B6B6B]">&bull; Resident Name: <span className="text-[#2C2C2C]">{showNamePublicly ? (fullName || user?.name || "Not Specified") : "[PRIVATE — Opt-in OFF]"}</span></p>
            <p className="text-[#6B6B6B]">&bull; Property Address: <span className="text-[#2C2C2C]">{showAddressPublicly ? ([houseNumber, streetLocality, city, state].filter(Boolean).join(", ") || "Not Specified") : "[PRIVATE — Opt-in OFF]"}</span></p>
            <p className="text-[#6B6B6B]">&bull; Contact Method: <span className="text-[#2C2C2C]">{showPhonePublicly ? (phoneNumber || "Not Specified") : "[PRIVATE — Opt-in OFF]"}</span></p>
          </div>
        </div>

        {/* Section: My Registered Properties */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#E8E0D0] pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-[#2D5016]" />
              <h2 className="font-display font-bold text-sm text-[#2C2C2C]">My Registered Map Properties</h2>
            </div>
            <button
              type="button"
              onClick={() => setShowAddPropModal(true)}
              className="bg-[#2D5016] hover:bg-[#3A6B1E] text-white px-3 py-1.5 rounded-xl font-semibold text-xs transition-all flex items-center gap-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Property</span>
            </button>
          </div>

          {myProperties.length === 0 ? (
            <div className="text-center py-6 bg-[#F7F3EC] rounded-xl border border-[#E8E0D0] text-xs text-[#8A8A8A]">
              No user properties registered yet. Click <strong>"Add Property"</strong> to map your house or building.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {myProperties.map((prop) => (
                <div key={prop.id} className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3.5 space-y-2 relative">
                  <div className="flex items-center justify-between font-bold text-[#2C2C2C]">
                    <span className="flex items-center gap-1 text-[#2D5016]">
                      <MapPin className="w-3.5 h-3.5 text-[#2D5016]" />
                      <span>{prop.title}</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDeleteProp(prop.id)}
                      className="text-rose-600 hover:text-rose-800 p-1"
                      title="Delete property"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="text-[11px] text-[#6B6B6B] space-y-0.5">
                    <p>Type: <span className="font-semibold text-[#2C2C2C] uppercase">{prop.property_type}</span></p>
                    <p>Address: {[prop.house_number, prop.street_locality, prop.city].filter(Boolean).join(", ") || "N/A"}</p>
                    <p className="font-mono text-[10px]">Coordinates: {prop.latitude.toFixed(5)}, {prop.longitude.toFixed(5)}</p>
                    <p className="text-[10px] text-[#7C3AED] font-semibold mt-1">
                      {prop.is_public ? "🌐 Publicly Shared Marker" : "🔒 Private Marker (Owner Only)"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal: Add Property */}
        {showAddPropModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
            <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 font-sans text-xs">
              <div className="flex items-center justify-between border-b border-[#E8E0D0] pb-3">
                <span className="font-display font-bold text-sm text-[#2D5016] flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" />
                  <span>Register User Property on Map</span>
                </span>
                <button
                  onClick={() => setShowAddPropModal(false)}
                  className="text-[#8A8A8A] hover:text-[#2C2C2C] font-bold text-sm"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateProperty} className="space-y-3">
                <div>
                  <label className="font-semibold text-[#2C2C2C] block mb-1">Property Label / Name</label>
                  <input
                    type="text"
                    required
                    value={newPropTitle}
                    onChange={(e) => setNewPropTitle(e.target.value)}
                    placeholder="e.g. My Family Residence / Office Building"
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-[#2C2C2C] block mb-1">Property Type</label>
                    <select
                      value={newPropType}
                      onChange={(e) => setNewPropType(e.target.value)}
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                    >
                      <option value="house">House / Residential</option>
                      <option value="building">Building / Commercial</option>
                      <option value="vacant_plot">Vacant Plot</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-semibold text-[#2C2C2C] block mb-1">House Number</label>
                    <input
                      type="text"
                      value={newPropHouseNo}
                      onChange={(e) => setNewPropHouseNo(e.target.value)}
                      placeholder="e.g. H.No 42"
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-[#2C2C2C] block mb-1">Street / Locality</label>
                  <input
                    type="text"
                    value={newPropLocality}
                    onChange={(e) => setNewPropLocality(e.target.value)}
                    placeholder="e.g. Arera Colony, Bhopal"
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-[#2C2C2C] block mb-1">Latitude</label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={newPropLat}
                      onChange={(e) => setNewPropLat(e.target.value)}
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs font-mono text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-[#2C2C2C] block mb-1">Longitude</label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={newPropLon}
                      onChange={(e) => setNewPropLon(e.target.value)}
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs font-mono text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                    />
                  </div>
                </div>

                <div className="bg-[#E8E0D0]/30 border border-[#E8E0D0] rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-[#2C2C2C]">Make Property Visible on Public Map</span>
                    <p className="text-[10px] text-[#6B6B6B]">Default is Private (Owner only).</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={newPropIsPublic}
                    onChange={(e) => setNewPropIsPublic(e.target.checked)}
                    className="accent-[#2D5016] w-4 h-4 cursor-pointer rounded"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddPropModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-[#6B6B6B]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={propSaving}
                    className="bg-[#2D5016] hover:bg-[#3A6B1E] text-white px-5 py-2 rounded-xl font-semibold text-xs transition-all shadow-xs"
                  >
                    {propSaving ? "Saving..." : "Save Property"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Profile Form */}
        <form onSubmit={handleSave} className="space-y-6">
          
          {/* Section 1: Personal Details */}
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-[#E8E0D0] pb-3">
              <User className="w-4 h-4 text-[#2D5016]" />
              <h2 className="font-display font-bold text-sm text-[#2C2C2C]">Personal & Identity Information</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Rajesh Kumar"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">Organization / Department</label>
                <input
                  type="text"
                  value={organization}
                  onChange={(e) => setOrganization(e.target.value)}
                  placeholder="e.g. Dept of Revenue / Land Records"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">Phone Number</label>
                <div className="relative">
                  <Phone className="w-4 h-4 absolute left-3 top-2.5 text-[#8A8A8A]" />
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl pl-9 pr-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                  />
                </div>
              </div>

              {/* 3-Tier Privacy Opt-In Controls */}
              <div className="sm:col-span-2 bg-[#E8E0D0]/30 border border-[#E8E0D0] rounded-xl p-4 space-y-3">
                <div className="font-bold text-xs text-[#2C2C2C] border-b border-[#E8E0D0] pb-1.5 flex items-center gap-1.5">
                  <EyeOff className="w-4 h-4 text-[#7C3AED]" />
                  <span>Granular Public Map Privacy Controls (All Default: OFF / Private)</span>
                </div>

                {/* 1. Name Opt-in */}
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-[#2C2C2C]">Show Full Name on Mapped Property</span>
                    <p className="text-[10px] text-[#6B6B6B]">Allows your full name to display when users select your building on the map.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer ml-3">
                    <input
                      type="checkbox"
                      checked={showNamePublicly}
                      onChange={(e) => setShowNamePublicly(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-[#E8E0D0] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#7C3AED]"></div>
                  </label>
                </div>

                {/* 2. Address Opt-in */}
                <div className="flex items-center justify-between text-xs border-t border-[#E8E0D0]/60 pt-2">
                  <div>
                    <span className="font-bold text-[#2C2C2C]">Show House & Street Address on Map</span>
                    <p className="text-[10px] text-[#6B6B6B]">Allows your house number and locality to display on mapped properties.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer ml-3">
                    <input
                      type="checkbox"
                      checked={showAddressPublicly}
                      onChange={(e) => setShowAddressPublicly(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-[#E8E0D0] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#7C3AED]"></div>
                  </label>
                </div>

                {/* 3. Phone Opt-in */}
                <div className="flex items-center justify-between text-xs border-t border-[#E8E0D0]/60 pt-2">
                  <div>
                    <span className="font-bold text-[#2C2C2C]">Show Phone Number Contact Method</span>
                    <p className="text-[10px] text-[#6B6B6B]">Allows your phone number to display as a contact method on mapped properties.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer ml-3">
                    <input
                      type="checkbox"
                      checked={showPhonePublicly}
                      onChange={(e) => setShowPhonePublicly(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-[#E8E0D0] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#7C3AED]"></div>
                  </label>
                </div>

              </div>
            </div>
          </div>

          {/* Section 2: Residence & Postal Address */}
          <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-[#E8E0D0] pb-3">
              <Home className="w-4 h-4 text-[#2D5016]" />
              <h2 className="font-display font-bold text-sm text-[#2C2C2C]">Residence & Postal Address Details</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">House / Flat / Building No.</label>
                <input
                  type="text"
                  value={houseNumber}
                  onChange={(e) => setHouseNumber(e.target.value)}
                  placeholder="e.g. H.No. 42 / Flat 301"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">Street / Locality / Landmark</label>
                <input
                  type="text"
                  value={streetLocality}
                  onChange={(e) => setStreetLocality(e.target.value)}
                  placeholder="e.g. Arera Colony, Ward 12"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">City</label>
                <input
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="e.g. Bhopal"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-[#2C2C2C]">State</label>
                <input
                  type="text"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  placeholder="e.g. Madhya Pradesh"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>

              <div className="space-y-1 sm:col-span-2">
                <label className="font-semibold text-[#2C2C2C]">PIN Code</label>
                <input
                  type="text"
                  value={pincode}
                  onChange={(e) => setPincode(e.target.value)}
                  placeholder="e.g. 462016"
                  className="w-full sm:w-1/2 bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
                />
              </div>
            </div>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-2">
            <Link
              href="/app/map"
              className="text-xs font-semibold text-[#6B6B6B] hover:text-[#2C2C2C] px-3 py-2"
            >
              Cancel
            </Link>

            <button
              type="submit"
              disabled={saving || loading}
              className="bg-[#2D5016] hover:bg-[#3A6B1E] text-white px-6 py-2.5 rounded-xl font-semibold text-xs shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Saving Profile...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Profile Details</span>
                </>
              )}
            </button>
          </div>

        </form>

      </main>

    </div>
  );
}
