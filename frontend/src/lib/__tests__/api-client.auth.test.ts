import http from "node:http";
import { afterEach, describe, expect, it } from "vitest";
import { ApiClient } from "../api-client";

const localStorageMock = {
  store: {} as Record<string, string>,
  getItem: (key: string) => localStorageMock.store[key] ?? null,
  setItem: (key: string, value: string) => {
    localStorageMock.store[key] = String(value);
  },
  removeItem: (key: string) => {
    delete localStorageMock.store[key];
  },
  clear: () => {
    localStorageMock.store = {};
  },
  key: () => null,
  length: 0,
} as Storage & { store: Record<string, string> };

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
  configurable: true,
});

afterEach(() => {
  localStorageMock.clear();
});

async function startServer(handler: http.RequestListener): Promise<{
  origin: string;
  close: () => Promise<void>;
}> {
  const server = http.createServer(handler);
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

describe("api client auth transport", () => {
  it("does not emit Authorization header from localStorage token", async () => {
    let observedHeaders: http.IncomingHttpHeaders | undefined;
    const { origin, close } = await startServer((req, res) => {
      observedHeaders = req.headers;
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true }));
    });

    try {
      const client = new ApiClient({ baseUrl: origin });
      localStorage.setItem("access_token", "stale-local-token");

      await client.get("/api/spine/health");

      expect(observedHeaders).toBeDefined();
      const capturedHeaders = observedHeaders as http.IncomingHttpHeaders;
      expect(capturedHeaders.authorization).toBeUndefined();
      expect(capturedHeaders["content-type"]).toBe("application/json");
      expect(capturedHeaders.cookie).toBeUndefined();
    } finally {
      await close();
    }
  });

  it("sends JSON request bodies exactly once through post", async () => {
    let observedBody = "";
    let observedMethod = "";
    const { origin, close } = await startServer(async (req, res) => {
      observedMethod = req.method ?? "";
      const chunks: Buffer[] = [];
      for await (const chunk of req) {
        chunks.push(Buffer.from(chunk));
      }
      observedBody = Buffer.concat(chunks).toString("utf8");
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true }));
    });

    try {
      const client = new ApiClient({ baseUrl: origin });

      await client.post("/api/auth/login", {
        email: "newuser@test.com",
        password: "testpass123",
      });

      expect(observedMethod).toBe("POST");
      expect(observedBody).toBe(JSON.stringify({
        email: "newuser@test.com",
        password: "testpass123",
      }));
    } finally {
      await close();
    }
  });
});
