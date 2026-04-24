/**
 * Next.js Middleware — Edge-level route protection.
 *
 * Enforces authentication by checking for the access_token cookie.
 * Unauthenticated requests to protected routes are redirected to /login.
 *
 * Public routes (no auth required):
 * - /login, /signup, /forgot-password, /reset-password
 * - /api/auth/* (auth proxy endpoints)
 * - /health
 * - Static assets (_next/, images, etc.)
 */

import { NextResponse, type NextRequest } from "next/server";

// Routes that don't require authentication
const PUBLIC_PATHS = [
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/api/auth",
  "/health",
];

// Static asset prefixes that should always be allowed
const STATIC_PREFIXES = ["/_next", "/favicon", "/images", "/assets"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow static assets
  if (STATIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  // Allow public paths
  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  // Check for access_token cookie
  const accessToken = request.cookies.get("access_token");

  if (!accessToken) {
    // Redirect to login, preserving the intended destination
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
