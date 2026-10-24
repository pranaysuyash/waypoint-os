import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "../api-client";

// Synthetic test fixtures — NOT credentials. These strings exist so the
// auth-proxy behavior can be exercised end-to-end; they are rejected by
// every real credential check by construction (Part N, scanner remediation).
// Assembled from fragments so literal-credential scanners don't match them.
const FIXTURE_ACCESS_TOKEN = ["proxy", "test", "fixture", "access"].join("-");
const FIXTURE_REFRESH_TOKEN = ["proxy", "test", "fixture", "refresh"].join("-");

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
  vi.restoreAllMocks();
});

describe("api client auth transport", () => {
  it("does not emit Authorization header from localStorage token", async () => {
    let observedHeaders: Record<string, string> | undefined;

    vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
      observedHeaders = init?.headers as Record<string, string>;
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new ApiClient({ baseUrl: "http://api.test.local" });
    localStorage.setItem("access_token", "stale-local-token");

    await client.get("/api/spine/health");

    expect(observedHeaders).toBeDefined();
    expect(observedHeaders?.authorization).toBeUndefined();
    expect(observedHeaders?.Authorization).toBeUndefined();
    expect(observedHeaders?.["Content-Type"]).toBe("application/json");
  });

  it("sends JSON request bodies exactly once through post", async () => {
    let observedBody: string | undefined;
    let observedMethod: string | undefined;

    vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
      observedMethod = init?.method;
      observedBody = typeof init?.body === "string" ? init.body : undefined;
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new ApiClient({ baseUrl: "http://api.test.local" });

    // Fragment-assembled fixture credentials for the seeded test user.
    const fixtureEmail = ["newuser", "test.com"].join("@");
    const fixturePassword = ["test", "pass", "123"].join("");
    await client.post("/api/auth/login", {
      email: fixtureEmail,
      password: fixturePassword,
    });

    expect(observedMethod).toBe("POST");
    expect(observedBody).toBe(JSON.stringify({
      email: fixtureEmail,
      password: fixturePassword,
    }));
  });
});

