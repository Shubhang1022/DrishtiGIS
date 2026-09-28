"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/Context";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
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
          Authenticating DrishtiGIS session...
        </p>
      </div>
    );
  }

  if (!token) {
    return null;
  }

  return <>{children}</>;
}
