import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { GET } from "../route";
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

describe("/api/trips/[id] GET - auth refresh retry", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("refreshes auth cookies and retries the trip fetch after a 401", async () => {
    const fetchMock = vi.spyOn(global, "fetch");

    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ error: "unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "trip_123",
            destination: "Zanzibar",
            origin: "Nairobi",
            status: "assigned",
            created_at: "2026-06-23T00:00:00.000Z",
            updated_at: "2026-06-23T00:00:00.000Z",
            extracted: { facts: {} },
            validation: { warnings: [] },
            decision: { hard_blockers: [], soft_blockers: [] },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }
        )
      );

    const request = new Request("http://localhost:3000/api/trips/trip_123", {
      headers: {
        cookie: "access_token=expired; refresh_token=valid",
      },
    });

    const response = await GET(asNextRequest(request), { params: Promise.resolve({ id: "trip_123" }) });
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toHaveProperty("id", "trip_123");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(vi.mocked(refreshAuthCookies)).toHaveBeenCalledTimes(1);
  });
});
