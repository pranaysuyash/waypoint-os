import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Next.js Network Boundary (Proxy)
 *
 * Page-level navigation guard for protected frontend routes.
 *
 * This is not the authoritative auth boundary. It only checks whether auth
 * cookies are present so unauthenticated users are redirected before protected
 * pages render. JWT validation happens in FastAPI AuthMiddleware through the
 * BFF API routes.
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

export function proxy(request: NextRequest) {
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

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon\\.ico).*)',
  ],
};
