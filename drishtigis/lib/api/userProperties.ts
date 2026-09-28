/**
 * DrishtiGIS — User Registered Properties API Client
 * Manages user-registered property locations, draggable markers, and privacy opt-ins.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  `${process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/v1`;

export interface UserPropertyData {
  id: string;
  user_id: string;
  title: string;
  house_number?: string;
  street_locality?: string;
  city?: string;
  state?: string;
  pincode?: string;
  property_type: string;
  description?: string;
  latitude: number;
  longitude: number;
  accuracy_m?: number | null;
  is_user_adjusted?: boolean;
  is_public?: boolean;
  show_name_publicly?: boolean;
  show_address_publicly?: boolean;
  show_phone_publicly?: boolean;
  phone_number?: string;
  owner_name?: string;
  created_at?: string;
  updated_at?: string;
}

export async function fetchUserProperties(token?: string | null): Promise<UserPropertyData[]> {
  try {
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}/user/properties`, {
      headers,
      credentials: "include",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function createUserProperty(
  token: string | null,
  data: Partial<UserPropertyData>
): Promise<UserPropertyData> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/user/properties`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to register property");
  }

  return await res.json();
}

export async function updateUserProperty(
  token: string | null,
  propertyId: string,
  data: Partial<UserPropertyData>
): Promise<UserPropertyData> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/user/properties/${propertyId}`, {
    method: "PUT",
    headers,
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to update property");
  }

  return await res.json();
}

export async function deleteUserProperty(
  token: string | null,
  propertyId: string
): Promise<boolean> {
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/user/properties/${propertyId}`, {
    method: "DELETE",
    headers,
    credentials: "include",
  });

  return res.ok;
}

export async function fetchPublicUserProperties(): Promise<Partial<UserPropertyData>[]> {
  try {
    const res = await fetch(`${API_BASE}/user/properties/public`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}
