/**
 * DrishtiGIS — API Base Client
 * ==============================
 * Shared fetch helper for all API calls to the FastAPI backend.
 * Base URL read from NEXT_PUBLIC_API_URL environment variable.
 */

/**
 * Retrieves the configured backend API root URL.
 * Supports NEXT_PUBLIC_API_URL (primary) and NEXT_PUBLIC_BACKEND_URL (fallback).
 * Strips any trailing slash and defaults to http://localhost:8000 for local dev.
 */
export function getBackendUrl(): string {
  const envUrl =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, "");
  }
  return "http://localhost:8000";
}

export const API_BASE = getBackendUrl();
export const BACKEND_URL = API_BASE;
export const API_V1_BASE = `${API_BASE}/api/v1`;


export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Retrieves the current user session token from localStorage or document.cookie.
 * Client-safe (returns null during server rendering).
 */
export function getStoredAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const local = localStorage.getItem("drishtigis_token");
    if (local) return local;
  } catch {}
  try {
    const match = document.cookie.match(/(?:^|; )drishtigis_token=([^;]*)/);
    if (match) return decodeURIComponent(match[1]);
  } catch {}
  return null;
}

export interface ApiFetchOptions extends RequestInit {
  token?: string | null;
}

export async function apiFetch<T>(
  path: string,
  options?: ApiFetchOptions
): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = path.startsWith("http://") || path.startsWith("https://")
    ? path
    : `${API_BASE}${normalizedPath}`;
  const token = options?.token !== undefined ? options.token : getStoredAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    credentials: options?.credentials ?? "include",
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMsg = `API error ${res.status} for ${path}`;
    try {
      const errJson = await res.json();
      if (errJson?.detail) {
        errMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {}
    throw new ApiError(res.status, errMsg);
  }

  return res.json() as Promise<T>;
}
