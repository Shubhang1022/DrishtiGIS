import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/register", "/design-system"];

const ROUTE_ALIASES: Record<string, string> = {
  "/map": "/app/map",
  "/dashboard": "/app/map",
  "/profile": "/app/profile",
  "/review": "/app/review",
  "/assistant": "/app/assistant",
  "/exports": "/app/exports",
  "/reports": "/app/reports",
  "/history": "/app/history",
  "/location": "/app/location",
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Allow static files, Next.js internal assets, and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // 2. Handle alias routes (/map -> /app/map, /profile -> /app/profile, etc.)
  if (ROUTE_ALIASES[pathname]) {
    return NextResponse.redirect(new URL(ROUTE_ALIASES[pathname], request.url));
  }
  if (pathname.startsWith("/property/")) {
    return NextResponse.redirect(new URL(`/app${pathname}`, request.url));
  }

  const token = request.cookies.get("drishtigis_token")?.value;

  // 3. Allow explicitly listed public paths
  if (PUBLIC_PATHS.includes(pathname)) {
    // If already logged in, redirect away from /login and /register to map workspace
    if (token && (pathname === "/login" || pathname === "/register")) {
      return NextResponse.redirect(new URL("/app/map", request.url));
    }
    return NextResponse.next();
  }

  // 4. Protect all other application routes (/app/*, /admin/*)
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
