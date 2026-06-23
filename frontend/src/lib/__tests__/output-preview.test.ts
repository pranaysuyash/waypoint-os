import { describe, expect, it } from "vitest";
import type { Trip } from "@/lib/api-client";
import { buildTripOutputPreview } from "../output-preview";

describe("buildTripOutputPreview", () => {
  it("replaces generic internal-draft wording with a customer-safe derived opening", () => {
    const trip = {
      id: "trip_test",
      destination: "Zanzibar",
      strategy: {
        session_goal: "Prepare a clear options plan for Zanzibar while keeping budget aligned.",
        priority_sequence: [],
        tonal_guardrails: [],
        risk_flags: [],
        suggested_opening: "(Internal draft) Generating preliminary options for agent review.",
        exit_criteria: [],
        next_action: "PROCEED_INTERNAL_DRAFT",
        assumptions: [],
        suggested_tone: "professional",
      },
      decision: {
        decision_state: "ASK_FOLLOWUP",
        follow_up_questions: [],
      },
    } as unknown as Trip;

    const preview = buildTripOutputPreview(trip);

    expect(preview.isDerived).toBe(true);
    expect(preview.travelerBundle?.user_message).toContain("I just need to confirm a couple of details");
    expect(preview.travelerBundle?.user_message).not.toContain("Internal draft");
    expect(preview.internalBundle?.user_message).toContain("I just need to confirm a couple of details");
  });
});
