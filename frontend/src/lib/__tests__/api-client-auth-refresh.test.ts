import { describe, expect, it, vi, afterEach } from "vitest";
import { ApiClient } from "../api-client";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api-client auth refresh retry", () => {
  it("refreshes once on 401 and retries the original request", async () => {
    let tripHits = 0;
    let refreshHits = 0;

    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
      const urlStr = String(url);
      if (urlStr.endsWith("/api/trips/trip-1")) {
        tripHits += 1;
        if (tripHits === 1) {
          return new Response(JSON.stringify({ message: "Unauthorized" }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify({ ok: true, trip_id: "trip-1" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (urlStr.endsWith("/api/auth/refresh")) {
        refreshHits += 1;
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Set-Cookie": "access_token=refreshed; Path=/; HttpOnly",
          },
        });
      }

      return new Response(JSON.stringify({ error: "not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new ApiClient({ baseUrl: "http://api.test.local" });
    const events: string[] = [];
    window.addEventListener("waypoint:auth-unauthorized", () => events.push("unauthorized"));

    const result = await client.get<{ ok: boolean; trip_id: string }>("/api/trips/trip-1");

    expect(result.trip_id).toBe("trip-1");
    expect(tripHits).toBe(2);
    expect(refreshHits).toBe(1);
    expect(events).toEqual([]);
  });
});

