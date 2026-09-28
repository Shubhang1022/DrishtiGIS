"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, UserRole } from "@/lib/types/auth";
import { loginUser, registerUser, getCurrentUser } from "@/lib/api/auth";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
}

const defaultAuthContext: AuthContextType = {
  user: null,
  token: null,
  loading: false,
  login: async () => {},
  register: async () => {},
  logout: () => {},
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
  }
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
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const data = await loginUser(email, password);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("drishtigis_token", data.access_token);
    setCookieToken(data.access_token);
  };

  const register = async (formData: any) => {
    const data = await registerUser(formData);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("drishtigis_token", data.access_token);
    setCookieToken(data.access_token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("drishtigis_token");
    clearCookieToken();
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
