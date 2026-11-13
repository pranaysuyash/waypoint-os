import { describe, it, expect, vi, afterEach } from "vitest";
import { parse as parseSetCookie } from "set-cookie-parser";
import { NextRequest } from "next/server";
import { GET, POST } from "../route";

function buildCookieHeaderFromSetCookies(rawSetCookies: string[]): string {
  const cookies = parseSetCookie(rawSetCookies);
  return cookies.map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
}

async function loginCookieHeader(): Promise<string | null> {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: "newuser@test.com",
        password: "testpass123",
      }),
      signal: AbortSignal.timeout(1000),
    });

    if (!response.ok) return null;

    const headersAny = response.headers as Headers & {
      getSetCookie?: () => string[];
    };
    const rawSetCookies =
      typeof headersAny.getSetCookie === "function"
        ? headersAny.getSetCookie()
        : response.headers.get("set-cookie")
          ? [response.headers.get("set-cookie") as string]
          : [];

    if (rawSetCookies.length === 0) return null;
    return buildCookieHeaderFromSetCookies(rawSetCookies);
  } catch {
    return null;
  }
}

describe("/api/trips POST endpoint - live call capture", () => {
  it("submits a live run and returns a queued run id", async () => {
    const cookieHeader = await loginCookieHeader();
    if (!cookieHeader) return;
    const request = new NextRequest("http://localhost:3000/api/trips", {
      method: "POST",
      headers: {
        cookie: cookieHeader,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        raw_note: "Customer wants to explore European destinations",
        owner_note: "Follow up about wine tours",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(202);
    expect(data).toHaveProperty("run_id");
    expect(data).toHaveProperty("state", "queued");
    expect(data).not.toHaveProperty("error");
  });

  it("rejects empty raw notes without reaching the backend", async () => {
    const request = new NextRequest("http://localhost:3000/api/trips", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner_note: "This is missing raw_note field",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data).toEqual({ error: "raw_note required" });
  });

  it("returns a 503 when call capture is disabled", async () => {
    const originalEnv = process.env.DISABLE_CALL_CAPTURE;
    process.env.DISABLE_CALL_CAPTURE = "true";

    try {
      const request = new NextRequest("http://localhost:3000/api/trips", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          raw_note: "Trip inquiry that should be rejected",
        }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data).toEqual({
        error: "Call capture feature is temporarily disabled",
      });
    } finally {
      if (originalEnv === undefined) {
        delete process.env.DISABLE_CALL_CAPTURE;
      } else {
        process.env.DISABLE_CALL_CAPTURE = originalEnv;
      }
    }
  });
});

describe("/api/trips GET BFF forwarding & workspace status filtering", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("forwards q, scope, offset, preserves valid workspace status subset, and exposes statusCounts", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [],
          total: 5,
          limit: 24,
          offset: 24,
          statusCounts: {
            assigned: 44100,
            in_progress: 120,
            waiting_customer: 49,
            blocked: 5,
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const request = new NextRequest(
      "http://localhost:3005/api/trips?view=workspace&status=blocked&q=Paris&scope=quotes&offset=24&limit=24",
    );
    const response = await GET(request);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const backendUrl = new URL(String(fetchMock.mock.calls[0][0]));
    expect(backendUrl.searchParams.get("status")).toBe("blocked");
    expect(backendUrl.searchParams.get("q")).toBe("Paris");
    expect(backendUrl.searchParams.get("scope")).toBe("quotes");
    expect(backendUrl.searchParams.get("offset")).toBe("24");
    expect(backendUrl.searchParams.get("limit")).toBe("24");
    expect(body.statusCounts).toEqual({
      assigned: 44100,
      in_progress: 120,
      waiting_customer: 49,
      blocked: 5,
    });
  });

  it("falls back to canonical workspace statuses when caller supplies an unknown status on view=workspace", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, limit: 24, offset: 0 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const request = new NextRequest(
      "http://localhost:3005/api/trips?view=workspace&status=invalid_status",
    );
    await GET(request);

    const backendUrl = new URL(String(fetchMock.mock.calls[0][0]));
    expect(backendUrl.searchParams.get("status")).toBe(
      "assigned,in_progress,ready_to_quote,ready_to_book,blocked,active",
    );
  });
});
