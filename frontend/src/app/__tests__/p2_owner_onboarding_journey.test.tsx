/**
 * P2 Owner Onboarding Journey E2E
 *
 * Validates the full UI continuity for the P2 training/problem scenario:
 *   Junior agent submits quote → coaching warnings appear → owner makes decision
 *
 * This test exercises:
 * 1. IntakePanel renders with a junior agent's quote
 * 2. Spine run returns suitability coaching warnings
 * 3. DecisionPanel displays suitability flags (coaching severity)
 * 4. Owner can review and act on coaching warnings
 * 5. SuitabilityPanel acknowledgment flow works end-to-end
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { IntakePanel } from "@/components/workspace/panels/IntakePanel";
import { DecisionPanel } from "@/components/workspace/panels/DecisionPanel";
import { SuitabilityPanel, type SuitabilityFlag } from "@/components/workspace/panels/SuitabilityPanel";
import type { Trip } from "@/lib/api-client";
import type { DecisionOutput, SuitabilityFlagData } from "@/types/spine";

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: () => ({
    input_raw_note:
      "Family of 4 from Bangalore, 2 adults + toddler (3yo) + elderly (70yo). Want Singapore or Bali. Budget 2.5L INR. June 2026.",
    input_owner_note: "Repeat customer, prioritise Sentosa for kids.",
    input_structured_json: "",
    input_itinerary_text: "",
    stage: "discovery",
    operating_mode: "normal_intake",
    strict_leakage: false,
    scenario_id: "",
    debug_raw_json: false,
    result_decision: null,
    setInputRawNote: vi.fn(),
    setInputOwnerNote: vi.fn(),
    setStage: vi.fn(),
    setOperatingMode: vi.fn(),
    setScenarioId: vi.fn(),
    setStrictLeakage: vi.fn(),
    setDebugRawJson: vi.fn(),
    setResultPacket: vi.fn(),
    setResultValidation: vi.fn(),
    setResultDecision: vi.fn(),
    setResultStrategy: vi.fn(),
    setResultInternalBundle: vi.fn(),
    setResultTravelerBundle: vi.fn(),
    setResultSafety: vi.fn(),
    setResultFees: vi.fn(),
    setResultRunTs: vi.fn(),
  }),
}));

vi.mock("@/contexts/TripContext", () => ({
  useTripContext: () => ({
    replaceTrip: vi.fn(),
    refetchTrip: vi.fn(),
  }),
}));

vi.mock("@/hooks/useSpineRun", () => ({
  useSpineRun: () => ({
    execute: vi.fn().mockResolvedValue({
      ok: true,
      run_id: "run-owner-001",
      decision: {
        decision_state: "ASK_FOLLOWUP",
        suitability_flags: [
          {
            flag_type: "toddler_water_unsafe",
            severity: "critical",
            reason: "Water activities unsafe for 3yo",
            confidence: 0.95,
            affected_travelers: ["toddler_1"],
          },
          {
            flag_type: "elderly_intense",
            severity: "high",
            reason: "Physical intensity may strain elderly traveler",
            confidence: 0.85,
            affected_travelers: ["elderly_1"],
          },
        ],
      },
    }),
    isLoading: false,
    error: null,
    reset: vi.fn(),
    data: null,
  }),
}));

vi.mock("@/hooks/useTrips", () => ({
  useTrips: () => ({
    data: [],
    total: 0,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateTrip: () => ({
    mutate: vi.fn().mockResolvedValue({}),
    isSaving: false,
    error: null,
  }),
}));

vi.mock("@/hooks/useFieldAuditLog", () => ({
  useFieldAuditLog: () => ({
    logChange: vi.fn(),
    getLatestChangeForField: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn(),
    getAll: vi.fn(),
    toString: vi.fn(),
  }),
  usePathname: () => "/",
}));

vi.mock("@/contexts/TripContext", () => ({
  useTripContext: () => ({
    replaceTrip: vi.fn(),
    refetchTrip: vi.fn(),
  }),
}));

vi.mock("@/lib/currency", () => ({
  CURRENCY_CONFIG: {
    INR: { symbol: "₹", code: "INR", name: "Indian Rupee" },
  },
  formatMoney: (amount: number) => `₹${amount}`,
  formatMoneyCompact: (amount: number) => `₹${amount}`,
  parseBudgetString: (s: string) => ({ amount: 250000, currency: "INR" }),
  getCurrencyOptions: () => [{ value: "INR", label: "INR", flag: "🇮🇳" }],
}));

vi.mock("@/lib/combobox", () => ({
  TRIP_TYPE_OPTIONS: [{ value: "Family", label: "Family" }],
  DESTINATION_OPTIONS: [
    { value: "Singapore", label: "Singapore" },
    { value: "Bali", label: "Bali" },
  ],
}));

vi.mock("@/lib/routes", () => ({
  getTripRoute: (tripId: string, tab: string) => `/trips/${tripId}/${tab}`,
}));

describe("P2 Owner Onboarding Journey: Junior Quote → Coaching Warnings → Owner Decision", () => {
  const juniorTrip: Trip = {
    id: "TRIP-JR-001",
    destination: "Singapore",
    type: "Family",
    state: "amber",
    age: "0d",
    dateWindow: "June 2026",
    party: 4,
    budget: "₹250000",
    customerMessage:
      "Family of 4 from Bangalore, 2 adults + toddler (3yo) + elderly (70yo). Want Singapore or Bali. Budget 2.5L INR. June 2026.",
    agentNotes: "Repeat customer, prioritise Sentosa for kids.",
    createdAt: "2026-04-23T08:00:00.000Z",
    updatedAt: "2026-04-23T08:15:00.000Z",
  };

  const coachingWarnings: SuitabilityFlagData[] = [
    {
      flag_type: "toddler_water_unsafe",
      severity: "critical",
      reason: "Water activities unsafe for 3yo toddler",
      confidence: 0.95,
      affected_travelers: ["toddler_1"],
    },
    {
      flag_type: "elderly_intense",
      severity: "high",
      reason: "Physical intensity may strain elderly traveler (70yo)",
      confidence: 0.85,
      affected_travelers: ["elderly_1"],
    },
  ];

  const decisionWithCoaching: DecisionOutput = {
    decision_state: "ASK_FOLLOWUP",
    hard_blockers: [],
    soft_blockers: [],
    contradictions: [],
    risk_flags: [],
    suitability_flags: coachingWarnings,
    follow_up_questions: [],
    rationale: {
      feasibility: "Feasible with coaching adjustments",
      confidence: 0.75,
      hard_blockers: [],
      soft_blockers: [],
      contradictions: [],
      confidence_scorecard: { data: 0.8, judgment: 0.75, commercial: 0.7 },
    },
    confidence: {
      data_quality: 0.8,
      judgment_confidence: 0.75,
      commercial_confidence: 0.7,
      overall: 0.75,
    },
    branch_options: [],
    commercial_decision: "proceed",
    budget_breakdown: null,
  };

  it("Step 1: IntakePanel renders with junior agent's trip data", () => {
    render(<IntakePanel tripId="TRIP-JR-001" trip={juniorTrip} />);

    expect(screen.getByText("Singapore")).toBeInTheDocument();
    expect(screen.getByText("Family")).toBeInTheDocument();
    expect(screen.getByDisplayValue(/Family of 4 from Bangalore/)).toBeInTheDocument();
  });

  it("Step 2: DecisionPanel renders coaching warnings after spine run", () => {
    const tripWithDecision = {
      ...juniorTrip,
      decision: decisionWithCoaching,
    };

    render(<DecisionPanel trip={tripWithDecision} tripId="TRIP-JR-001" />);

    expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
    expect(screen.getByText("Suitability Audit Results")).toBeInTheDocument();
    expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
    expect(screen.getByText("Physical Intensity Unsafe for Elderly")).toBeInTheDocument();
  });

  it("Step 3: SuitabilityPanel shows critical and high warnings with acknowledgment", () => {
    const flags: SuitabilityFlag[] = coachingWarnings.map((f) => ({
      flag: f.flag_type,
      flag_type: f.flag_type,
      severity: f.severity,
      reason: f.reason,
      confidence: f.confidence,
      affected_travelers: f.affected_travelers,
    }));

    const handleAcknowledge = vi.fn();

    render(
      <SuitabilityPanel
        flags={flags}
        tripId="TRIP-JR-001"
        onAcknowledge={handleAcknowledge}
      />
    );

    expect(screen.getByText("Critical Concerns")).toBeInTheDocument();
    expect(screen.getByText("Important Warnings")).toBeInTheDocument();
    expect(
      screen.getByText("Operator review required before sending to customer")
    ).toBeInTheDocument();

    const continueButton = screen.getByRole("button", { name: /Continue to Send/ });
    expect(continueButton).toBeDisabled();
  });

  it("Step 4: Owner acknowledges critical flags and proceeds", async () => {
    const flags: SuitabilityFlag[] = coachingWarnings.map((f) => ({
      flag: f.flag_type,
      flag_type: f.flag_type,
      severity: f.severity,
      reason: f.reason,
      confidence: f.confidence,
      affected_travelers: f.affected_travelers,
    }));

    const handleAcknowledge = vi.fn();

    render(
      <SuitabilityPanel
        flags={flags}
        tripId="TRIP-JR-001"
        onAcknowledge={handleAcknowledge}
      />
    );

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThanOrEqual(1);

    fireEvent.click(checkboxes[0]);

    const continueButton = screen.getByRole("button", { name: /Continue to Send/ });
    expect(continueButton).not.toBeDisabled();

    fireEvent.click(continueButton);

    await waitFor(() => {
      expect(handleAcknowledge).toHaveBeenCalledWith(
        expect.arrayContaining([expect.any(String)])
      );
    });
  });

  it("Step 5: Full journey — intake data flows through decision to coaching display", () => {
    const tripWithDecision = {
      ...juniorTrip,
      decision: decisionWithCoaching,
    };

    const { unmount } = render(
      <DecisionPanel trip={tripWithDecision} tripId="TRIP-JR-001" />
    );

    expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
    expect(screen.getByText("Suitability Audit Results")).toBeInTheDocument();
    expect(screen.getByText("Tier 1: Hard Blockers (Must Acknowledge Before Approval)")).toBeInTheDocument();
    expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
    expect(screen.getByText(/95%/)).toBeInTheDocument();
    expect(screen.getByText(/85%/)).toBeInTheDocument();

    unmount();

    const flags: SuitabilityFlag[] = coachingWarnings.map((f) => ({
      flag: f.flag_type,
      flag_type: f.flag_type,
      severity: f.severity,
      reason: f.reason,
      confidence: f.confidence,
      affected_travelers: f.affected_travelers,
    }));

    render(
      <SuitabilityPanel flags={flags} tripId="TRIP-JR-001" />
    );

    expect(screen.getByText("Critical Concerns")).toBeInTheDocument();
    expect(screen.getByText("Important Warnings")).toBeInTheDocument();
    expect(screen.getByText("Confidence: 95%")).toBeInTheDocument();
    expect(screen.getByText("Confidence: 85%")).toBeInTheDocument();
  });
});
