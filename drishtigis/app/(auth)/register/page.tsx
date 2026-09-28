"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Lock, Mail, User, Building, ArrowRight, AlertCircle } from "lucide-react";
import { useAuth } from "@/lib/auth/Context";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [org, setOrg] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register({
        name,
        email,
        organization: org,
        password,
        role: "SURVEYOR", // Default requested role
      });
      router.push("/app/map");
    } catch (err: any) {
      setError(err.message || "Registration failed. Please check your credentials.");
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
        <div className="w-full max-w-sm bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 sm:p-8 shadow-panel space-y-6">
          
          {/* Brand */}
          <div className="text-center space-y-2">
            <div className="w-10 h-10 rounded-xl bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center font-bold mx-auto shadow-md">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
              </svg>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#2D5016]">
              Request Access
            </h1>
            <p className="text-xs text-[#6B6B6B]">
              Register for institutional WebGIS property intelligence.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3 top-3 text-[#8A8A8A]" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Officer / Researcher Name"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Official Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-[#8A8A8A]" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@agency.gov.in"
                  className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#2C2C2C] block">
                Organization / Department
              </label>
              <div className="relative">
                <Building className="w-4 h-4 absolute left-3 top-3 text-[#8A8A8A]" />
                <input
                  type="text"
                  required
                  value={org}
                  onChange={(e) => setOrg(e.target.value)}
                  placeholder="Urban Development / Municipal Corp"
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
              className="w-full bg-[#2D5016] hover:bg-[#3A6B1E] text-[#FBF9F5] font-semibold text-xs py-2.5 rounded-lg transition-all shadow-sm flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
            >
              {loading ? (
                <span>Registering Account…</span>
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Footer Link */}
          <div className="text-center text-xs text-[#6B6B6B] border-t border-[#E8E0D0] pt-4">
            Already registered?{" "}
            <Link href="/login" className="font-semibold text-[#2D5016] hover:underline">
              Sign In
            </Link>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-[11px] text-[#8A8A8A] py-2">
        DrishtiGIS &nbsp;&middot;&nbsp; SIH26012 &nbsp;&middot;&nbsp; Smart India Hackathon
      </footer>

    </div>
  );
}
