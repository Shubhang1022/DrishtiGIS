"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Lock,
  Mail,
  User,
  Building,
  MapPin,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Shield,
  Info,
} from "lucide-react";
import { useAuth } from "@/lib/auth/Context";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [org, setOrg] = useState("");
  const [city, setCity] = useState("Bhopal");
  const [state, setState] = useState("Madhya Pradesh");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailSent, setEmailSent] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Phase 16: Public self-registration ALWAYS defaults to PUBLIC role
      const res = await register({
        name,
        email,
        organization: org,
        password,
        city,
        state,
      });

      if (res?.needEmailConfirmation) {
        setEmailSent(true);
        setSuccessMessage(
          res.message ||
            "Account created! Please check your email inbox to verify your address before signing in."
        );
      } else {
        router.push("/app/map");
      }
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
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]"
        >
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
              <Shield className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-display font-bold text-[#2D5016]">
              Create Personal Account
            </h1>
            <p className="text-xs text-[#6B6B6B]">
              Real-user authentication with private, isolated HOME location support.
            </p>
          </div>

          {/* Privacy Notice */}
          <div className="bg-[#EBF3E8] border border-[#C5DEC0] rounded-xl p-3 flex items-start gap-2 text-[11px] text-[#244212]">
            <Info className="w-4 h-4 flex-shrink-0 mt-0.5 text-[#2D5016]" />
            <div>
              <span className="font-semibold">Privacy Guarantee:</span> Personal accounts receive a unique identity. Your saved HOME locations are strictly private and never shared.
            </div>
          </div>

          {/* Email Confirmation Screen */}
          {emailSent ? (
            <div className="space-y-4 py-4 text-center">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-base font-bold text-[#2D5016]">Verification Email Sent</h2>
                <p className="text-xs text-[#6B6B6B] leading-relaxed">
                  {successMessage}
                </p>
              </div>
              <div className="pt-2">
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center gap-2 w-full bg-[#2D5016] hover:bg-[#3A6B1E] text-[#FBF9F5] font-semibold text-xs py-2.5 rounded-lg transition-all"
                >
                  <span>Proceed to Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ) : (
            <>
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
                      placeholder="Officer / Researcher / Citizen Name"
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                    />
                  </div>
                </div>

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
                      placeholder="name@example.com"
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
                      value={org}
                      onChange={(e) => setOrg(e.target.value)}
                      placeholder="e.g. Municipal Corp / Public Citizen"
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[#2C2C2C] block">
                      City
                    </label>
                    <div className="relative">
                      <MapPin className="w-4 h-4 absolute left-3 top-3 text-[#8A8A8A]" />
                      <input
                        type="text"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        placeholder="City"
                        className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[#2C2C2C] block">
                      State
                    </label>
                    <input
                      type="text"
                      value={state}
                      onChange={(e) => setState(e.target.value)}
                      placeholder="State"
                      className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
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
                      minLength={6}
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
                      <span>Create Personal Account</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </form>

              {/* Footer Link */}
              <div className="text-center text-xs text-[#6B6B6B] border-t border-[#E8E0D0] pt-4">
                Already registered or using a demo account?{" "}
                <Link href="/login" className="font-semibold text-[#2D5016] hover:underline">
                  Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-[11px] text-[#8A8A8A] py-2">
        DrishtiGIS &nbsp;&middot;&nbsp; SIH26012 &nbsp;&middot;&nbsp; Smart India Hackathon
      </footer>
    </div>
  );
}
