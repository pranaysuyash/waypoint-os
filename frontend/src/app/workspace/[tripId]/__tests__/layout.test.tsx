import { describe, it, expect, vi, beforeEach } from "vitest";
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

const baseTrip: Trip = {
  id: "TRIP-123",
  destination: "Bali",
  type: "Family",
  state: "amber",
  age: "5h",
  createdAt: "2026-04-18T00:00:00.000Z",
  updatedAt: "2026-04-18T00:00:00.000Z",
};

describe("workspace/[tripId]/layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(navigation.useParams).mockReturnValue({ tripId: "TRIP-123" });
    vi.mocked(navigation.usePathname).mockReturnValue("/workspace/TRIP-123/intake");
  });

  it("renders loading state while trip is pending", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
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
    expect(screen.getByRole("link", { name: "Decision" })).toBeInTheDocument();
    expect(screen.getByText("Stage content")).toBeInTheDocument();
  });

  it("keeps right rail collapsed by default and toggles open", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: baseTrip,
      isLoading: false,
      error: null,
    });

    render(
      <WorkspaceTripLayoutShell>
        <div>Stage content</div>
      </WorkspaceTripLayoutShell>,
    );

    expect(screen.queryByText("AI Copilot Panel")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show AI rail" }));

    expect(screen.getByText("AI Copilot Panel")).toBeInTheDocument();
  });

  it("renders not-found/error fallback when trip fails", () => {
    vi.mocked(tripsHook.useTrip).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Trip lookup failed"),
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
