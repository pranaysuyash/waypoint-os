import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

vi.mock("@/lib/bff-auth", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/bff-auth")>();
  return {
    ...actual,
    bffFetchOptions: vi.fn().mockResolvedValue({
      headers: { Authorization: "Bearer test-token" },
    }),
  };
});

vi.mock("@/lib/bff-trip-adapters", () => ({
  transformSpineTripsResponseToTrips: vi.fn(() => []),
  isWorkspaceTrip: vi.fn((trip: { stage?: string }) => trip.stage !== "intake"),
}));

import { GET } from "../route";

describe("/api/pipeline statusCounts SSOT", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses SQL statusCounts so totals do not cap at 10,000 items", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            items: [],
            total: 48767,
            statusCounts: {
              in_progress: 1849,
              assigned: 42218,
              active: 202,
              blocked: 5,
              completed: 13,
              new: 3896,
              incomplete: 582,
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const res = await GET(new NextRequest("http://localhost/api/pipeline"));
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(Array.isArray(data)).toBe(true);
    expect(data).toEqual(
      expect.arrayContaining([
        { label: "assigned", count: 42218 },
        { label: "in_progress", count: 1849 },
        { label: "active", count: 202 },
        { label: "blocked", count: 5 },
      ]),
    );
  });
});
