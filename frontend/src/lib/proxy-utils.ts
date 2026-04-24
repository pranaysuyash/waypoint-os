/**
 * Proxy utilities for Next.js BFF routes.
 *
 * Provides helpers to forward authentication cookies from the incoming
 * request to the spine-api backend, ensuring sessions are maintained
 * across the proxy boundary.
 */

import type { NextRequest } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

/**
 * Build headers that forward the incoming request's cookies to spine-api.
 * Preserves Content-Type and adds the Cookie header if present.
 */
export function forwardAuthHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const cookie = request.headers.get("cookie");
  if (cookie) {
    headers["cookie"] = cookie;
  }

  return headers;
}

/**
 * Build headers that forward the incoming request's cookies to spine-api
 * for non-JSON requests (e.g., file uploads).
 */
export function forwardAuthHeadersRaw(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {};

  const cookie = request.headers.get("cookie");
  if (cookie) {
    headers["cookie"] = cookie;
  }

  return headers;
}

/**
 * Construct the spine-api base URL.
 */
export function getSpineApiUrl(): string {
  return SPINE_API_URL;
}
