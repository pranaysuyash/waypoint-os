import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DecisionPanel } from "../DecisionPanel";
import { useWorkbenchStore } from "@/stores/workbench";
import type { Trip } from "@/lib/api-client";

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock("@/contexts/TripContext", () => ({
  useTripContext: vi.fn(() => ({
    replaceTrip: vi.fn(),
    refetchTrip: vi.fn(),
  })),
}));

vi.mock("@/lib/api-client", () => ({
  acknowledgeSuitabilityFlags: vi.fn(),
  transitionTripStage: vi.fn(),
}));

vi.mock("./SuitabilitySignal", () => ({
  SuitabilitySignal: () => <div data-testid="suitability-signal" />,
}));

vi.mock("./SuitabilityCard", () => ({
  SuitabilityCard: () => <div data-testid="suitability-card" />,
}));

const baseDecision = {
  decision_state: "PROCEED_INTERNAL_DRAFT",
  hard_blockers: [],
  soft_blockers: [],
  contradictions: [],
  risk_flags: [],
  follow_up_questions: [],
  rationale: {},
  confidence: { overall: 0.85 },
  branch_options: [],
  commercial_decision: "NONE",
  budget_breakdown: null,
};

const readinessWithAdvance = {
  highest_ready_tier: "quote_ready",
  suggested_next_stage: "shortlist",
  should_auto_advance_stage: false,
  missing_for_next: [],
};

describe("DecisionPanel stage advance button", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useWorkbenchStore as any).mockReturnValue({
      result_decision: baseDecision,
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      acknowledged_suitability_flags: [],
      acknowledgeFlag: vi.fn(),
    });
  });

  it("appears when suggested_next_stage differs from current stage", () => {
    const trip: Trip = {
      id: "TRIP-ADV-1",
      destination: "Singapore",
      type: "Family",
      state: "green",
      age: "1h",
      stage: "discovery",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessWithAdvance,
      } as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    expect(screen.getByTestId("stage-advance-btn")).toBeInTheDocument();
    expect(screen.getByText(/Advance to Shortlist/i)).toBeInTheDocument();
  });

  it("does not render when suggested stage equals current stage", () => {
    const trip: Trip = {
      id: "TRIP-ADV-2",
      destination: "Singapore",
      type: "Family",
      state: "green",
      age: "1h",
      stage: "shortlist",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: {
          ...readinessWithAdvance,
          suggested_next_stage: "shortlist",
        },
      } as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    expect(screen.queryByTestId("stage-advance-btn")).not.toBeInTheDocument();
  });

  it("calls PATCH endpoint when clicked", async () => {
    const { transitionTripStage } = await import("@/lib/api-client");
    (transitionTripStage as any).mockResolvedValue({
      trip_id: "TRIP-ADV-3",
      old_stage: "discovery",
      new_stage: "shortlist",
      changed: true,
    });

    // Mock window.location.reload
    const reloadMock = vi.fn();
    Object.defineProperty(window, "location", {
      value: { reload: reloadMock },
      writable: true,
    });

    const trip: Trip = {
      id: "TRIP-ADV-3",
      destination: "Singapore",
      type: "Family",
      state: "green",
      age: "1h",
      stage: "discovery",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessWithAdvance,
      } as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    const btn = screen.getByTestId("stage-advance-btn");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(transitionTripStage).toHaveBeenCalledWith(
        "TRIP-ADV-3",
        "shortlist",
        "Advanced from discovery to shortlist",
        "discovery",
      );
    });
  });

  it("reloads page after successful transition", async () => {
    const { transitionTripStage } = await import("@/lib/api-client");
    (transitionTripStage as any).mockResolvedValue({
      trip_id: "TRIP-ADV-4",
      old_stage: "discovery",
      new_stage: "shortlist",
      changed: true,
    });

    const reloadMock = vi.fn();
    Object.defineProperty(window, "location", {
      value: { reload: reloadMock },
      writable: true,
    });

    const trip: Trip = {
      id: "TRIP-ADV-4",
      destination: "Singapore",
      type: "Family",
      state: "green",
      age: "1h",
      stage: "discovery",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessWithAdvance,
      } as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    fireEvent.click(screen.getByTestId("stage-advance-btn"));

    await waitFor(() => {
      expect(reloadMock).toHaveBeenCalled();
    });
  });

  it("does not render when no readiness data", () => {
    const trip: Trip = {
      id: "TRIP-ADV-5",
      destination: "Singapore",
      type: "Family",
      state: "green",
      age: "1h",
      stage: "discovery",
      decision: baseDecision as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    expect(screen.queryByTestId("stage-advance-btn")).not.toBeInTheDocument();
  });

  it("never auto-advances - button requires explicit click", async () => {
    const { transitionTripStage } = await import("@/lib/api-client");

    const trip: Trip = {
      id: "TRIP-ADV-6",
      destination: "Singapore",
      type: "Family",
      state: "green",
      age: "1h",
      stage: "discovery",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: {
          ...readinessWithAdvance,
          should_auto_advance_stage: false,
        },
      } as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    // Button exists but no API call has been made
    expect(screen.getByTestId("stage-advance-btn")).toBeInTheDocument();
    expect(transitionTripStage).not.toHaveBeenCalled();
  });
});
