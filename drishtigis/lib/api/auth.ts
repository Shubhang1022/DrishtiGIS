import { AuthTokenResponse, User, SecurityAuditLogItem } from "@/lib/types/auth";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function loginUser(email: string, password: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Authentication failed");
  }

  return res.json();
}

export async function registerUser(data: {
  email: string;
  name: string;
  password: string;
  role?: string;
  organization?: string;
  city?: string;
  state?: string;
}): Promise<AuthTokenResponse> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }

  return res.json();
}

export async function getCurrentUser(token: string): Promise<User> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error("Session expired or invalid");
  }

  return res.json();
}

export async function fetchUsers(token: string): Promise<User[]> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/users`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error("Failed to fetch user directory");
  }

  return res.json();
}

export async function updateUserRole(token: string, userId: string, role: string): Promise<User> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/users/${userId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ role }),
  });

  if (!res.ok) {
    throw new Error("Failed to update user role");
  }

  return res.json();
}

export async function fetchAuditLogs(token: string): Promise<SecurityAuditLogItem[]> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/audit-logs`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error("Failed to fetch audit logs");
  }

  const data = await res.json();
  return data.logs || [];
}

export async function fetchRegions(): Promise<any[]> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/regions`);
  if (!res.ok) {
    throw new Error("Failed to fetch regions");
  }
  const data = await res.json();
  return data.regions || [];
}

export async function createRegion(token: string, regionData: any): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/v1/auth/regions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(regionData),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to register region" }));
    throw new Error(err.detail || "Failed to register region");
  }

  return res.json();
}

