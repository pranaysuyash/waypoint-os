import { describe, expect, it } from "vitest";
import { bffHeaders, isAuthStatus, noStoreHeaders } from "../bff-auth";
import type { NextRequest } from "next/server";

function mockRequest(cookies: Record<string, string> = {}): NextRequest {
  return {
    cookies: {
      get: (name: string) => {
        const value = cookies[name];
        return value ? { value } : undefined;
      },
    },
  } as unknown as NextRequest;
}

describe("bffHeaders", () => {
  it("forwards access_token cookie", () => {
    const req = mockRequest({ access_token: "jwt-token" });
    const headers = bffHeaders(req);
    expect(headers["Cookie"]).toBe("access_token=jwt-token");
    expect(headers["Accept"]).toBe("application/json");
  });

  it("does not send Cookie header when no auth cookies exist", () => {
    const req = mockRequest();
    const headers = bffHeaders(req);
    expect(headers["Cookie"]).toBeUndefined();
    expect(headers["Accept"]).toBe("application/json");
  });

  it("forwards both cookies with access_and_refresh scope", () => {
    const req = mockRequest({ access_token: "access", refresh_token: "refresh" });
    const headers = bffHeaders(req, "access_and_refresh");
    expect(headers["Cookie"]).toBe("access_token=access; refresh_token=refresh");
  });

  it("forwards only access_token by default", () => {
    const req = mockRequest({ access_token: "access", refresh_token: "refresh" });
    const headers = bffHeaders(req);
    expect(headers["Cookie"]).toBe("access_token=access");
    expect(headers["Cookie"]).not.toContain("refresh_token");
  });

  it("merges extra headers", () => {
    const req = mockRequest({ access_token: "jwt" });
    const headers = bffHeaders(req, "access_only", { "Content-Type": "application/json" });
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["Cookie"]).toBe("access_token=jwt");
  });

  it("does not forward non-auth cookies", () => {
    const req = mockRequest({ access_token: "jwt", analytics_id: "abc", theme: "dark" });
    const headers = bffHeaders(req);
    expect(headers["Cookie"]).toBe("access_token=jwt");
    expect(headers["Cookie"]).not.toContain("analytics_id");
    expect(headers["Cookie"]).not.toContain("theme");
  });
});

describe("isAuthStatus", () => {
  it("returns true for 401", () => {
    expect(isAuthStatus(401)).toBe(true);
  });

  it("returns true for 403", () => {
    expect(isAuthStatus(403)).toBe(true);
  });

  it("returns false for 200", () => {
    expect(isAuthStatus(200)).toBe(false);
  });

  it("returns false for 404", () => {
    expect(isAuthStatus(404)).toBe(false);
  });

  it("returns false for 500", () => {
    expect(isAuthStatus(500)).toBe(false);
  });
});

describe("noStoreHeaders", () => {
  it("returns Cache-Control: no-store", () => {
    const headers = noStoreHeaders();
    expect(headers).toEqual({ "Cache-Control": "no-store" });
  });
});
