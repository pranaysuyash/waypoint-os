import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
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

describe("trips/[tripId]/layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(navigation.useParams).mockReturnValue({ tripId: "TRIP-123" });
    vi.mocked(navigation.usePathname).mockReturnValue("/trips/TRIP-123/intake");
  });

  it("renders loading state while trip is pending", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.getByText("Loading workspace...")).toBeInTheDocument();
  });

  it("renders trip header and stage tabs", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: baseTrip,
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

    expect(screen.getByRole("heading", { name: "Bali" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Intake" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Quote Assessment" })).toBeInTheDocument();
    expect(screen.getByText("Stage content")).toBeInTheDocument();
  });

  it("keeps timeline panel collapsed by default and toggles open", async () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: baseTrip,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      replaceTrip: vi.fn(),
    });

    // Mock fetch for TimelinePanel
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

    expect(screen.queryByLabelText("Trip timeline")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show timeline" }));

    expect(screen.getByLabelText("Trip timeline")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Decision Timeline" })).toBeInTheDocument();
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
    expect(screen.getByRole("link", { name: "Back to Workspaces" })).toBeInTheDocument();
  });
});
