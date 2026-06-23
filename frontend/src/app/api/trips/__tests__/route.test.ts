import { describe, it, expect } from "vitest";
import { parse as parseSetCookie } from "set-cookie-parser";
import { NextRequest } from "next/server";
import { POST } from "../route";

function buildCookieHeaderFromSetCookies(rawSetCookies: string[]): string {
  const cookies = parseSetCookie(rawSetCookies);
  return cookies.map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
}

async function loginCookieHeader(): Promise<string> {
  const response = await fetch("http://127.0.0.1:8000/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: "newuser@test.com",
      password: "testpass123",
    }),
  });

  expect(response.ok).toBe(true);

  const headersAny = response.headers as Headers & {
    getSetCookie?: () => string[];
  };
  const rawSetCookies =
    typeof headersAny.getSetCookie === "function"
      ? headersAny.getSetCookie()
      : response.headers.get("set-cookie")
        ? [response.headers.get("set-cookie") as string]
        : [];

  expect(rawSetCookies.length).toBeGreaterThan(0);
  return buildCookieHeaderFromSetCookies(rawSetCookies);
}

describe("/api/trips POST endpoint - live call capture", () => {
  it("submits a live run and returns a queued run id", async () => {
    const cookieHeader = await loginCookieHeader();
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
