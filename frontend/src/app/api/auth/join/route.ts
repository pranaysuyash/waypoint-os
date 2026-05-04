/**
 * BFF route: POST /api/auth/join
 *
 * Creates a new user account and joins an existing agency via workspace invitation code.
 * This is the agent onboarding path, distinct from /api/auth/signup which creates agencies.
 *
 * On success, the backend sets httpOnly auth cookies (access_token, refresh_token).
 * This proxy forwards those Set-Cookie headers to the browser via applyCookies in proxy-core.
 *
 * The explicit route file is used (rather than the catch-all proxy) because:
 * 1. The auth/* family of routes all have dedicated files for clarity and control.
 * 2. Set-Cookie forwarding needs to work correctly (handled by bff-auth + proxy-core).
 */

import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { parse as parseSetCookie } from "set-cookie-parser";
import { NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return bffJson({ error: "Invalid request body" }, 400);
  }

  const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/auth/join`;

  try {
    const response = await fetch(
      spineApiUrl,
      bffFetchOptions(request, "POST", "access_only", { "Content-Type": "application/json" }, body)
    );

    const rawCookies = response.headers.getSetCookie();

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      const errorData = await response.json().catch(() => ({ detail: "Join failed" }));
      return bffJson(
        { error: errorData.detail || "Join failed" },
        response.status
      );
    }

    const data = await response.json();
    const nextResponse = NextResponse.json({ ok: true, ...data }, { status: 201 });

    // Forward auth cookies from FastAPI to the browser
    const cookies = parseSetCookie(rawCookies);
    for (const c of cookies) {
      nextResponse.cookies.set(c.name, c.value, {
        httpOnly: c.httpOnly ?? undefined,
        secure: c.secure ?? undefined,
        sameSite: c.sameSite ? (c.sameSite.toLowerCase() as "lax" | "strict" | "none") : undefined,
        path: c.path ?? undefined,
        expires: c.expires ?? undefined,
        maxAge: c.maxAge ?? undefined,
      });
    }

    return nextResponse;
  } catch {
    return bffJson({ error: "Backend unavailable" }, 502);
  }
}
