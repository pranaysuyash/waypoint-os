import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DecisionPage from "../decision/page";
import StrategyPage from "../strategy/page";
import OutputPage from "../output/page";
import SafetyPage from "../safety/page";

vi.mock("@/contexts/TripContext", () => ({
  useTripContext: vi.fn(),
}));

vi.mock("@/components/workspace/panels/DecisionPanel", () => ({
  DecisionPanel: () => <div>Decision panel</div>,
}));

vi.mock("@/components/workspace/panels/StrategyPanel", () => ({
  StrategyPanel: () => <div>Strategy panel</div>,
}));

vi.mock("@/components/workspace/panels/OutputPanel", () => ({
  default: () => <div>Output panel</div>,
}));

vi.mock("@/components/workspace/panels/SafetyPanel", () => ({
  SafetyPanel: () => <div>Safety panel</div>,
}));

const { useTripContext } = await import("@/contexts/TripContext");

const blockedTrip = {
  id: "trip_4b9e0d894872",
  destination: "Singapore",
  type: "family leisure",
  status: "assigned",
  state: "amber",
  party: 5,
  dateWindow: "dates around 9th to 14th feb",
  origin: "TBD",
  budget: "$0",
  decision: {
    decision_state: "ASK_FOLLOWUP",
    hard_blockers: [],
    soft_blockers: ["incomplete_intake"],
  },
  validation: {
    warnings: [
      { field: "origin_city" },
      { field: "budget_raw_text" },
    ],
  },
} as any;

describe("gated planning stage pages", () => {
  it.each([
    ["Quote Assessment", DecisionPage],
    ["Options", StrategyPage],
    ["Output", OutputPage],
    ["Risk Review", SafetyPage],
  ])("renders a gate state on %s when required planning fields are missing", (label, PageComponent) => {
    vi.mocked(useTripContext).mockReturnValue({
      tripId: "trip_4b9e0d894872",
      trip: blockedTrip,
      isLoading: false,
      error: null,
      refetchTrip: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(<PageComponent />);

    expect(screen.getByText("Before building options")).toBeInTheDocument();
    expect(screen.getByText("Confirm budget range and origin city first.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to missing details" })).toHaveAttribute(
      "href",
      "/trips/trip_4b9e0d894872/intake",
    );
    expect(screen.queryByText(`${label} panel`)).not.toBeInTheDocument();
  });
});
