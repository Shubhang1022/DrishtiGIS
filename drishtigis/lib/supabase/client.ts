/**
 * DrishtiGIS — Supabase Client Configuration
 * ============================================
 * Official Supabase JavaScript client for real-user authentication and session management.
 * 
 * SECURITY RULES:
 * - Only uses NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.
 * - NEVER exposes backend service role keys to the browser.
 * - Gracefully handles unconfigured environment variables during SSR / build time.
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _supabaseInstance: SupabaseClient | null = null;

export function getSupabaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    ""
  ).trim();
}

export function getSupabaseAnonKey(): string {
  return (
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    ""
  ).trim();
}

export function isSupabaseConfigured(): boolean {
  const url = getSupabaseUrl();
  const key = getSupabaseAnonKey();
  return Boolean(url && key && url.startsWith("http"));
}

/**
 * Returns the singleton Supabase client instance.
 * Returns null if Supabase environment variables are not configured.
 */
export function getSupabase(): SupabaseClient | null {
  if (typeof window === "undefined") {
    // Server-side / static generation safe instantiation
    const url = getSupabaseUrl();
    const key = getSupabaseAnonKey();
    if (!url || !key) return null;
    return createClient(url, key, {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    });
  }

  if (!_supabaseInstance) {
    const url = getSupabaseUrl();
    const key = getSupabaseAnonKey();
    if (!url || !key) return null;

    _supabaseInstance = createClient(url, key, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: "drishtigis_sb_auth",
      },
    });
  }

  return _supabaseInstance;
}

export const supabase = getSupabase();
