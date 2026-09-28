"use client";

import React, { useState } from "react";
import { MapPin, ShieldCheck, Compass, AlertCircle, X } from "lucide-react";

interface LocationConsentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConsentGranted: (coords: { latitude: number; longitude: number; accuracy: number }) => void;
  onManualSelect: () => void;
}

export function LocationConsentModal({
  isOpen,
  onClose,
  onConsentGranted,
  onManualSelect,
}: LocationConsentModalProps) {
  const [requesting, setRequesting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRequestLocation = () => {
    setErrorMsg(null);
    if (!navigator.geolocation) {
      setErrorMsg("Browser geolocation is not supported on this device/browser.");
      return;
    }

    setRequesting(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setRequesting(false);
        onConsentGranted({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        onClose();
      },
      (err) => {
        setRequesting(false);
        if (err.code === err.PERMISSION_DENIED) {
          setErrorMsg("Location permission was denied. You can manually enter or click a location anytime.");
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          setErrorMsg("Current position is unavailable. Please check device location settings.");
        } else if (err.code === err.TIMEOUT) {
          setErrorMsg("Location request timed out. Please try again or select manually.");
        } else {
          setErrorMsg("Failed to obtain device location.");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs font-sans">
      <div className="max-w-md w-full bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-2xl space-y-5 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8A8A8A] hover:text-[#2C2C2C] p-1 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#7C3AED]/10 text-[#7C3AED] flex items-center justify-center font-bold shadow-xs">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display font-bold text-lg text-[#2C2C2C]">
              Device Location Request
            </h2>
            <p className="text-xs text-[#6B6B6B]">Explicit User Consent Required</p>
          </div>
        </div>

        <div className="bg-[#E8E0D0]/30 border border-[#E8E0D0] rounded-xl p-3.5 space-y-2">
          <div className="flex items-start gap-2 text-xs text-[#2C2C2C]">
            <ShieldCheck className="w-4 h-4 text-[#2D5016] shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              DrishtiGIS can use your device location to center the map and optionally save a private <strong>HOME</strong> marker. Your location is <strong>never</strong> used to establish property ownership or legal boundaries.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="bg-amber-500/10 border border-amber-500/30 text-amber-800 rounded-xl p-3 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <p>{errorMsg}</p>
          </div>
        )}

        <div className="space-y-2 pt-1">
          <button
            onClick={handleRequestLocation}
            disabled={requesting}
            className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all disabled:opacity-50"
          >
            {requesting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Requesting Location...</span>
              </>
            ) : (
              <>
                <MapPin className="w-4 h-4" />
                <span>Use My Location</span>
              </>
            )}
          </button>

          <button
            onClick={() => {
              onClose();
              onManualSelect();
            }}
            className="w-full bg-[#F5EFE6] hover:bg-[#E8E0D0] text-[#2C2C2C] py-2 px-4 rounded-xl text-xs font-semibold transition-colors"
          >
            Enter Location Manually
          </button>

          <button
            onClick={onClose}
            className="w-full text-center text-xs text-[#8A8A8A] hover:text-[#2C2C2C] py-1.5 transition-colors"
          >
            Not Now
          </button>
        </div>
      </div>
    </div>
  );
}
