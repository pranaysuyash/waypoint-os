/**
 * proxy-core.ts  —  generic FastAPI proxy used by /api/[...path]/route.ts
 *
 * Auth flow:
 *   Browser → Next.js middleware checks access_token cookie
 *   This proxy forwards relevant auth headers/cookies to FastAPI
 *   FastAPI get_current_user reads access_token cookie
 *
 * Production hardening applied:
 *   - URL joining normalizes slashes (P0)
 *   - Content-Type is forwarded, never forced (P1)
 *   - Cache-Control is applied correctly (P1)
 *   - Safe backend response header allowlist (P1)
 *   - Cookie parsing uses parseSetCookie(getSetCookie()) (P0)
 *   - sameSite normalized to lowercase (P1)
 *   - 204/empty response handled without JSON.parse (P1)
 *   - Timeout errors return 504, other proxy errors return 502 (P1)
 *   - Error details hidden in production (P1)
 */

import { NextRequest, NextResponse } from "next/server";
import { parse as parseSetCookie } from "set-cookie-parser";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
const PROXY_TIMEOUT_MS = 10_000;
const IS_DEV = process.env.NODE_ENV !== "production";

/**
 * Headers from the backend that we safely copy to the browser response.
 * We do NOT forward all headers to avoid leaking debug/internal data.
 */
const RESPONSE_HEADER_ALLOWLIST = [
  "content-type",
  "cache-control",
  "x-request-id",
  "x-ratelimit-limit",
  "x-ratelimit-remaining",
  "x-ratelimit-reset",
  "retry-after",
  "content-disposition",
] as const;

export interface ProxyOptions {
  backendPath: string;
  method?: string;
  stripParams?: string[];
  extraHeaders?: Record<string, string>;
  transformResponse?: (data: unknown) => unknown;
  errorFallback?: (status: number, error: unknown) => NextResponse;
  cacheControl?: string | null;
  timeoutMs?: number;
}

/** Join base URL and path, normalising slashes */
function joinUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

export function forwardAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: req.headers.get("accept") || "application/json",
  };

  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;

  const cookie = req.headers.get("cookie");
  if (cookie) headers["cookie"] = cookie;

  const authz = req.headers.get("authorization");
  if (authz) headers["authorization"] = authz;

  // Trace IDs help correlate frontend and backend logs
  const requestId = req.headers.get("x-request-id");
  if (requestId) headers["x-request-id"] = requestId;

  // Forward user-agent for analytics / rate-limiting
  const userAgent = req.headers.get("user-agent");
  if (userAgent) headers["user-agent"] = userAgent;

  return headers;
}

function buildBackendUrl(
  req: NextRequest,
  backendPath: string,
  stripParams?: string[]
): string {
  const url = new URL(req.url);
  const params = new URLSearchParams(url.searchParams.toString());
  if (stripParams) {
    for (const p of stripParams) params.delete(p);
  }
  const query = params.toString();
  return `${joinUrl(SPINE_API_URL, backendPath)}${query ? `?${query}` : ""}`;
}

async function buildFetchOptions(
  req: NextRequest,
  opts: ProxyOptions
): Promise<RequestInit> {
  const method = (opts.method || req.method).toUpperCase();

  const headers = new Headers(forwardAuthHeaders(req));
  if (opts.extraHeaders) {
    for (const [k, v] of Object.entries(opts.extraHeaders)) {
      headers.set(k, v);
    }
  }

  const timeoutMs = opts.timeoutMs ?? PROXY_TIMEOUT_MS;
  const fetchOptions: RequestInit = {
    method,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutMs),
  };

  // Read body only for non-safe methods, using the *effective* method
  if (method !== "GET" && method !== "HEAD") {
    try {
      const body = await req.arrayBuffer();
      if (body.byteLength > 0) {
        fetchOptions.body = body;
      }
    } catch {
      // Request has no readable body.
    }
  }

  return fetchOptions;
}

/**
 * Build response headers from backend response.
 * - Copies safe headers from allowlist.
 * - Handles cacheControl option:
 *     undefined → "no-store" (safest default for auth-proxied routes)
 *     string    → set that exact value
 *     null      → do not set any cache-control header
 */
function buildResponseHeaders(
  backendHeaders: Headers,
  opts: ProxyOptions
): Headers {
  const headers = new Headers();

  for (const name of RESPONSE_HEADER_ALLOWLIST) {
    const value = backendHeaders.get(name);
    if (value) headers.set(name, value);
  }

  if (opts.cacheControl !== null) {
    headers.set("cache-control", opts.cacheControl ?? "no-store");
  }

  return headers;
}

/**
 * Set cookies on a NextResponse using NextResponse.cookies.set().
 *
 * Next.js (Turbopack dev-mode) silently drops raw "set-cookie" headers
 * attached via response.headers. We parse the backend Set-Cookie array and
 * set cookies explicitly.
 *
 * INTENTIONALLY NOT FORWARDED:
 *   - Domain: the backend origin is internal. Cookies must target the
 *     browser-visible frontend origin, not the internal FastAPI host.
 */
function applyCookies(response: NextResponse, rawSetCookieHeaders: string[]) {
  const cookies = parseSetCookie(rawSetCookieHeaders);
  for (const c of cookies) {
    response.cookies.set(c.name, c.value, {
      httpOnly: c.httpOnly ?? undefined,
      secure: c.secure ?? undefined,
      sameSite: c.sameSite
        ? (c.sameSite.toLowerCase() as "lax" | "strict" | "none")
        : undefined,
      path: c.path ?? undefined,
      expires: c.expires ?? undefined,
      maxAge: c.maxAge ?? undefined,
    });
  }
}

/** Map proxy-level errors to correct HTTP status codes. */
function getProxyErrorStatus(error: unknown): number {
  if (
    error instanceof Error &&
    (error.name === "TimeoutError" || error.name === "AbortError")
  ) {
    return 504;
  }
  return 502;
}

export async function proxyRequest(
  req: NextRequest,
  opts: ProxyOptions
): Promise<NextResponse> {
  try {
    const targetUrl = buildBackendUrl(req, opts.backendPath, opts.stripParams);
    const fetchOptions = await buildFetchOptions(req, opts);

    const backendResponse = await fetch(targetUrl, fetchOptions);

    const rawCookies = backendResponse.headers.getSetCookie();
    const responseHeaders = buildResponseHeaders(backendResponse.headers, opts);

    // 204 No Content → short-circuit without touching body
    if (backendResponse.status === 204) {
      const response = new NextResponse(null, {
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        headers: responseHeaders,
      });
      applyCookies(response, rawCookies);
      return response;
    }

    const text = await backendResponse.text();

    // Empty body → skip JSON.parse entirely
    if (!text) {
      const response = new NextResponse(null, {
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        headers: responseHeaders,
      });
      applyCookies(response, rawCookies);
      return response;
    }

    // Attempt JSON → transform if needed
    try {
      const data = JSON.parse(text);
      const payload = opts.transformResponse
        ? opts.transformResponse(data)
        : data;

      const response = NextResponse.json(payload, {
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        headers: responseHeaders,
      });
      applyCookies(response, rawCookies);
      return response;
    } catch {
      // Non-JSON → return text verbatim
      const response = new NextResponse(text, {
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        headers: responseHeaders,
      });
      applyCookies(response, rawCookies);
      return response;
    }
  } catch (error) {
    const status = getProxyErrorStatus(error);

    if (opts.errorFallback) {
      return opts.errorFallback(status, error);
    }

    const message = error instanceof Error ? error.message : "Unknown error";
    console.error(`Proxy error [${opts.backendPath}] status=${status}:`, error);

    return NextResponse.json(
      {
        ok: false,
        error: status === 504 ? "Backend timeout" : "Backend unavailable",
        ...(IS_DEV ? { detail: message } : {}),
      },
      { status }
    );
  }
}
