/**
 * Catch-all proxy: /api/[...path] → FastAPI spine_api
 *
 * This is the DEFAULT handler for all /api/* calls not matched by explicit routes.
 * Next.js guarantees that explicit routes always win over this catch-all.
 *
 * Auth flow:
 *   Browser → access_token httpOnly cookie travels automatically
 *   This proxy forwards cookies + safe headers to FastAPI
 *   FastAPI get_current_user reads access_token cookie
 *
 * Security note:
 *   - Mapped routes (via route-map.ts) are the ONLY paths forwarded.
 *   - Unknown paths return 404 — no fallback passthrough.
 *   - Every route must be explicitly mapped before use.
 */

import { NextRequest, NextResponse } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";
import { resolveBackendRoute } from "@/lib/route-map";

function handler(method: string) {
  return async (
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
  ) => {
    const { path: segments } = await params;

    if (!segments || segments.length === 0) {
      return NextResponse.json(
        { error: "No path provided" },
        { status: 404 }
      );
    }

    const backendRoute = resolveBackendRoute(segments);
    if (backendRoute == null) {
      // Unknown route — deny. Map it in route-map.ts before use.
      return NextResponse.json(
        { error: "Not found" },
        { status: 404 }
      );
    }

    return proxyRequest(request, {
      backendPath: backendRoute.backendPath,
      method,
      timeoutMs: backendRoute.timeoutMs,
    });
  };
}

export const GET = handler("GET");
export const POST = handler("POST");
export const PUT = handler("PUT");
export const PATCH = handler("PATCH");
export const DELETE = handler("DELETE");
