/**
 * bff-auth.ts - Shared auth forwarding for explicit BFF routes.
 *
 * Explicit routes (app/api/trips/route.ts, etc.) transform backend responses
 * and cannot use the generic proxyRequest() from proxy-core.ts.
 *
 * This module provides the auth primitives those routes need:
 *   - Selective cookie forwarding (access_token, refresh_token only)
 *   - No empty Cookie header when no auth cookies exist
 *   - No reliance on credentials: "include" (server-side concept only)
 *   - CSRF Origin validation for mutating routes
 *
 * FastAPI AuthMiddleware is the authoritative auth boundary.
 * These helpers ensure the BFF forwards credentials correctly.
 */

import { NextRequest, NextResponse } from "next/server";

const PROXY_TIMEOUT_MS = 10_000;

export type CookieScope = "access_only" | "access_and_refresh";


function buildAuthCookieHeader(
  request: NextRequest,
  scope: CookieScope = "access_only"
): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  const access = request.cookies.get("access_token")?.value;
  const refresh = request.cookies.get("refresh_token")?.value;

  const parts: string[] = [];
  if (access) parts.push(`access_token=${access}`);
  if (scope === "access_and_refresh" && refresh) {
    parts.push(`refresh_token=${refresh}`);
  }

  if (parts.length > 0) {
    headers["Cookie"] = parts.join("; ");
  }

  return headers;
}

export function bffHeaders(
  request: NextRequest,
  scope: CookieScope = "access_only",
  extra?: Record<string, string>
): Record<string, string> {
  return {
    ...buildAuthCookieHeader(request, scope),
    ...extra,
  };
}

export function bffFetchOptions(
  request: NextRequest,
  method: string,
  scope: CookieScope = "access_only",
  extraHeaders?: Record<string, string>,
  body?: unknown
): RequestInit {
  const opts: RequestInit = {
    method,
    headers: bffHeaders(request, scope, extraHeaders),
    cache: "no-store",
    signal: AbortSignal.timeout(PROXY_TIMEOUT_MS),
  };

  if (body !== undefined && method !== "GET" && method !== "HEAD") {
    const headers = new Headers(opts.headers);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
      opts.headers = headers;
    }
    opts.body = JSON.stringify(body);
  }

  return opts;
}

export function noStoreHeaders(): HeadersInit {
  return { "Cache-Control": "no-store" };
}

export function bffJson(payload: unknown, status: number = 200): NextResponse {
  return NextResponse.json(payload, {
    status,
    headers: noStoreHeaders(),
  });
}

export function validateOrigin(request: NextRequest): NextResponse | null {
  const origin = request.headers.get("origin");
  if (!origin) return null;

  const host = request.headers.get("host");
  if (!host) return null;

  try {
    const originHost = new URL(origin).host;
    if (originHost !== host) {
      return NextResponse.json(
        { error: "Invalid origin" },
        { status: 403, headers: noStoreHeaders() }
      );
    }
  } catch {
    return NextResponse.json(
      { error: "Invalid origin" },
      { status: 403, headers: noStoreHeaders() }
    );
  }

  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && fetchSite === "cross-site") {
    return NextResponse.json(
      { error: "Cross-site request rejected" },
      { status: 403, headers: noStoreHeaders() }
    );
  }

  return null;
}

export function isAuthStatus(status: number): boolean {
  return status === 401 || status === 403;
}
