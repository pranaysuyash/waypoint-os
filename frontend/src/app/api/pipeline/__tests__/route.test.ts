import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { GET } from "../route";
import type { NextRequest } from "next/server";

vi.mock("@/lib/bff-auth", async (importOriginal) => {
  const actual: Record<string, unknown> = await importOriginal() as Record<string, unknown>;
  return {
    ...actual,
    bffFetchOptions: vi.fn(() => ({
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store" as RequestCache,
    })),
    bffJson: vi.fn((data: unknown, status = 200) =>
      new Response(JSON.stringify(data), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  };
});

vi.mock("@/lib/bff-trip-adapters", () => ({
  transformSpineTripsResponseToTrips: vi.fn(),
  isWorkspaceTrip: vi.fn(),
}));

import { transformSpineTripsResponseToTrips, isWorkspaceTrip } from "@/lib/bff-trip-adapters";
import { bffJson } from "@/lib/bff-auth";

function asNextRequest(request: Request): NextRequest {
  return request as unknown as NextRequest;
}

const WORKSPACE_TRIP = { id: "t1", destination: "Tokyo", type: "leisure", state: "amber" as const, age: "2d", createdAt: "2026-05-01", updatedAt: "2026-05-03", status: "assigned" };
const BOOK_TRIP = { id: "t4", destination: "Paris", type: "leisure", state: "green" as const, age: "1d", createdAt: "2026-05-02", updatedAt: "2026-05-03", status: "ready_to_book" };
const BLOCKED_TRIP = { id: "t5", destination: "London", type: "business", state: "red" as const, age: "5d", createdAt: "2026-04-28", updatedAt: "2026-05-03", status: "blocked" };
const NEW_TRIP = { id: "t6", destination: "Berlin", type: "leisure", state: "blue" as const, age: "0d", createdAt: "2026-05-03", updatedAt: "2026-05-03", status: "new" };
const COMPLETED_TRIP = { id: "t7", destination: "Rome", type: "leisure", state: "green" as const, age: "14d", createdAt: "2026-04-19", updatedAt: "2026-05-03", status: "completed" };
const CANCELLED_TRIP = { id: "t8", destination: "Madrid", type: "business", state: "red" as const, age: "7d", createdAt: "2026-04-26", updatedAt: "2026-05-03", status: "cancelled" };

function mockBackend(data: unknown[], status = 200) {
  vi.spyOn(global, "fetch").mockResolvedValueOnce(
    new Response(JSON.stringify({ items: data }), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

describe("/api/pipeline GET - Operational Pipeline", () => {
  beforeEach(() => {
    vi.mocked(isWorkspaceTrip).mockImplementation(
      (trip: { status?: string }) =>
        ["assigned", "in_progress", "ready_to_quote", "ready_to_book", "blocked"].includes(trip.status ?? ""),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns only { label, count }[] in stable order", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([
      WORKSPACE_TRIP,
      BLOCKED_TRIP,
    ]);
    mockBackend([WORKSPACE_TRIP, BLOCKED_TRIP]);

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    const data = await res.json();

    expect(data).toEqual([
      { label: "assigned", count: 1 },
      { label: "in_progress", count: 0 },
      { label: "ready_to_quote", count: 0 },
      { label: "ready_to_book", count: 0 },
      { label: "blocked", count: 1 },
    ]);
  });

  it("includes zero-count stages", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([BOOK_TRIP]);
    mockBackend([BOOK_TRIP]);

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    const data = (await res.json()) as Array<{ label: string; count: number }>;

    expect(data).toHaveLength(5);
    data.forEach((s) => {
      expect(s).toHaveProperty("label");
      expect(s).toHaveProperty("count");
    });
    expect(data.find((s) => s.label === "in_progress")?.count).toBe(0);
    expect(data.find((s) => s.label === "ready_to_quote")?.count).toBe(0);
  });

  it("excludes new, completed, and cancelled from counts", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([
      WORKSPACE_TRIP,
      NEW_TRIP,
      COMPLETED_TRIP,
      CANCELLED_TRIP,
    ]);
    mockBackend([WORKSPACE_TRIP, NEW_TRIP, COMPLETED_TRIP, CANCELLED_TRIP]);

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    const data = (await res.json()) as Array<{ label: string; count: number }>;

    expect(data.find((s) => s.label === "assigned")?.count).toBe(1);
    expect(data.find((s) => s.label === "ready_to_book")?.count).toBe(0);
  });

  it("does not return analytics fields", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([WORKSPACE_TRIP]);
    mockBackend([WORKSPACE_TRIP]);

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    const data = (await res.json()) as Array<Record<string, unknown>>;

    expect(data[0]).not.toHaveProperty("stageId");
    expect(data[0]).not.toHaveProperty("stageName");
    expect(data[0]).not.toHaveProperty("tripCount");
    expect(data[0]).not.toHaveProperty("avgTimeInStage");
    expect(data[0]).not.toHaveProperty("exitRate");
    expect(data[0]).not.toHaveProperty("avgTimeToExit");
  });

  it("preserves auth status from backend", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "unauthenticated" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    expect(res.status).toBe(401);
    const data = await res.json();
    expect(data).toHaveProperty("error");
  });

  it("returns all five stages in correct order even when empty", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([]);
    mockBackend([]);

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    const data = (await res.json()) as Array<{ label: string }>;

    expect(data.map((s) => s.label)).toEqual([
      "assigned",
      "in_progress",
      "ready_to_quote",
      "ready_to_book",
      "blocked",
    ]);
  });

  it("handles backend server error gracefully", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(null, { status: 500 }),
    );
    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data).toHaveProperty("error");
  });

  it("counts trips with multiple statuses correctly", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([
      WORKSPACE_TRIP,
      WORKSPACE_TRIP,
      BOOK_TRIP,
      BLOCKED_TRIP,
    ]);
    mockBackend([WORKSPACE_TRIP, WORKSPACE_TRIP, BOOK_TRIP, BLOCKED_TRIP]);

    const res = await GET(asNextRequest(new Request("http://localhost:3000/api/pipeline")));
    const data = (await res.json()) as Array<{ label: string; count: number }>;

    expect(data.find((s) => s.label === "assigned")?.count).toBe(2);
    expect(data.find((s) => s.label === "ready_to_book")?.count).toBe(1);
    expect(data.find((s) => s.label === "blocked")?.count).toBe(1);
  });
});
