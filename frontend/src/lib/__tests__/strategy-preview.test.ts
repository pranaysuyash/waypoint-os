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

  it("falls back to a derived preview when a persisted escalation strategy conflicts with a quote-ready trip", () => {
    const trip = makeTrip({
      validation: {
        readiness: {
          highest_ready_tier: "quote_ready",
        },
      } as never,
      strategy: {
        session_goal: "Escalate to senior review due to critical contradictions.",
        priority_sequence: ["Document contradictions and evidence"],
        tonal_guardrails: ["Focus questions on gaps"],
        risk_flags: ["Critical review"],
        suggested_opening: "I need to escalate this to a senior agent to review some inconsistencies.",
        exit_criteria: ["Escalation brief prepared"],
        next_action: "STOP_NEEDS_REVIEW",
        assumptions: [],
        suggested_tone: "professional",
      },
    });

    const preview = buildTripStrategyPreview(trip);

    expect(preview).not.toEqual(trip.strategy);
    expect(preview?.session_goal).toContain("Bali");
    expect(preview?.suggested_opening).toContain("options plan");
  });

  it("falls back to a derived preview when a persisted internal draft conflicts with a quote-ready trip", () => {
    const trip = makeTrip({
      destination: "Singapore",
      origin: "Mumbai",
      tripPurpose: "business",
      budget: "USD 42,000",
      party: 18,
      validation: {
        readiness: {
          highest_ready_tier: "quote_ready",
        },
      } as never,
      strategy: {
        session_goal: "Generate internal business-travel draft for Singapore with documented assumptions for agent review.",
        priority_sequence: ["Preserve the corporate/group shape"],
        tonal_guardrails: ["Focus questions on gaps"],
        risk_flags: ["Visa requirement unknown"],
        suggested_opening: "(Internal draft) Generating preliminary business-travel options for Singapore.",
        exit_criteria: ["Internal draft completed"],
        next_action: "PROCEED_INTERNAL_DRAFT",
        assumptions: ["Assuming procurement notes stay visible"],
        suggested_tone: "professional",
      },
    });

    const preview = buildTripStrategyPreview(trip);

    expect(preview).not.toEqual(trip.strategy);
    expect(preview?.session_goal).toContain("business trip");
    expect(preview?.suggested_opening).toContain("options plan for Singapore");
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

  it("uses corporate language when the trip purpose is business", () => {
    const preview = buildTripStrategyPreview(makeTrip({
      destination: "Singapore",
      origin: "Mumbai",
      tripPurpose: "business",
      party: 18,
      budget: "USD 42,000",
    }));

    expect(preview).not.toBeNull();
    expect(preview?.session_goal).toContain("business trip");
    expect(preview?.session_goal).toContain("$42,000");
    expect(preview?.priority_sequence.join(" ")).toContain("corporate/group shape");
    expect(preview?.suggested_opening).toContain("business requirements");
    expect(preview?.priority_sequence.join(" ")).not.toContain("Trip priorities / must-haves");
    expect(preview?.assumptions.join(" ")).not.toContain("Trip priorities / must-haves");
  });
});
