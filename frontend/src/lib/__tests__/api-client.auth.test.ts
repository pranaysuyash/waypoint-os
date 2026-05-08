import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api-client";

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

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: localStorageMock,
    configurable: true,
  });
  localStorageMock.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api client auth transport", () => {
  it("does not emit Authorization header from localStorage token", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    localStorage.setItem("access_token", "stale-local-token");

    await api.get("/api/spine/health");

    expect(fetchSpy).toHaveBeenCalledOnce();
    const [, init] = fetchSpy.mock.calls[0];
    const headers = new Headers(init?.headers as HeadersInit);

    expect(headers.get("Authorization")).toBeNull();
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init?.credentials).toBe("include");
  });
});
