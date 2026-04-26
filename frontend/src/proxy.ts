import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Next.js Network Boundary (Proxy)
 *
 * Page-level navigation guard for protected frontend routes.
 *
 * This runs as an edge middleware on every page request (via Next.js
 * proxy.ts convention). It checks for auth cookies before rendering
 * so unauthenticated users are redirected server-side.
 *
 * NOTE: JWT validation still happens at FastAPI AuthMiddleware.
 * This is just a server-side redirect to avoid the flash-of-unauthenticated-content
 * that happens with client-side-only guards like AuthProvider.
 */

const PUBLIC_PAGES = new Set([
  '/',
  '/v2',
  '/itinerary-checker',
  '/login',
  '/signup',
  '/forgot-password',
  '/reset-password',
]);

const AUTH_PAGES = new Set(['/login', '/signup']);

const PUBLIC_FILES = new Set([
  '/robots.txt',
  '/sitemap.xml',
  '/manifest.json',
  '/icon.png',
  '/apple-icon.png',
  '/opengraph-image.png',
  '/twitter-image.png',
]);

const PROTECTED_LANDING = '/overview';

function hasAuthCookie(request: NextRequest): boolean {
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;
  return Boolean(accessToken || refreshToken);
}

function isAllowed(pathname: string): boolean {
  if (pathname.startsWith('/api/')) return true;

  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/static/') ||
    pathname.startsWith('/images/') ||
    pathname.startsWith('/favicon')
  ) {
    return true;
  }

  if (PUBLIC_FILES.has(pathname)) return true;

  if (PUBLIC_PAGES.has(pathname)) return true;

  if (pathname.startsWith('/reset-password/')) return true;

  return false;
}

function isSafeRedirect(target: string): boolean {
  if (!target.startsWith('/')) return false;
  if (target.startsWith('//')) return false;
  if (AUTH_PAGES.has(target)) return false;
  return true;
}

/**
 * The proxy handler — used by the Next.js edge runtime.
 * Exported as both default and named so callers (including tests)
 * can import it whichever way is convenient.
 */
export default function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const authed = hasAuthCookie(request);

  if (authed && AUTH_PAGES.has(pathname)) {
    const redirectTarget = request.nextUrl.searchParams.get('redirect') || '';
    const safeRedirect = isSafeRedirect(redirectTarget)
      ? redirectTarget
      : PROTECTED_LANDING;
    return NextResponse.redirect(new URL(safeRedirect, request.url));
  }

  if (isAllowed(pathname)) {
    return NextResponse.next();
  }

  if (!authed) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// Re-export as named export for unit tests that import { proxy } from "../proxy"
export { proxy as proxy };

/**
 * Matcher config — controls which paths run through this proxy.
 * - Excludes static files so they serve directly without middleware overhead
 * - All other paths go through proxy (including protected pages)
 */
export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon\.ico).*)',
  ],
};
