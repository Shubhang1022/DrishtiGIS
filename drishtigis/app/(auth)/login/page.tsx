"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Lock, Mail, ArrowRight, ShieldCheck, UserCheck } from "lucide-react";
import { useAuth } from "@/lib/auth/Context";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect");
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDemoSelect = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await login(email, password);
      let safeDestination = "/app/map";
      if (redirectParam && redirectParam.startsWith("/") && !redirectParam.startsWith("//")) {
        safeDestination = redirectParam;
      }
      router.push(safeDestination);
    } catch (err: any) {
      setError(err.message || "Invalid email or password. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col justify-between p-4 font-sans selection:bg-[#2D5016] selection:text-[#FBF9F5]">
      
      {/* Top Header */}
      <header className="max-w-7xl mx-auto w-full flex items-center justify-between py-2">
        <Link href="/" className="inline-flex items-center gap-2 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Home</span>
        </Link>
      </header>

      {/* Auth Card */}
      <main className="flex-1 flex items-center justify-center py-12">
        <div className="w-full max-w-md bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 sm:p-8 shadow-panel space-y-6">
          
          {/* Brand */}
          <div className="text-center space-y-2">
            <div className="w-10 h-10 rounded-xl bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center font-bold mx-auto shadow-md">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-display font-bold text-[#2D5016]">
              Sign In to DrishtiGIS
            </h1>
            <p className="text-xs text-[#6B6B6B]">
              Role-Based Multi-User Geospatial Intelligence Platform (SIH26012)
            </p>
          </div>

          {/* Quick Demo Account Selector */}
          <div className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-xl p-3 space-y-2">
            <div className="text-[10px] font-bold text-[#2D5016] uppercase tracking-wider flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5" />
              <span>Select SIH Demo Evaluation Account:</span>
            </div>
            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              <button
                type="button"
                onClick={() => handleDemoSelect("demo-public@drishtigis.in", "Public123!")}
                className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] p-1.5 rounded text-left"
              >
                <div className="font-bold text-[#2C2C2C]">Public Citizen</div>
                <div className="text-[9px] text-[#8A8A8A]">Read-only public data</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoSelect("demo-surveyor@drishtigis.in", "Surveyor123!")}
                className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] p-1.5 rounded text-left"
              >
                <div className="font-bold text-[#2D5016]">Field Surveyor</div>
                <div className="text-[9px] text-[#8A8A8A]">Geometry editing</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoSelect("demo-reviewer@drishtigis.in", "Reviewer123!")}
                className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] p-1.5 rounded text-left"
              >
                <div className="font-bold text-amber-900">Reviewer / Approver</div>
                <div className="text-[9px] text-[#8A8A8A]">Approve/reject edits</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoSelect("demo-admin@drishtigis.in", "Admin123!")}
                className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] p-1.5 rounded text-left"
              >
                <div className="font-bold text-rose-900">System Admin</div>
                <div className="text-[9px] text-[#8A8A8A]">Full governance</div>
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-[#8A8A8A]" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@organization.gov.in"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-[#8A8A8A]" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#2D5016] hover:bg-[#3A6B1E] disabled:opacity-50 text-[#FBF9F5] font-semibold text-xs py-2.5 rounded-lg transition-all shadow-sm flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>Authenticating…</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Footer Link */}
          <div className="text-center text-xs text-[#6B6B6B] border-t border-[#E8E0D0] pt-4">
            Don't have an account?{" "}
            <Link href="/register" className="font-semibold text-[#2D5016] hover:underline">
              Register Organization
            </Link>
          </div>

        </div>
      </main>

      {/* Footer */}
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F7F3EC] flex items-center justify-center text-xs text-[#8A8A8A]">Loading login screen...</div>}>
      <LoginForm />
    </Suspense>
  );
}
