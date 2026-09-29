"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, UserRole } from "@/lib/types/auth";
import { loginUser, registerUser, getCurrentUser } from "@/lib/api/auth";
import { API_V1_BASE } from "@/lib/api/client";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (roles: UserRole[]) => boolean;
}

const defaultAuthContext: AuthContextType = {
  user: null,
  token: null,
  loading: false,
  login: async () => {},
  register: async () => {},
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
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("drishtigis_token") || getCookieToken();
    if (savedToken) {
      setToken(savedToken);
      setCookieToken(savedToken);
      getCurrentUser(savedToken)
        .then((userData) => setUser(userData))
        .catch(() => {
          localStorage.removeItem("drishtigis_token");
          clearCookieToken();
          clearLegacyLocationStorage();
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    clearLegacyLocationStorage();
    const data = await loginUser(email, password);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("drishtigis_token", data.access_token);
    setCookieToken(data.access_token);
  };

  const register = async (formData: any) => {
    clearLegacyLocationStorage();
    const data = await registerUser(formData);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("drishtigis_token", data.access_token);
    setCookieToken(data.access_token);
  };

  const logout = async () => {
    const activeToken = token || localStorage.getItem("drishtigis_token") || getCookieToken();
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
    setToken(null);
    setUser(null);
    localStorage.removeItem("drishtigis_token");
    clearCookieToken();
    clearLegacyLocationStorage();
  };

  const hasRole = (roles: UserRole[]): boolean => {
    if (!user) return roles.includes("PUBLIC");
    return roles.includes(user.role) || user.role === "ADMIN";
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  return context || defaultAuthContext;
}
