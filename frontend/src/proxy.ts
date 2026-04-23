import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_ROUTES = ['/login', '/signup', '/forgot-password', '/reset-password'];
const PROTECTED_ROUTES = ['/overview', '/inbox', '/workspace', '/owner', '/settings', '/workbench'];

function isAuthRoute(pathname: string): boolean {
  return AUTH_ROUTES.some((route) => pathname.startsWith(route));
}

function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some((route) => pathname.startsWith(route));
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check for access_token cookie (set on login/signup)
  const accessToken = request.cookies.get('access_token')?.value;
  // Also check refresh_token cookie (long-lived session)
  const refreshToken = request.cookies.get('refresh_token')?.value;
  const hasAuth = !!accessToken || !!refreshToken;

  // Redirect authenticated users away from auth pages
  if (isAuthRoute(pathname) && hasAuth) {
    return NextResponse.redirect(new URL('/overview', request.url));
  }

  // Redirect unauthenticated users to login
  if (isProtectedRoute(pathname) && !hasAuth) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)',
  ],
};
