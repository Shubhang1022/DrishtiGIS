/**
 * DrishtiGIS — Private User HOME Location API Client
 * Strictly authenticated per-user HOME location operations.
 */
import { API_V1_BASE } from "./client";

const API_BASE = API_V1_BASE;

export interface UserHomeData {
  user_id: string;
  latitude: number;
  longitude: number;
  address_label?: string;
  accuracy_m?: number | null;
  created_at?: string;
  updated_at?: string;
}

export async function fetchUserHome(token?: string | null): Promise<UserHomeData | null> {
  // CRITICAL PRIVACY: If no authenticated token is provided, never make ambient network requests
  if (!token || !token.trim()) {
    return null;
  }

  try {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${token.trim()}`,
    };
    const res = await fetch(`${API_BASE}/user/home`, {
      headers,
      credentials: "include",
    });
    if (res.status === 404 || res.status === 401) return null;
    if (!res.ok) throw new Error("Failed to fetch HOME location");
    const data: UserHomeData = await res.json();
    return data;
  } catch {
    return null;
  }
}

export async function saveUserHome(
  token: string | null,
  latitude: number,
  longitude: number,
  address_label: string = "HOME",
  accuracy_m?: number
): Promise<UserHomeData> {
  if (!token || !token.trim()) {
    throw new Error("Authentication required to save private HOME location.");
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token.trim()}`,
  };

  const res = await fetch(`${API_BASE}/user/home`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify({
      latitude,
      longitude,
      address_label,
      accuracy_m,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to save HOME location");
  }

  return await res.json();
}

export async function deleteUserHome(token?: string | null): Promise<boolean> {
  if (!token || !token.trim()) {
    return false;
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token.trim()}`,
  };
  const res = await fetch(`${API_BASE}/user/home`, {
    method: "DELETE",
    headers,
    credentials: "include",
  });
  return res.ok;
}
