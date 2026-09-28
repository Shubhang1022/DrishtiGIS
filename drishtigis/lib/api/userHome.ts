/**
 * DrishtiGIS — Private User HOME Location API Client
 * Strictly authenticated per-user HOME location operations.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  `${process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/v1`;

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
  try {
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}/user/home`, {
      headers,
      credentials: "include",
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error("Failed to fetch HOME location");
    return await res.json();
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
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

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
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}/user/home`, {
    method: "DELETE",
    headers,
    credentials: "include",
  });
  return res.ok;
}
