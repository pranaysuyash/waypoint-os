import { describe, expect, it, vi, afterEach } from "vitest";
import { api, getScenarios } from "../api-client";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("getScenarios", () => {
  it("unwraps envelope responses with items", async () => {
    vi.spyOn(api, "get").mockResolvedValueOnce({
      items: [
        { id: "SC-1", title: "Alpha" },
        { id: "SC-2", title: "Beta" },
      ],
    } as never);

    await expect(getScenarios()).resolves.toEqual([
      { id: "SC-1", title: "Alpha" },
      { id: "SC-2", title: "Beta" },
    ]);
  });

  it("passes through raw array responses", async () => {
    vi.spyOn(api, "get").mockResolvedValueOnce([
      { id: "SC-3", title: "Gamma" },
    ] as never);

    await expect(getScenarios()).resolves.toEqual([
      { id: "SC-3", title: "Gamma" },
    ]);
  });
});
