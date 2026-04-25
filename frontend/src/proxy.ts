import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Next.js Network Boundary (Proxy)
 *
 * Ported from deprecated middleware.ts to comply with Next.js 16 standards.
 * Ensures all original authentication guards, whitelists, and redirect
 * patterns are preserved.
 */

// Page routes that do NOT require authentication (Original + V2)
const PUBLIC_PAGES = new Set([
  '/',
  '/v2',
  '/itinerary-checker',
  '/login',
  '/signup',
  '/forgot-password',
  '/reset-password',
]);

/**
 * isAllowed — Preserves whitelisting logic for static assets and public routes.
 */
function isAllowed(pathname: string): boolean {
  // API routes pass through — FastAPI handles auth
  if (pathname.startsWith('/api/')) return true;

  // Static assets and internal Next.js paths
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/static/') ||
    pathname.startsWith('/favicon')
  ) {
    return true;
  }

  // Explicitly whitelisted public pages
  if (PUBLIC_PAGES.has(pathname)) return true;

  // Auth-related sub-paths
  if (pathname.startsWith('/reset-password')) return true;

  return false;
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Allow through if the route doesn't need auth (Verbatim preservation)
  if (isAllowed(pathname)) {
    return NextResponse.next();
  }

  // 2. Check for cookies set by FastAPI. A refresh token is enough to let
  // /api/auth/me or /api/auth/refresh repair an expired access cookie.
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;

  if (!accessToken && !refreshToken) {
    // 3. Redirect to login, preserving the route the operator intended.
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Token present — allow the request through to protected routes
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except static assets (Original matcher)
     */
    '/((?!_next/static|_next/image|favicon\\.ico).*)',
  ],
};
