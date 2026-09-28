"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { useAuth } from "@/lib/auth/Context";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !token) {
      const redirectUrl = `/login?redirect=${encodeURIComponent(pathname)}`;
      router.replace(redirectUrl);
    }
  }, [token, loading, pathname, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F3EC] flex flex-col items-center justify-center p-4">
        <div className="w-10 h-10 border-3 border-[#2D5016] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-semibold text-[#2D5016] font-sans">
          Verifying administrative authorization...
        </p>
      </div>
    );
  }

  if (!token) {
    return null;
  }

  if (user?.role !== "ADMIN") {
    return (
      <div className="min-h-screen bg-[#F7F3EC] flex items-center justify-center p-4 font-sans">
        <div className="max-w-md w-full bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 sm:p-8 shadow-panel text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-red-500/10 text-red-600 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-[#2C2C2C] font-display">
            Access Restricted (403 Forbidden)
          </h1>
          <p className="text-xs text-[#6B6B6B] leading-relaxed">
            Your current account role (<span className="font-semibold text-[#2C2C2C]">{user?.role || "PUBLIC"}</span>) does not have administrative privileges required to access the DrishtiGIS Admin Console.
          </p>
          <div className="pt-2">
            <Link
              href="/app/map"
              className="inline-flex items-center gap-2 bg-[#2D5016] text-[#FBF9F5] px-4 py-2.5 rounded-xl text-xs font-semibold hover:bg-[#3A6B1E] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to WebGIS Workspace</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
