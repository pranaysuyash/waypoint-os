import { describe, expect, it, vi } from "vitest";

const { proxy } = await import("../proxy");

import type { NextRequest } from "next/server";

// Synthetic test fixtures — NOT credentials. These strings exist so the
// auth-proxy behavior can be exercised end-to-end; they are rejected by
// every real credential check by construction (Part N, scanner remediation).
const FIXTURE_AUTH_COOKIE_VALUE = 'proxy-test-fixture-access-value';
const FIXTURE_SESSION_COOKIE_VALUE = 'proxy-test-fixture-refresh-value';


function mockRequest(path: string, cookies: Record<string, string> = {}, search: string = ""): NextRequest {
  const url = `http://localhost:3000${path}${search}`;
  const req = {
    nextUrl: new URL(url),
    url,
    cookies: {
      get: (name: string) => {
        const value = cookies[name];
        return value ? { value } : undefined;
      },
    },
    headers: {
      get: () => null,
    },
  } as unknown as NextRequest;
  return req;
}

function redirectLocation(response: Response): string | null {
  return response.headers.get("location");
}

describe("proxy.ts page guard", () => {
  it("allows unauthenticated protected route shell for in-app auth modal", async () => {
    const req = mockRequest("/trips/123", {}, "?tab=reviews");
    const res = await proxy(req);
    expect(res.status).toBe(200);
    expect(redirectLocation(res)).toBeNull();
  });

  it("passes through unauthenticated /api/* requests", async () => {
    const req = mockRequest("/api/trips");
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("passes through public pages without redirect", async () => {
    const pages = ["/", "/v2", "/itinerary-checker", "/login", "/signup", "/forgot-password", "/reset-password"];
    const results = await Promise.all(
      pages.map(async (page) => {
        const req = mockRequest(page);
        return proxy(req);
      })
    );
    for (const res of results) {
      expect(res.status).not.toBe(307);
    }
  });

  it("passes through public metadata and static files", async () => {
    const paths = [
      "/robots.txt",
      "/sitemap.xml",
      "/manifest.json",
      "/icon.png",
      "/apple-icon.png",
      "/_next/static/chunk.js",
      "/images/logo.png",
      "/favicon.ico",
    ];
    const results = await Promise.all(
      paths.map(async (path) => {
        const req = mockRequest(path);
        return proxy(req);
      })
    );
    for (const res of results) {
      expect(res.status).not.toBe(307);
    }
  });

  it("allows refresh_token-only requests through protected pages", async () => {
    const req = mockRequest("/overview", { refresh_token: FIXTURE_SESSION_COOKIE_VALUE });
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("redirects auth-looking user on /login to safe protected destination", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE });
    const res = await proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("redirects auth-looking user on /login with redirect param to target", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=/inbox");
    const res = await proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/inbox");
    expect(loc).not.toContain("/login");
  });

  it("ignores redirect=https://evil.com (external)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=https://evil.com");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("evil.com");
  });

  it("ignores redirect=//evil.com (protocol-relative)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=//evil.com");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("evil.com");
  });

  it("ignores redirect=/login to prevent redirect loop", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=/login");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("ignores redirect=/signup to prevent redirect loop", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=/signup");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("ignores redirect=/login?next=/overview to prevent auth-page redirect loops", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=/login?next=/overview");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("/login?next=");
  });

  it("ignores redirect=/signup?invite=abc to prevent auth-page redirect loops", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: FIXTURE_AUTH_COOKIE_VALUE }, "?redirect=/signup?invite=abc");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("/signup?invite=");
  });

  it("allows stale auth-looking users to reach /login when session validation fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));
    const req = mockRequest("/login", { access_token: "stale-token" }, "?redirect=/overview");
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("allows tokenized /reset-password/abc123 without auth", async () => {
    const req = mockRequest("/reset-password/abc123");
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("does not public-allowlist dead /itinerary-checker/shared/ route (no such page exists)", async () => {
    const sharedReq = mockRequest("/itinerary-checker/shared/abc-123");
    const sharedRes = await proxy(sharedReq);
    const plainReq = mockRequest("/trips/123");
    const plainRes = await proxy(plainReq);
    // No shared page exists; the dead public allowlist entry was removed, so the
    // path now follows the generic protected-route behavior (auth shell), exactly
    // like any other non-public path.
    expect(sharedRes.status).toBe(plainRes.status);
  });
});
