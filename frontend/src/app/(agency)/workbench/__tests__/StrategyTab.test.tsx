import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import type { Trip } from "@/lib/api-client";
import StrategyTab from "../StrategyTab";

const mockUseWorkbenchStore = vi.hoisted(() => vi.fn());

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: () => mockUseWorkbenchStore(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/workbench/workbench.module.css", () => ({
  default: {
    emptyState: "emptyState",
    section: "section",
    sectionTitle: "sectionTitle",
    card: "card",
    list: "list",
    listItem: "listItem",
    listIcon: "listIcon",
    iconInfo: "iconInfo",
    iconWarning: "iconWarning",
    jsonToggle: "jsonToggle",
    jsonOutput: "jsonOutput",
  },
}));

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: "trip_test",
    destination: "Singapore",
    type: "business",
    state: "blue",
    age: "Today",
    createdAt: "2026-06-23T00:00:00Z",
    updatedAt: "2026-06-23T00:00:00Z",
    party: 18,
    dateWindow: "in Oct 2026",
    origin: "Mumbai",
    budget: "USD 42,000",
    tripPurpose: "business",
    status: "new",
    rawInput: { fixture_id: "trip_test_fixture" },
    decision: null,
    validation: null,
    strategy: {
      session_goal: "Generate internal trip draft with documented assumptions for agent review.",
      priority_sequence: ["Generate internal draft with documented assumptions"],
      tonal_guardrails: ["Focus questions on gaps"],
      risk_flags: [],
      suggested_opening: "(Internal draft) Generating preliminary options for agent review.",
      exit_criteria: ["Draft ready"],
      next_action: "PROCEED_INTERNAL_DRAFT",
      assumptions: ["Assuming soft_preferences can be inferred or is acceptable as-is"],
      suggested_tone: "professional",
    },
    ...overrides,
  };
}

describe("StrategyTab", () => {
  it("prefers the live business-oriented preview when the stored strategy is generic boilerplate", () => {
    mockUseWorkbenchStore.mockReturnValue({
      result_strategy: null,
      result_internal_bundle: null,
      result_traveler_bundle: null,
      debug_raw_json: false,
      setDebugRawJson: vi.fn(),
    });

    render(<StrategyTab trip={makeTrip()} />);

    expect(screen.getByText(/business trip/i)).toBeInTheDocument();
    expect(screen.getByText(/corporate\/group shape/i)).toBeInTheDocument();
    expect(screen.getByText(/business requirements/i)).toBeInTheDocument();
    expect(screen.getAllByText(/\$42,000/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/priorities or must-haves/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/Trip priorities \/ must-haves/i)).toHaveLength(0);
  });
});
