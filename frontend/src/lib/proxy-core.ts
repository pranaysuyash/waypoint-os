/**
 * proxy-core.ts  —  generic FastAPI proxy used by /api/[...path]/route.ts
 *
 * Auth flow:
 *   Browser → Next.js middleware checks access_token cookie
 *   This proxy forwards all cookies to FastAPI
 *   FastAPI get_current_user reads access_token cookie
 */

import { NextRequest, NextResponse } from "next/server";
import { parseSetCookie } from "set-cookie-parser";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
const PROXY_TIMEOUT_MS = 10_000;

export interface ProxyOptions {
  backendPath: string;
  method?: string;
  stripParams?: string[];
  extraHeaders?: Record<string, string>;
  transformResponse?: (data: unknown) => unknown;
  errorFallback?: (status: number) => NextResponse;
  cacheControl?: string | null;
}

export function forwardAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  const cookie = req.headers.get("cookie");
  if (cookie) headers["cookie"] = cookie;
  const authz = req.headers.get("authorization");
  if (authz) headers["authorization"] = authz;
  return headers;
}

function buildBackendUrl(req: NextRequest, backendPath: string, stripParams?: string[]): string {
  const url = new URL(req.url);
  const params = new URLSearchParams(url.searchParams.toString());
  if (stripParams) {
    for (const p of stripParams) params.delete(p);
  }
  const query = params.toString();
  return `${SPINE_API_URL}/${backendPath}${query ? `?${query}` : ""}`;
}

async function buildFetchOptions(req: NextRequest, opts: ProxyOptions): Promise<RequestInit> {
  const headers = new Headers(forwardAuthHeaders(req));
  if (opts.extraHeaders) {
    for (const [k, v] of Object.entries(opts.extraHeaders)) {
      headers.set(k, v);
    }
  }

  const fetchOptions: RequestInit = {
    method: opts.method || req.method,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(PROXY_TIMEOUT_MS),
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      const body = await req.text();
      if (body) fetchOptions.body = body;
    } catch {
      // no body
    }
  }

  return fetchOptions;
}

function applyCookies(response: NextResponse, rawSetCookieHeaders: string[]) {
  /**
   * Set cookies on a NextResponse using NextResponse.cookies.set().
   *
   * Next.js (Turbopack dev mode, issue #63991) silently drops raw "set-cookie"
   * headers attached to a NextResponse. We use `set-cookie-parser` to parse
   * backend Set-Cookie headers and set cookies explicitly via the typed API.
   */
  for (const raw of rawSetCookieHeaders) {
    const parsed = parseSetCookie(raw);
    for (const c of parsed) {
      response.cookies.set(c.name, c.value, {
        httpOnly: c.httpOnly ?? undefined,
        secure: c.secure ?? undefined,
        sameSite: (c.sameSite as "lax" | "strict" | "none") ?? undefined,
        path: c.path ?? undefined,
        expires: c.expires ?? undefined,
        maxAge: c.maxAge ?? undefined,
      });
    }
  }
}

export async function proxyRequest(req: NextRequest, opts: ProxyOptions): Promise<NextResponse> {
  try {
    const targetUrl = buildBackendUrl(req, opts.backendPath, opts.stripParams);
    const fetchOptions = await buildFetchOptions(req, opts);

    const be = await fetch(targetUrl, fetchOptions);
    const rawCookies = be.headers.getSetCookie();

    let payload: unknown;
    const text = await be.text();
    try {
      const data = JSON.parse(text);
      payload = opts.transformResponse ? opts.transformResponse(data) : data;
    } catch {
      // Non-JSON response — return as plain text
      const response = new NextResponse(text, {
        status: be.status,
        statusText: be.statusText,
        headers: { "content-type": be.headers.get("content-type") || "text/plain" },
      });
      applyCookies(response, rawCookies);
      return response;
    }

    const response = NextResponse.json(payload, {
      status: be.status,
      headers: {
        "content-type": be.headers.get("content-type") || "application/json",
      },
    });
    applyCookies(response, rawCookies);
    return response;
  } catch (error) {
    if (opts.errorFallback) return opts.errorFallback(502);
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error(`Proxy error [${opts.backendPath}]:`, error);
    return NextResponse.json(
      { ok: false, error: `Proxy error: ${message}` },
      { status: 502 }
    );
  }
}
