import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { WorkspaceTripLayoutShell } from "../layout";
import type { Trip } from "@/lib/api-client";
import * as navigation from "next/navigation";
import * as tripsHook from "@/hooks/useTrips";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock("@/hooks/useTrips", () => ({
  useTrip: vi.fn(),
}));

vi.mock("@/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  InlineError: ({ title, message }: { title?: string; message: string }) => (
    <div role="alert">{title && <span>{title}</span>}{message}</div>
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
  });

  it("renders loading state while trip is pending", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    act(() => {
      render(
        <WorkspaceTripLayoutShell>
          <div>Stage content</div>
        </WorkspaceTripLayoutShell>,
      );
    });

    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();
  });

  it("renders trip header and stage tabs", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: {
        ...baseTrip,
        status: "assigned",
        party: 4,
        dateWindow: "Feb 9-14",
        budget: "$6000",
        origin: "Delhi",
        decision: {
          decision_state: "PROCEED_INTERNAL_DRAFT",
          hard_blockers: [],
          soft_blockers: [],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          rationale: {} as any,
          confidence: {} as any,
          branch_options: [],
          commercial_decision: "NONE",
          budget_breakdown: null,
        },
        validation: {
          warnings: [],
        },
      } as any,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByRole("heading", { name: "Bali family trip" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Intake" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Quote Assessment" })).toBeInTheDocument();
    expect(screen.getByText("Stage content")).toBeInTheDocument();
    await waitForTimelineFetch();
  });

  it("uses lead-review header copy for incomplete leads", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: {
        ...baseTrip,
        id: "trip_4b9e0d894872",
        destination: "Singapore",
        type: "Family Leisure",
        status: "incomplete",
        state: "blue",
        party: 5,
        dateWindow: "around 9th to 14th Feb",
        budget: "$0",
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByRole("heading", { name: "Singapore family trip" })).toBeInTheDocument();
    expect(screen.getByText(/5 pax · Around Feb 9–14/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Trips in Planning" })).toHaveAttribute("href", "/trips");
    expect(screen.queryByText("trip_4b9e0d894872")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Quote Assessment" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Options" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Output" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Risk Review" })).not.toBeInTheDocument();
    await waitForTimelineFetch();
  });

  it("uses planning header copy for trips in planning that still need customer details", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: {
        ...baseTrip,
        id: "trip_4b9e0d894872",
        destination: "Singapore",
        type: "Family Leisure",
        status: "assigned",
        state: "amber",
        party: 5,
        dateWindow: "around 9th to 14th Feb",
        budget: "$0",
        rawInput: { fixture_id: "SC-901" },
        decision: {
          decision_state: "ASK_FOLLOWUP",
          hard_blockers: [],
          soft_blockers: ["incomplete_intake"],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          rationale: {} as any,
          confidence: {} as any,
          branch_options: [],
          commercial_decision: "NONE",
          budget_breakdown: null,
        },
        validation: {
          warnings: [
            { severity: "warning", code: "QUOTE_READY_INCOMPLETE", message: "budget missing", field: "budget_raw_text" },
          ],
        },
      } as any,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByRole("heading", { name: "Singapore family trip" })).toBeInTheDocument();
    expect(screen.getByText(/In planning · Inquiry Ref: 4B9E/i)).toBeInTheDocument();
    expect(screen.queryByText("trip_4b9e0d894872")).not.toBeInTheDocument();
    expect(screen.queryByText("In Progress")).not.toBeInTheDocument();
    await waitForTimelineFetch();
  });

  it("keeps blocked planning stages visible but gated while required fields are missing", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: {
        ...baseTrip,
        id: "trip_4b9e0d894872",
        destination: "Singapore",
        type: "Family Leisure",
        status: "assigned",
        state: "amber",
        party: 5,
        dateWindow: "around 9th to 14th Feb",
        budget: "$0",
        origin: "TBD",
        rawInput: { fixture_id: "SC-901" },
        decision: {
          decision_state: "ASK_FOLLOWUP",
          hard_blockers: [],
          soft_blockers: ["incomplete_intake"],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          rationale: {} as any,
          confidence: {} as any,
          branch_options: [],
          commercial_decision: "NONE",
          budget_breakdown: null,
        },
        validation: {
          warnings: [
            { severity: "warning", code: "QUOTE_READY_INCOMPLETE", message: "origin missing", field: "origin_city" },
            { severity: "warning", code: "QUOTE_READY_INCOMPLETE", message: "budget missing", field: "budget_raw_text" },
          ],
        },
      } as any,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByRole("link", { name: "Intake" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Trip Details" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Timeline" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Quote Assessment" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Options" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Output" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Risk Review" })).not.toBeInTheDocument();
    expect(
      screen.getByText("Complete budget range and origin city to unlock quote, options, output, and risk review."),
    ).toBeInTheDocument();
    expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
    expect(screen.getAllByText("Options").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Budget + origin needed").length).toBeGreaterThan(0);
    await waitForTimelineFetch();
  });

  it("shows a compact collapsed timeline trigger for low-signal history and toggles open on demand", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: baseTrip,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    // Mock fetch for timeline metadata + panel
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trip_id: "TRIP-123",
        events: [
          {
            trip_id: "TRIP-123",
            timestamp: "2026-04-18T10:00:00Z",
            stage: "intake",
            status: "completed",
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

    expect(await screen.findByRole("button", { name: "Show activity" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Trip timeline")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show activity" }));

    expect(screen.getByLabelText("Trip timeline")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Timeline Summary" })).toBeInTheDocument();
  });

  it("auto-opens the timeline when important events are present", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: baseTrip,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

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

    expect(await screen.findByLabelText("Trip timeline")).toBeInTheDocument();
  });

  it("renders not-found/error fallback when trip fails", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Trip lookup failed"),
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByText("Workspace unavailable")).toBeInTheDocument();
    expect(screen.getByText("Trip lookup failed")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Trips in Planning" })).toBeInTheDocument();
  });
});
