import { describe, expect, it } from "vitest";
import { parse as parseSetCookie } from "set-cookie-parser";
import { NextRequest } from "next/server";
import { GET } from "../route";

const TRIP_ID = "trip_2333bff6434d";

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

describe("/api/trips/[id] GET - live auth refresh retry", () => {
  it("refreshes auth cookies and returns the real trip payload from the live backend", async () => {
    const cookieHeader = await loginCookieHeader();
    const request = new NextRequest(`http://localhost:3000/api/trips/${TRIP_ID}`, {
      headers: {
        cookie: cookieHeader.replace(/access_token=[^;]+/, "access_token=invalid"),
      },
    });

    const response = await GET(request, { params: Promise.resolve({ id: TRIP_ID }) });
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toMatchObject({
      id: TRIP_ID,
      destination: "Italy",
      tripPurpose: "family leisure",
      validation: {
        warnings: expect.arrayContaining([
          expect.objectContaining({
            field: "budget_raw_text",
          }),
        ]),
      },
    });
    expect(data.budget).toBe("Budget missing");
  });
});
