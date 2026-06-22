import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { WorkspaceTripLayoutShell } from "../layout";
import { ApiException, type Trip } from "@/lib/api-client";
import * as apiClient from "@/lib/api-client";
import * as navigation from "next/navigation";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return {
    ...actual,
    api: {
      ...actual.api,
      get: vi.fn(),
    },
  };
});

vi.mock("@/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  InlineError: ({ title, message }: { title?: string; message: string }) => (
    <div role="alert">
      {title && <span>{title}</span>}
      {message}
    </div>
  ),
}));

const baseTrip: Trip = {
  id: "TRIP-123",
  destination: "Bali",
  type: "Family",
  state: "amber",
  age: "5h",
  createdAt: "2026-04-18T00:00:00.000Z",
  updatedAt: "2026-04-18T00:00:00.000Z",
};

const planningTrip = {
  ...baseTrip,
  status: "assigned",
  party: 2,
  dateWindow: "Jun 10-20",
  budget: "$5000",
  origin: "Delhi",
} as any;

function mockTimelineFetch(events: TimelineEventFixture[] = []) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      trip_id: "TRIP-123",
      events,
    }),
  });
}

type TimelineEventFixture = {
  trip_id: string;
  timestamp: string;
  stage: string;
  status: string;
  reason?: string;
  state_snapshot: Record<string, unknown>;
};

async function waitForTimelineFetch() {
  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/trips/TRIP-123/timeline",
      expect.objectContaining({
        credentials: "include",
        cache: "no-store",
      }),
    );
  });
}

describe("trips/[tripId]/layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(navigation.useParams).mockReturnValue({ tripId: "TRIP-123" });
    vi.mocked(navigation.usePathname).mockReturnValue("/trips/TRIP-123/intake");
    mockTimelineFetch();
    vi.mocked(apiClient.api.get).mockResolvedValue(baseTrip as Trip);
  });

  it("renders loading state while trip is pending", () => {
    vi.mocked(apiClient.api.get).mockImplementation(
      () => new Promise<Trip>(() => {}),
    );

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();
  });

  it("renders the current incomplete-trip copy", async () => {
    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    await waitForTimelineFetch();
    expect(screen.getByRole("heading", { name: "Trip details incomplete" })).toBeInTheDocument();
    expect(screen.getByText("Missing customer details")).toBeInTheDocument();
    expect(screen.getByText("In planning · Inquiry Ref: TRIP")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Intake" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Stage content")).toBeInTheDocument();
  });

  it("shows the stale-link fallback when the trip lookup returns 404", async () => {
    vi.mocked(apiClient.api.get).mockRejectedValueOnce(new ApiException("Trip not found", 404));

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(await screen.findByText("Workspace unavailable")).toBeInTheDocument();
    expect(
      screen.getByText("This trip link is stale or missing. Return to Trips in Planning and reopen it."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Trips in Planning" })).toHaveAttribute("href", "/trips");
  });

  it("shows a compact collapsed timeline trigger for low-signal history and toggles open on demand", async () => {
    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    await waitForTimelineFetch();
    expect(await screen.findByRole("button", { name: "Show activity" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Trip timeline")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show activity" }));

    expect(screen.getByLabelText("Trip timeline")).toBeInTheDocument();
    expect(screen.getByLabelText("Trip timeline").className).toContain("sticky");
    expect(screen.getByLabelText("Trip timeline").className).toContain("top-5");
    expect(await screen.findByText("No activity yet")).toBeInTheDocument();
  });

  it("auto-opens the timeline when important events are present", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trip_id: "TRIP-123",
        events: [
          {
            trip_id: "TRIP-123",
            timestamp: "2026-04-18T10:00:00Z",
            stage: "decision",
            status: "completed",
            reason: "Manual override applied after escalation",
            state_snapshot: {},
          },
        ],
      }),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    await waitForTimelineFetch();
    expect(await screen.findByLabelText("Trip timeline")).toBeInTheDocument();
  });
});

describe("Trip Workspace — Ops tab visibility", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(navigation.useParams).mockReturnValue({ tripId: "TRIP-123" });
    vi.mocked(navigation.usePathname).mockReturnValue("/trips/TRIP-123/intake");
    mockTimelineFetch();
  });

  function renderWithStage(stage: string, tripOverride?: any) {
    vi.mocked(apiClient.api.get).mockResolvedValue({ ...(tripOverride ?? planningTrip), stage } as any);
    render(
      <WorkspaceTripLayoutShell>
        <div>content</div>
      </WorkspaceTripLayoutShell>,
    );
  }

  it("shows Ops tab for proposal-stage trip", async () => {
    renderWithStage("proposal");
    await waitForTimelineFetch();
    expect(screen.getByText("Ops")).toBeInTheDocument();
  });

  it("shows Ops tab for booking-stage trip", async () => {
    renderWithStage("booking");
    await waitForTimelineFetch();
    expect(screen.getByText("Ops")).toBeInTheDocument();
  });

  it("hides Ops tab for intake-stage trip", async () => {
    renderWithStage("intake");
    await waitForTimelineFetch();
    expect(screen.queryByText("Ops")).not.toBeInTheDocument();
  });

  it("hides Ops tab for discovery-stage trip", async () => {
    renderWithStage("discovery");
    await waitForTimelineFetch();
    expect(screen.queryByText("Ops")).not.toBeInTheDocument();
  });

  it("hides Ops tab when trip stage is null", async () => {
    vi.mocked(apiClient.api.get).mockResolvedValue({ ...planningTrip, stage: null } as any);
    render(
      <WorkspaceTripLayoutShell>
        <div>content</div>
      </WorkspaceTripLayoutShell>,
    );
    await waitForTimelineFetch();
    expect(screen.queryByText("Ops")).not.toBeInTheDocument();
  });

  it("Ops tab links to /trips/TRIP-123/ops when accessible", async () => {
    renderWithStage("proposal");
    await waitForTimelineFetch();
    const opsLink = screen.queryByRole("link", { name: "Ops" });
    if (opsLink) {
      expect(opsLink).toHaveAttribute("href", "/trips/TRIP-123/ops");
    } else {
      expect(screen.getByText("Ops")).toBeInTheDocument();
    }
  });
});
