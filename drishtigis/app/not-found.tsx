import Link from "next/link";
import { 
  MapPinOff, 
  Compass, 
  ArrowLeft, 
  Home, 
  Map as MapIcon, 
  User, 
  Search,
  ShieldCheck,
  FileSpreadsheet,
  Bot
} from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col justify-between p-6 font-sans selection:bg-[#2D5016] selection:text-[#FBF9F5]">
      
      {/* Header */}
      <header className="max-w-7xl mx-auto w-full flex items-center justify-between py-4">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center font-bold shadow-xs group-hover:bg-[#3A6B1E] transition-colors">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
          </div>
          <div className="flex flex-col">
            <span className="font-display font-bold text-lg text-[#2D5016] tracking-tight leading-none">
              DrishtiGIS
            </span>
            <span className="text-[10px] text-[#6B6B6B] font-medium tracking-wide mt-0.5">
              Geospatial Intelligence Platform
            </span>
          </div>
        </Link>

        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Landing</span>
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="w-full max-w-xl bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-8 sm:p-10 shadow-lg text-center space-y-6">
          
          {/* Animated MapPinOff Icon */}
          <div className="relative w-20 h-20 mx-auto">
            <div className="absolute inset-0 rounded-full bg-[#2D5016]/10 animate-ping opacity-25" />
            <div className="relative w-20 h-20 rounded-2xl bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center shadow-md mx-auto">
              <MapPinOff className="w-10 h-10" />
            </div>
          </div>

          {/* Title & Description */}
          <div className="space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-100 text-rose-800 text-[11px] font-bold uppercase tracking-wider">
              <Compass className="w-3.5 h-3.5" />
              <span>404 — Coordinates Out of Bounds</span>
            </div>

            <h1 className="text-3xl font-display font-bold text-[#2D5016] tracking-tight">
              You’ve Navigated Beyond the Map Grid
            </h1>

            <p className="text-xs text-[#6B6B6B] leading-relaxed max-w-md mx-auto">
              The requested geospatial route or resource does not exist on our server or may have been relocated. Verify the target address or navigate back to safety.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link
              href="/app/map"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[#2D5016] hover:bg-[#3A6B1E] text-[#FBF9F5] text-xs font-semibold px-6 py-2.5 rounded-xl transition-all shadow-sm"
            >
              <MapIcon className="w-4 h-4" />
              <span>Open WebGIS Workspace</span>
            </Link>

            <Link
              href="/"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[#F7F3EC] hover:bg-[#E8E0D0] text-[#2C2C2C] text-xs font-semibold px-6 py-2.5 rounded-xl border border-[#E8E0D0] transition-all"
            >
              <Home className="w-4 h-4" />
              <span>Return Home</span>
            </Link>
          </div>

          {/* Helpful Destination Quick Links */}
          <div className="border-t border-[#E8E0D0] pt-6 space-y-3">
            <div className="text-[11px] font-bold text-[#2D5016] uppercase tracking-wider text-left">
              Popular Destinations:
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-left">
              <Link
                href="/app/map"
                className="bg-[#F7F3EC] hover:border-[#2D5016] border border-[#E8E0D0] p-2.5 rounded-lg flex items-center gap-2 group transition-all"
              >
                <MapIcon className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="text-[11px] font-medium group-hover:text-[#2D5016]">WebGIS Map</span>
              </Link>

              <Link
                href="/app/profile"
                className="bg-[#F7F3EC] hover:border-[#2D5016] border border-[#E8E0D0] p-2.5 rounded-lg flex items-center gap-2 group transition-all"
              >
                <User className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="text-[11px] font-medium group-hover:text-[#2D5016]">User Profile</span>
              </Link>

              <Link
                href="/app/assistant"
                className="bg-[#F7F3EC] hover:border-[#2D5016] border border-[#E8E0D0] p-2.5 rounded-lg flex items-center gap-2 group transition-all"
              >
                <Bot className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="text-[11px] font-medium group-hover:text-[#2D5016]">AI Assistant</span>
              </Link>

              <Link
                href="/app/exports"
                className="bg-[#F7F3EC] hover:border-[#2D5016] border border-[#E8E0D0] p-2.5 rounded-lg flex items-center gap-2 group transition-all"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="text-[11px] font-medium group-hover:text-[#2D5016]">Data Exports</span>
              </Link>

              <Link
                href="/admin"
                className="bg-[#F7F3EC] hover:border-[#2D5016] border border-[#E8E0D0] p-2.5 rounded-lg flex items-center gap-2 group transition-all"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="text-[11px] font-medium group-hover:text-[#2D5016]">Admin Panel</span>
              </Link>

              <Link
                href="/login"
                className="bg-[#F7F3EC] hover:border-[#2D5016] border border-[#E8E0D0] p-2.5 rounded-lg flex items-center gap-2 group transition-all"
              >
                <Search className="w-3.5 h-3.5 text-[#2D5016]" />
                <span className="text-[11px] font-medium group-hover:text-[#2D5016]">Account Login</span>
              </Link>
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto w-full text-center py-4 text-[11px] text-[#6B6B6B] border-t border-[#E8E0D0]">
        DrishtiGIS Platform (SIH26012) — Powered by High-Resolution Aerial Imagery & AI Cadastral Intelligence
      </footer>

    </div>
  );
}
