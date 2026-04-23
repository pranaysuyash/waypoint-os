import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_ROUTES = ['/login', '/signup'];
const PROTECTED_ROUTES = ['/', '/inbox', '/workspace', '/owner', '/settings', '/workbench'];

function isAuthRoute(pathname: string): boolean {
  return AUTH_ROUTES.some((route) => pathname.startsWith(route));
}

function isProtectedRoute(pathname: string): boolean {
  if (pathname === '/') return true;
  return PROTECTED_ROUTES.some((route) => route !== '/' && pathname.startsWith(route));
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('access_token')?.value;

  // Check for token in Authorization header pattern (via cookie or localStorage)
  // Note: middleware can't access localStorage, so we use a session cookie approach
  const hasAuth = !!token;

  // Redirect authenticated users away from auth pages
  if (isAuthRoute(pathname) && hasAuth) {
    return NextResponse.redirect(new URL('/', request.url));
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
