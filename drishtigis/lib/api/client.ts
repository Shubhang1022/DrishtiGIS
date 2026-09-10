/**
 * DrishtiGIS — API Base Client
 * ==============================
 * Shared fetch helper for all API calls to the FastAPI backend.
 * Base URL read from NEXT_PUBLIC_API_URL environment variable.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API error ${res.status} for ${path}`);
  }
  return res.json() as Promise<T>;
}
