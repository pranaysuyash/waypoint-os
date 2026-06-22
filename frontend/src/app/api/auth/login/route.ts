import { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { parse as parseSetCookie } from "set-cookie-parser";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";

function getSetCookieHeaders(headers: Headers): string[] {
  const headersAny = headers as Headers & {
    getSetCookie?: () => string[];
  };

  if (typeof headersAny.getSetCookie === "function") {
    return headersAny.getSetCookie();
  }

  const singleHeader = headers.get("set-cookie");
  return singleHeader ? [singleHeader] : [];
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return bffJson({ error: "Invalid request body" }, 400);
  }

  const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/auth/login`;

  try {
    const response = await fetch(
      spineApiUrl,
      bffFetchOptions(request, "POST", "access_only", { "Content-Type": "application/json" }, body)
    );

    const rawCookies = getSetCookieHeaders(response.headers);

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      const errorData = await response.json().catch(() => ({ detail: "Login failed" }));
      return bffJson(
        { error: errorData.detail || "Login failed" },
        response.status
      );
    }

    const data = await response.json();
    const nextResponse = NextResponse.json({ ok: true, ...data }, { status: 200 });

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
  } catch (error) {
    console.error("Error proxying login:", error);
    return bffJson({ error: "Backend unavailable" }, 502);
  }
}
