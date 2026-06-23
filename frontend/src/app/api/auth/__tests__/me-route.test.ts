import { describe, expect, it } from "vitest";
import { parse as parseSetCookie } from "set-cookie-parser";
import { NextRequest } from "next/server";
import { GET } from "../me/route";

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

describe("/api/auth/me GET - live auth refresh retry", () => {
  it("refreshes auth cookies and returns the real authenticated user payload", async () => {
    const cookieHeader = await loginCookieHeader();
    const refreshMatch = cookieHeader.match(/refresh_token=[^;]+/);
    expect(refreshMatch).not.toBeNull();

    const request = new NextRequest("http://localhost:3000/api/auth/me", {
      headers: {
        cookie: cookieHeader.replace(/access_token=[^;]+/, "access_token=invalid"),
      },
    });

    const response = await GET(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toMatchObject({
      ok: true,
      user: {
        email: "newuser@test.com",
      },
      agency: {
        id: "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
      },
    });
  });
});
