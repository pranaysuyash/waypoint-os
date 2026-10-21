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
  decision_state: "BRANCH_OPTIONS",
  hard_blockers: [],
  soft_blockers: [],
  contradictions: [],
  risk_flags: [],
  follow_up_questions: [],
  rationale: { feasibility: "Budget allows the trip." },
  confidence: { overall: 0.7 },
  branch_options: [],
  commercial_decision: "NONE",
  budget_breakdown: null,
};

function renderWithDecision(branchOptions: unknown) {
  const decision = { ...baseDecision, branch_options: branchOptions } as any;
  (useWorkbenchStore as any).mockReturnValue({
    result_decision: decision,
    result_validation: null,
    debug_raw_json: false,
    setDebugRawJson: vi.fn(),
    acknowledged_suitability_flags: [],
    acknowledgeFlag: vi.fn(),
  });
  return render(<DecisionPanel />);
}

describe("DecisionPanel branch options", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders both payload shapes: plain string entries and scored route structures", () => {
    renderWithDecision([
      "Budget-tier options",
      {
        label: "Option A",
        description: "Direct route, longer first stay",
        route_structure: {
          cities: ["Goa", "Jaipur"],
          nights: [3, 2],
          open_jaw_aligned: false,
          score: 11,
          label: "Option A",
        },
      },
    ]);

    expect(screen.getByTestId("branch-options")).toBeInTheDocument();
    expect(screen.getByText("Budget-tier options")).toBeInTheDocument();
    expect(screen.getByText("Option A")).toBeInTheDocument();
    expect(screen.getByText("Direct route, longer first stay")).toBeInTheDocument();
    expect(screen.getByText(/route score 11/)).toBeInTheDocument();
  });

  it("renders nothing when branch_options is empty", () => {
    renderWithDecision([]);

    expect(screen.queryByTestId("branch-options")).not.toBeInTheDocument();
  });

  it("renders branch options coming from a persisted trip decision", () => {
    const trip: Trip = {
      id: "TRIP-123",
      destination: "Bali",
      type: "Family",
      state: "amber",
      age: "5h",
      decision: {
        ...baseDecision,
        branch_options: [
          {
            label: "Option B",
            description: "Open-jaw arrival",
            route_structure: {
              cities: ["Bali"],
              nights: [5],
              open_jaw_aligned: true,
              score: 13,
              label: "Option B",
            },
          },
        ],
      } as any,
    } as any;

    (useWorkbenchStore as any).mockReturnValue({
      result_decision: null,
      result_validation: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
      acknowledged_suitability_flags: [],
      acknowledgeFlag: vi.fn(),
    });

    render(<DecisionPanel trip={trip} />);

    expect(screen.getByTestId("branch-options")).toBeInTheDocument();
    expect(screen.getByText("Option B")).toBeInTheDocument();
    expect(screen.getByText(/route score 13/)).toBeInTheDocument();
  });
});
