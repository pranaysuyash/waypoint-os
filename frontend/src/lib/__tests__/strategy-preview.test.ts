import { describe, expect, it } from "vitest";
import type { Trip } from "@/lib/api-client";
import { buildTripStrategyPreview } from "@/lib/strategy-preview";

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: "trip_test",
    destination: "Bali",
    type: "leisure",
    state: "blue",
    age: "Today",
    createdAt: "2026-06-21T00:00:00Z",
    updatedAt: "2026-06-21T00:00:00Z",
    party: 4,
    dateWindow: "August 2026",
    origin: "Mumbai",
    budget: "1200000",
    status: "new",
    rawInput: { fixture_id: "trip_test_fixture" },
    decision: null,
    validation: null,
    tripPriorities: "slow pace, vegetarian food",
    ...overrides,
  };
}

describe("buildTripStrategyPreview", () => {
  it("returns null when trip is missing", () => {
    expect(buildTripStrategyPreview(null)).toBeNull();
  });

  it("prefers a persisted strategy when one exists", () => {
    const trip = makeTrip({
      strategy: {
        session_goal: "Persisted goal",
        priority_sequence: ["Persisted step"],
        tonal_guardrails: ["Persisted guardrail"],
        risk_flags: ["Persisted risk"],
        suggested_opening: "Persisted opening",
        exit_criteria: ["Persisted exit"],
        next_action: "STOP_NEEDS_REVIEW",
        assumptions: ["Persisted assumption"],
        suggested_tone: "professional",
      },
    });

    expect(buildTripStrategyPreview(trip)).toEqual(trip.strategy);
  });

  it("synthesizes a preview from trip context when strategy is absent", () => {
    const preview = buildTripStrategyPreview(makeTrip());

    expect(preview).not.toBeNull();
    expect(preview?.session_goal).toContain("Bali");
    expect(preview?.session_goal).toContain("slow pace, vegetarian food");
    expect(preview?.priority_sequence[0]).toContain("Mumbai");
    expect(preview?.suggested_tone).toBe("professional");
  });

  it("avoids placeholder text in the priority sequence when origin is unknown", () => {
    const preview = buildTripStrategyPreview(makeTrip({ origin: "TBD", budget: "Budget: USD 4,000" }));

    expect(preview).not.toBeNull();
    expect(preview?.priority_sequence[0]).toBe("Check the trip details around Bali");
    expect(preview?.priority_sequence.join(" ")).not.toContain("TBD and Bali together");
  });
});
