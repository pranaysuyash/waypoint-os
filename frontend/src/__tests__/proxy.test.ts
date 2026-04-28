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
  it("redirects unauthenticated protected route to /login with pathname + query preserved", () => {
    const req = mockRequest("/trips/123", {}, "?tab=reviews");
    const res = proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/login");
    expect(loc).toContain("redirect=%2Ftrips%2F123%3Ftab%3Dreviews");
  });

  it("passes through unauthenticated /api/* requests", () => {
    const req = mockRequest("/api/trips");
    const res = proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("passes through public pages without redirect", () => {
    for (const page of ["/", "/v2", "/itinerary-checker", "/login", "/signup", "/forgot-password", "/reset-password"]) {
      const req = mockRequest(page);
      const res = proxy(req);
      expect(res.status).not.toBe(307);
    }
  });

  it("passes through public metadata and static files", () => {
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
      const res = proxy(req);
      expect(res.status).not.toBe(307);
    }
  });

  it("allows refresh_token-only requests through protected pages", () => {
    const req = mockRequest("/overview", { refresh_token: "valid-refresh" });
    const res = proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("redirects auth-looking user on /login to safe protected destination", () => {
    const req = mockRequest("/login", { access_token: "valid-token" });
    const res = proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("redirects auth-looking user on /login with redirect param to target", () => {
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/inbox");
    const res = proxy(req);
    expect(res.status).toBe(307);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/inbox");
    expect(loc).not.toContain("/login");
  });

  it("ignores redirect=https://evil.com (external)", () => {
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=https://evil.com");
    const res = proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("evil.com");
  });

  it("ignores redirect=//evil.com (protocol-relative)", () => {
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=//evil.com");
    const res = proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
    expect(loc).not.toContain("evil.com");
  });

  it("ignores redirect=/login to prevent redirect loop", () => {
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/login");
    const res = proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("ignores redirect=/signup to prevent redirect loop", () => {
    const req = mockRequest("/login", { access_token: "valid-token" }, "?redirect=/signup");
    const res = proxy(req);
    const loc = redirectLocation(res)!;
    expect(loc).toContain("/overview");
  });

  it("allows tokenized /reset-password/abc123 without auth", () => {
    const req = mockRequest("/reset-password/abc123");
    const res = proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("allows public /itinerary-checker/shared/[id] without auth", () => {
    const req = mockRequest("/itinerary-checker/shared/abc-123");
    const res = proxy(req);
    expect(res.status).not.toBe(307);
  });

  it("allows public /itinerary/shared/[id] without auth", () => {
    const req = mockRequest("/itinerary/shared/xyz-456");
    const res = proxy(req);
    expect(res.status).not.toBe(307);
  });
});
