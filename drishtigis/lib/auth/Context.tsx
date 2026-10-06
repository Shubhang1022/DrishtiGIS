"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, UserRole } from "@/lib/types/auth";
import { loginUser, getCurrentUser } from "@/lib/api/auth";
import { API_V1_BASE } from "@/lib/api/client";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase/client";
import { isDemoEmail } from "@/lib/auth/demoAccounts";

export type AuthProviderType = "supabase" | "demo" | null;

export interface RegisterResult {
  needEmailConfirmation?: boolean;
  message?: string;
  user?: User;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  authProvider: AuthProviderType;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    name: string;
    organization?: string;
    city?: string;
    state?: string;
  }) => Promise<RegisterResult>;
  logout: () => Promise<void>;
  hasRole: (roles: UserRole[]) => boolean;
}

const defaultAuthContext: AuthContextType = {
  user: null,
  token: null,
  loading: false,
  authProvider: null,
  login: async () => {},
  register: async () => ({}),
  logout: async () => {},
  hasRole: (roles: UserRole[]) => roles.includes("PUBLIC"),
};

const AuthContext = createContext<AuthContextType>(defaultAuthContext);

function getCookieToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|; )drishtigis_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookieToken(token: string) {
  if (typeof document !== "undefined") {
    document.cookie = `drishtigis_token=${token}; path=/; max-age=604800; SameSite=Lax`;
  }
}

function clearCookieToken() {
  if (typeof document !== "undefined") {
    document.cookie = "drishtigis_token=; path=/; max-age=0; SameSite=Lax";
    document.cookie = "drishtigis_token=; path=/; max-age=0; SameSite=Strict";
    document.cookie = "drishtigis_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  }
}

function clearLegacyLocationStorage() {
  if (typeof window === "undefined") return;
  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (
        key &&
        (key.startsWith("homeLocation") ||
          key.startsWith("userHome") ||
          key.startsWith("savedHome") ||
          key === "HOME_LOCATION" ||
          key === "home_lat" ||
          key === "home_lng" ||
          key === "lastLocation")
      ) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((k) => localStorage.removeItem(k));
  } catch {}
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [authProvider, setAuthProvider] = useState<AuthProviderType>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Initialize session on mount
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      // 1. First check Supabase session if configured
      if (isSupabaseConfigured()) {
        try {
          const sb = getSupabase();
          if (sb) {
            const { data } = await sb.auth.getSession();
            const session = data?.session;
            if (session && session.access_token) {
              const activeToken = session.access_token;
              try {
                const profile = await getCurrentUser(activeToken);
                if (isMounted) {
                  setUser(profile);
                  setToken(activeToken);
                  setAuthProvider("supabase");
                  setCookieToken(activeToken);
                  setLoading(false);
                  return;
                }
              } catch (profileErr) {
                console.warn("Failed to load DrishtiGIS profile for Supabase user:", profileErr);
              }
            }
          }
        } catch (sbErr) {
          console.warn("Supabase session check failed:", sbErr);
        }
      }

      // 2. Otherwise check existing demo/custom token in localStorage or cookie
      const savedToken =
        (typeof window !== "undefined" ? localStorage.getItem("drishtigis_token") : null) ||
        getCookieToken();

      if (savedToken) {
        try {
          const userData = await getCurrentUser(savedToken);
          if (isMounted) {
            setUser(userData);
            setToken(savedToken);
            setAuthProvider(savedToken.startsWith("sb_") ? "supabase" : "demo");
            setCookieToken(savedToken);
          }
        } catch {
          if (typeof window !== "undefined") {
            localStorage.removeItem("drishtigis_token");
          }
          clearCookieToken();
          clearLegacyLocationStorage();
          if (isMounted) {
            setToken(null);
            setUser(null);
            setAuthProvider(null);
          }
        }
      }

      if (isMounted) {
        setLoading(false);
      }
    }

    initSession();

    // Listen to Supabase Auth state changes
    const sb = getSupabase();
    let authListener: { subscription: { unsubscribe: () => void } } | null = null;
    if (sb) {
      const { data } = sb.auth.onAuthStateChange(async (event, session) => {
        if (!isMounted) return;
        if (event === "SIGNED_OUT") {
          setUser(null);
          setToken(null);
          setAuthProvider(null);
          clearCookieToken();
          clearLegacyLocationStorage();
        } else if ((event === "SIGNED_IN" || event === "TOKEN_REFRESHED") && session) {
          const newToken = session.access_token;
          setToken(newToken);
          setAuthProvider("supabase");
          setCookieToken(newToken);
          try {
            const profile = await getCurrentUser(newToken);
            if (isMounted) setUser(profile);
          } catch {}
        }
      });
      authListener = data;
    }

    return () => {
      isMounted = false;
      if (authListener?.subscription) {
        authListener.subscription.unsubscribe();
      }
    };
  }, []);

  const login = async (email: string, password: string) => {
    clearLegacyLocationStorage();
    const cleanEmail = email.trim();

    // Route A: SIH Demo Evaluation Accounts
    if (isDemoEmail(cleanEmail)) {
      const data = await loginUser(cleanEmail, password);
      setToken(data.access_token);
      setUser(data.user);
      setAuthProvider("demo");
      if (typeof window !== "undefined") {
        localStorage.setItem("drishtigis_token", data.access_token);
      }
      setCookieToken(data.access_token);
      return;
    }

    // Route B: Real Users authenticated through Supabase Auth
    const sb = getSupabase();
    if (!sb || !isSupabaseConfigured()) {
      // If Supabase is not configured yet in this environment, provide actionable feedback
      throw new Error(
        "Supabase Auth is not configured on this frontend. Please use one of the SIH Demo Accounts or configure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY."
      );
    }

    const { data, error } = await sb.auth.signInWithPassword({
      email: cleanEmail,
      password,
    });

    if (error) {
      throw new Error(error.message || "Failed to sign in with email and password.");
    }

    if (!data.session || !data.session.access_token) {
      throw new Error("Login succeeded but no active session was returned. Please check your email for confirmation.");
    }

    const sbToken = data.session.access_token;
    setToken(sbToken);
    setAuthProvider("supabase");
    if (typeof window !== "undefined") {
      localStorage.setItem("drishtigis_token", sbToken);
    }
    setCookieToken(sbToken);

    // Synchronize DrishtiGIS profile
    try {
      const profile = await getCurrentUser(sbToken);
      setUser(profile);
    } catch {
      // If backend profile endpoint is pending or sync in progress, provide safe fallback
      if (data.user) {
        setUser({
          user_id: data.user.id,
          email: data.user.email || cleanEmail,
          name: (data.user.user_metadata?.name as string) || cleanEmail.split("@")[0],
          role: "PUBLIC",
          organization: (data.user.user_metadata?.organization as string) || "DrishtiGIS User",
          country: "India",
          state: (data.user.user_metadata?.state as string) || "Madhya Pradesh",
          city: (data.user.user_metadata?.city as string) || "Bhopal",
          region_id: "bhopal_mp",
          allowed_datasets: ["uavpal_bhopal", "bhopal_synthetic_parcels"],
          is_active: true,
          created_at: data.user.created_at,
        });
      }
    }
  };

  const register = async (formData: {
    email: string;
    password: string;
    name: string;
    organization?: string;
    city?: string;
    state?: string;
  }): Promise<RegisterResult> => {
    clearLegacyLocationStorage();
    const cleanEmail = formData.email.trim();

    const sb = getSupabase();
    if (!sb || !isSupabaseConfigured()) {
      throw new Error(
        "Supabase Auth is not configured. Please configure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY."
      );
    }

    // Phase 16: Public self-registration ALWAYS defaults strictly to PUBLIC role
    const { data, error } = await sb.auth.signUp({
      email: cleanEmail,
      password: formData.password,
      options: {
        data: {
          name: formData.name.trim(),
          organization: (formData.organization || "Independent Citizen").trim(),
          city: (formData.city || "Bhopal").trim(),
          state: (formData.state || "Madhya Pradesh").trim(),
          role: "PUBLIC",
        },
      },
    });

    if (error) {
      throw new Error(error.message || "Registration failed. Please check your details.");
    }

    // Phase 4: Respect Supabase email confirmation configuration
    if (data.user && !data.session) {
      // Supabase requires email verification
      return {
        needEmailConfirmation: true,
        message:
          "Account created successfully! Please check your email inbox to verify your address before signing in.",
      };
    }

    // Immediate session (email confirmation disabled)
    if (data.session && data.session.access_token) {
      const sbToken = data.session.access_token;
      setToken(sbToken);
      setAuthProvider("supabase");
      if (typeof window !== "undefined") {
        localStorage.setItem("drishtigis_token", sbToken);
      }
      setCookieToken(sbToken);

      try {
        const profile = await getCurrentUser(sbToken);
        setUser(profile);
        return { needEmailConfirmation: false, user: profile };
      } catch {
        const userId = data.user?.id || `usr-${Date.now()}`;
        const fallbackUser: User = {
          user_id: userId,
          email: data.user?.email || cleanEmail,
          name: formData.name,
          role: "PUBLIC",
          organization: formData.organization || "Independent Citizen",
          country: "India",
          state: formData.state || "Madhya Pradesh",
          city: formData.city || "Bhopal",
          region_id: "bhopal_mp",
          allowed_datasets: ["uavpal_bhopal", "bhopal_synthetic_parcels"],
          is_active: true,
          created_at: data.user?.created_at || new Date().toISOString(),
        };
        setUser(fallbackUser);
        return { needEmailConfirmation: false, user: fallbackUser };
      }
    }

    return { needEmailConfirmation: false };
  };

  const logout = async () => {
    // 1. Supabase signout
    if (authProvider === "supabase" || isSupabaseConfigured()) {
      try {
        const sb = getSupabase();
        if (sb) {
          await sb.auth.signOut();
        }
      } catch (e) {
        console.warn("Supabase signOut error:", e);
      }
    }

    // 2. DrishtiGIS backend session logout & cookie removal
    const activeToken =
      token ||
      (typeof window !== "undefined" ? localStorage.getItem("drishtigis_token") : null) ||
      getCookieToken();

    if (activeToken) {
      try {
        await fetch(`${API_V1_BASE}/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${activeToken}`,
          },
          credentials: "include",
        });
      } catch (e) {
        console.warn("Server logout notification failed:", e);
      }
    }

    // 3. Clear all authentication and location state
    setToken(null);
    setUser(null);
    setAuthProvider(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("drishtigis_token");
      localStorage.removeItem("drishtigis_sb_auth");
    }
    clearCookieToken();
    clearLegacyLocationStorage();
  };

  const hasRole = (roles: UserRole[]): boolean => {
    if (!user) return roles.includes("PUBLIC");
    return roles.includes(user.role) || user.role === "ADMIN";
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        authProvider,
        login,
        register,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  return context || defaultAuthContext;
}
