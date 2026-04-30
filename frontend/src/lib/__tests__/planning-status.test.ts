import { describe, expect, it } from "vitest";
import type { Trip } from "@/lib/api-client";
import {
  canAccessPlanningStage,
  getPlanningBriefStatus,
  getPlanningPrimaryActionLabel,
  getPlanningStageGateReason,
  getRecommendedPlanningFields,
  getRequiredPlanningFields,
} from "../planning-status";

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: "trip_4b9e0d894872",
    destination: "Singapore",
    type: "family leisure",
    state: "amber",
    age: "Today",
    createdAt: "2026-04-29T20:02:40.764703+00:00",
    updatedAt: "2026-04-30T12:23:15.851953+00:00",
    party: 5,
    dateWindow: "dates around 9th to 14th feb",
    origin: "TBD",
    budget: "$0",
    status: "assigned",
    decision: {
      decision_state: "ASK_FOLLOWUP",
      hard_blockers: [],
      soft_blockers: ["incomplete_intake"],
      contradictions: [],
      risk_flags: [],
      follow_up_questions: [],
      branch_options: [],
      rationale: {} as any,
      confidence: {} as any,
      commercial_decision: "NONE",
      budget_breakdown: null,
    },
    validation: {
      is_valid: true,
      errors: [],
      warnings: [
        {
          severity: "warning",
          code: "QUOTE_READY_INCOMPLETE",
          message: "Field 'origin_city' missing",
          field: "origin_city",
        },
        {
          severity: "warning",
          code: "QUOTE_READY_INCOMPLETE",
          message: "Field 'budget_raw_text' missing",
          field: "budget_raw_text",
        },
      ],
    },
    rawInput: { fixture_id: "SC-901" },
    ...overrides,
  } as Trip;
}

describe("planning-status", () => {
  it("classifies blocked trips with required and recommended fields", () => {
    const trip = makeTrip();

    expect(getPlanningBriefStatus(trip)).toBe("missing_required_details");
    expect(getRequiredPlanningFields(trip)).toEqual(["Budget range", "Origin city"]);
    expect(getRecommendedPlanningFields(trip)).toEqual(["Trip priorities / must-haves", "Date flexibility"]);
  });

  it("allows only intake, trip details, and timeline when required fields are missing", () => {
    const trip = makeTrip();

    expect(canAccessPlanningStage(trip, "intake")).toBe(true);
    expect(canAccessPlanningStage(trip, "packet")).toBe(true);
    expect(canAccessPlanningStage(trip, "timeline")).toBe(true);
    expect(canAccessPlanningStage(trip, "decision")).toBe(false);
    expect(canAccessPlanningStage(trip, "strategy")).toBe(false);
    expect(canAccessPlanningStage(trip, "output")).toBe(false);
    expect(canAccessPlanningStage(trip, "safety")).toBe(false);
    expect(getPlanningStageGateReason(trip, "strategy")).toBe("Confirm budget range and origin city first.");
  });

  it("keeps draft follow-up as the primary action while required fields are missing", () => {
    expect(getPlanningPrimaryActionLabel(makeTrip())).toBe("Draft follow-up");
  });

  it("unlocks options once required fields are complete but recommended details remain", () => {
    const trip = makeTrip({
      origin: "Mumbai",
      budget: "$5000",
      validation: {
        is_valid: true,
        errors: [],
        warnings: [],
      } as any,
      decision: {
        decision_state: "ASK_FOLLOWUP",
        hard_blockers: [],
        soft_blockers: [],
        contradictions: [],
        risk_flags: [],
        follow_up_questions: [],
        branch_options: [],
        rationale: {} as any,
        confidence: {} as any,
        commercial_decision: "NONE",
        budget_breakdown: null,
      } as any,
    });

    expect(getPlanningBriefStatus(trip)).toBe("missing_recommended_details");
    expect(canAccessPlanningStage(trip, "strategy")).toBe(true);
    expect(getPlanningPrimaryActionLabel(trip)).toBe("Continue to options");
  });
});
