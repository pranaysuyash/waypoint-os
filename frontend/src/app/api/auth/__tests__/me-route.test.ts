import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { GET } from "../me/route";
import type { NextRequest } from "next/server";
import { refreshAuthCookies } from "@/lib/bff-auth";

vi.mock("@/lib/bff-auth", async (importOriginal) => {
  const actual: Record<string, unknown> = await importOriginal() as Record<string, unknown>;
  return {
    ...actual,
    bffFetchOptions: vi.fn(() => ({
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store" as RequestCache,
    })),
    refreshAuthCookies: vi.fn(async () => ["access_token=new_access; Path=/; HttpOnly"]),
    mergeCookieHeader: vi.fn(() => "access_token=new_access; refresh_token=valid"),
  };
});

function asNextRequest(request: Request): NextRequest {
  return request as unknown as NextRequest;
}

describe("/api/auth/me GET - auth refresh retry", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("refreshes auth cookies and retries when the first auth/me call returns 401", async () => {
    const fetchMock = vi.spyOn(global, "fetch");

    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ error: "unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ user: { id: "u1", email: "newuser@test.com" } }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    const request = new Request("http://localhost:3000/api/auth/me", {
      headers: {
        cookie: "access_token=expired; refresh_token=valid",
      },
    });

    const response = await GET(asNextRequest(request));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toEqual({ user: { id: "u1", email: "newuser@test.com" } });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(vi.mocked(refreshAuthCookies)).toHaveBeenCalledTimes(1);
  });
});
