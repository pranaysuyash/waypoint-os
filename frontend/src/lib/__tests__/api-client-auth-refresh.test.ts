import http from "node:http";
import { describe, expect, it } from "vitest";
import { ApiClient } from "../api-client";

async function startServer(): Promise<{
  origin: string;
  close: () => Promise<void>;
}> {
  let tripHits = 0;
  const server = http.createServer(async (req, res) => {
    if (req.url === "/api/trips/trip-1" && req.method === "GET") {
      tripHits += 1;
      if (tripHits === 1) {
        res.writeHead(401, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ message: "Unauthorized" }));
        return;
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true, trip_id: "trip-1" }));
      return;
    }

    if (req.url === "/api/auth/refresh" && req.method === "POST") {
      res.writeHead(200, {
        "Content-Type": "application/json",
        "Set-Cookie": "access_token=refreshed; Path=/; HttpOnly",
      });
      res.end(JSON.stringify({ ok: true }));
      return;
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "not found" }));
  });

  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Failed to start test server");
  }
  return {
    origin: `http://127.0.0.1:${address.port}`,
    close: () =>
      new Promise<void>((resolve, reject) => {
        server.close((err) => (err ? reject(err) : resolve()));
      }),
  };
}

describe("api-client auth refresh retry", () => {
  it("refreshes once on 401 and retries the original request", async () => {
    const { origin, close } = await startServer();
    const client = new ApiClient({ baseUrl: origin });
    const events: string[] = [];
    window.addEventListener("waypoint:auth-unauthorized", () => events.push("unauthorized"));

    try {
      const result = await client.get<{ ok: boolean; trip_id: string }>("/api/trips/trip-1");

      expect(result.trip_id).toBe("trip-1");
      expect(events).toEqual([]);
    } finally {
      await close();
    }
  });
});
