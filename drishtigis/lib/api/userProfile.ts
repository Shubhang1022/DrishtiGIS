/**
 * DrishtiGIS — User Profile API Client
 * Authenticated per-user profile management.
 */
import { API_V1_BASE } from "./client";

const API_BASE = API_V1_BASE;

export interface UserProfileData {
  user_id: string;
  full_name?: string;
  phone_number?: string;
  house_number?: string;
  street_locality?: string;
  city?: string;
  state?: string;
  pincode?: string;
  organization?: string;
  show_name_publicly: boolean;
  show_address_publicly: boolean;
  show_phone_publicly: boolean;
  created_at?: string;
  updated_at?: string;
}

export async function fetchUserProfile(token: string): Promise<UserProfileData | null> {
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/user/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch user profile");
    return await res.json();
  } catch {
    return null;
  }
}

export async function saveUserProfile(
  token: string,
  profileData: Partial<UserProfileData>
): Promise<UserProfileData> {
  const res = await fetch(`${API_BASE}/user/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(profileData),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to update user profile");
  }

  return await res.json();
}
