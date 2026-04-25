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
 *   - Mapped routes (via route-map.ts) are preferred and safer.
 *   - Unknown paths fall through to passthrough for rapid dev.
 *   - If a path is NOT in route-map.ts, a console.warn is emitted.
 *   - Before production launch, tighten by removing fallback passthrough
 *     and requiring every route to be explicitly mapped.
 */

import { NextRequest, NextResponse } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";
import { resolveBackendPath } from "@/lib/route-map";

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

    const backendPath = resolveBackendPath(segments);
    if (backendPath == null) {
      // Passthrough — unknown path. Log so we know what to add to route-map.ts.
      const joined = segments.join("/");
      console.warn(
        `[proxy] Unmapped route: ${request.method} /api/${joined} → falling through to ${joined}`
      );
      return proxyRequest(request, {
        backendPath: joined,
        method,
      });
    }

    return proxyRequest(request, {
      backendPath,
      method,
    });
  };
}

export const GET = handler("GET");
export const POST = handler("POST");
export const PUT = handler("PUT");
export const PATCH = handler("PATCH");
export const DELETE = handler("DELETE");
