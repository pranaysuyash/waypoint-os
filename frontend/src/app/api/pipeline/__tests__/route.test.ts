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
  };
});

vi.mock("@/lib/bff-trip-adapters", () => ({
  transformSpineTripsResponseToTrips: vi.fn(),
  isWorkspaceTrip: vi.fn(),
}));

import { transformSpineTripsResponseToTrips, isWorkspaceTrip } from "@/lib/bff-trip-adapters";

function asNextRequest(request: Request): NextRequest {
  return request as unknown as NextRequest;
}

const WORKSPACE_TRIP = { id: "t1", status: "assigned", state: "amber" };
const IN_PROGRESS_TRIP = { id: "t2", status: "in_progress", state: "amber" };
const QUOTE_TRIP = { id: "t3", status: "ready_to_quote", state: "red" };
const BOOK_TRIP = { id: "t4", status: "ready_to_book", state: "green" };
const BLOCKED_TRIP = { id: "t5", status: "blocked", state: "red" };
const NEW_TRIP = { id: "t6", status: "new", state: "blue" };
const COMPLETED_TRIP = { id: "t7", status: "completed", state: "green" };
const CANCELLED_TRIP = { id: "t8", status: "cancelled", state: "red" };

function mockBackendResponse(data: unknown) {
  vi.spyOn(global, "fetch").mockResolvedValueOnce(
    new Response(JSON.stringify({ items: data }), {
      status: 200,
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
    mockBackendResponse([WORKSPACE_TRIP, BLOCKED_TRIP]);

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);
    const data = await response.json();

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
    mockBackendResponse([BOOK_TRIP]);

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);
    const data = await response.json();

    expect(data).toHaveLength(5);
    data.forEach((stage: { label: string; count: number }) => {
      expect(stage).toHaveProperty("label");
      expect(stage).toHaveProperty("count");
    });
    expect(data.find((s: { label: string }) => s.label === "in_progress")?.count).toBe(0);
    expect(data.find((s: { label: string }) => s.label === "ready_to_quote")?.count).toBe(0);
  });

  it("excludes new, completed, and cancelled from counts", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([
      WORKSPACE_TRIP,
      NEW_TRIP,
      COMPLETED_TRIP,
      CANCELLED_TRIP,
    ]);
    mockBackendResponse([WORKSPACE_TRIP, NEW_TRIP, COMPLETED_TRIP, CANCELLED_TRIP]);

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);
    const data = await response.json();

    const assigned = data.find((s: { label: string }) => s.label === "assigned");
    expect(assigned.count).toBe(1);
    expect(data.find((s: { label: string }) => s.label === "ready_to_book")?.count).toBe(0);
  });

  it("does not return analytics fields", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([WORKSPACE_TRIP]);
    mockBackendResponse([WORKSPACE_TRIP]);

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);
    const data = await response.json();

    expect(data[0]).not.toHaveProperty("stageId");
    expect(data[0]).not.toHaveProperty("stageName");
    expect(data[0]).not.toHaveProperty("tripCount");
    expect(data[0]).not.toHaveProperty("avgTimeInStage");
    expect(data[0]).not.toHaveProperty("exitRate");
    expect(data[0]).not.toHaveProperty("avgTimeToExit");
  });

  it("preserves auth errors from the backend", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "Not authenticated" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);

    expect(response.status).toBe(401);
    const data = await response.json();
    expect(data).toHaveProperty("error");
  });

  it("returns all five stages in the correct order", async () => {
    vi.mocked(transformSpineTripsResponseToTrips).mockReturnValue([]);
    mockBackendResponse([]);

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);
    const data = await response.json();

    expect(data).toBeInstanceOf(Array);
    const labels = (data as Array<{ label: string }>).map((s) => s.label);
    expect(labels).toEqual([
      "assigned",
      "in_progress",
      "ready_to_quote",
      "ready_to_book",
      "blocked",
    ]);
  });

  it("handles backend errors gracefully", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(null, { status: 500 }),
    );

    const request = asNextRequest(new Request("http://localhost:3000/api/pipeline"));
    const response = await GET(request);

    expect(response.status).toBe(500);
    const data = await response.json();
    expect(data).toHaveProperty("error");
  });
});
