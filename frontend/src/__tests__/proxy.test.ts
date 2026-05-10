import { describe, expect, it, vi } from "vitest";

const { proxy } = await import("../proxy");

import type { NextRequest } from "next/server";

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
    for (const page of ["/", "/v2", "/itinerary-checker", "/login", "/signup", "/forgot-password", "/reset-password"]) {
      const req = mockRequest(page);
      const res = await proxy(req);
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
    for (const path of paths) {
      const req = mockRequest(path);
      const res = await proxy(req);
      expect(res.status).not.toBe(307);
    }
  });

  it("allows refresh_token-only requests through protected pages", async () => {
    const req = mockRequest("/overview", { refresh_token: "valid-refresh" });
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("redirects auth-looking user on /login to safe protected destination", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" });
    const res = await proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("redirects auth-looking user on /login with redirect param to target", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/inbox");
    const res = await proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/inbox");
    expect(loc).not.toContain("/login");
  });

  it("ignores redirect=https://evil.com (external)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=https://evil.com");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("evil.com");
  });

  it("ignores redirect=//evil.com (protocol-relative)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=//evil.com");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("evil.com");
  });

  it("ignores redirect=/login to prevent redirect loop", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/login");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("ignores redirect=/signup to prevent redirect loop", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/signup");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("ignores redirect=/login?next=/overview to prevent auth-page redirect loops", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/login?next=/overview");
    const res = await proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("/login?next=");
  });

  it("ignores redirect=/signup?invite=abc to prevent auth-page redirect loops", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/signup?invite=abc");
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

  it("allows public /itinerary-checker/shared/[id] without auth", async () => {
    const req = mockRequest("/itinerary-checker/shared/abc-123");
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("allows public /itinerary/shared/[id] without auth", async () => {
    const req = mockRequest("/itinerary/shared/xyz-456");
    const res = await proxy(req);
    expect(res.status).not.toBe(307);
  });
});
