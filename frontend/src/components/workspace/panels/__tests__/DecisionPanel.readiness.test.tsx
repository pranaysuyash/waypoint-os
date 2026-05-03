import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
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

const readinessPayload = {
  highest_ready_tier: "quote_ready",
  suggested_next_stage: "shortlist",
  should_auto_advance_stage: false,
  missing_for_next: ["trip_priorities", "date_flexibility"],
};

describe("DecisionPanel readiness banner", () => {
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

  it("renders readiness from result_validation store", () => {
    (useWorkbenchStore as any).mockReturnValue({
      result_decision: baseDecision,
      result_validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessPayload,
      },
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      acknowledged_suitability_flags: [],
      acknowledgeFlag: vi.fn(),
    });

    render(<DecisionPanel />);

    expect(screen.getByText("Readiness")).toBeInTheDocument();
    expect(screen.getByText("Quote Ready")).toBeInTheDocument();
    expect(screen.getByText(/2 fields needed for Shortlist/i)).toBeInTheDocument();
  });

  it("renders readiness from trip.validation after refresh", () => {
    const trip: Trip = {
      id: "TRIP-123",
      destination: "Bali",
      type: "Family",
      state: "amber",
      age: "5h",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessPayload,
      } as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    expect(screen.getByText("Readiness")).toBeInTheDocument();
    expect(screen.getByText("Quote Ready")).toBeInTheDocument();
  });

  it("prefers result_validation over trip.validation", () => {
    const trip: Trip = {
      id: "TRIP-123",
      destination: "Bali",
      type: "Family",
      state: "amber",
      age: "5h",
      decision: baseDecision as any,
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: {
          highest_ready_tier: "intake_minimum",
          suggested_next_stage: "discovery",
          missing_for_next: [],
        },
      } as any,
    } as any;

    (useWorkbenchStore as any).mockReturnValue({
      result_decision: baseDecision,
      result_validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessPayload,
      },
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      acknowledged_suitability_flags: [],
      acknowledgeFlag: vi.fn(),
    });

    render(<DecisionPanel trip={trip} />);

    // Store readiness (quote_ready) should win over trip readiness (intake_minimum)
    expect(screen.getByText("Quote Ready")).toBeInTheDocument();
    expect(screen.queryByText("Intake")).not.toBeInTheDocument();
  });

  it("hides banner when no readiness data", () => {
    (useWorkbenchStore as any).mockReturnValue({
      result_decision: baseDecision,
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      acknowledged_suitability_flags: [],
      acknowledgeFlag: vi.fn(),
    });

    const trip: Trip = {
      id: "TRIP-123",
      destination: "Bali",
      type: "Family",
      state: "amber",
      age: "5h",
      decision: baseDecision as any,
    } as any;

    render(<DecisionPanel trip={trip} />);

    expect(screen.queryByText("Readiness")).not.toBeInTheDocument();
  });

  it("shows no stage-advance button", () => {
    (useWorkbenchStore as any).mockReturnValue({
      result_decision: baseDecision,
      result_validation: {
        is_valid: true,
        errors: [],
        warnings: [],
        readiness: readinessPayload,
      },
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      acknowledged_suitability_flags: [],
      acknowledgeFlag: vi.fn(),
    });

    render(<DecisionPanel />);

    expect(screen.queryByRole("button", { name: /advance/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /move to/i })).not.toBeInTheDocument();
  });
});
