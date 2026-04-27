import { describe, expect, it } from "vitest";
import {
  transformSpineTripToInboxTrip,
  transformSpineTripToTrip,
  transformSpineTripsResponseToTrips,
  WORKSPACE_STATES,
} from "../bff-trip-adapters";

const now = new Date("2026-04-27T12:00:00.000Z");

const spineTrip = {
  id: "trip-123456",
  status: "assigned",
  created_at: "2026-04-25T12:00:00.000Z",
  updated_at: "2026-04-26T12:00:00.000Z",
  assigned_to: "agent-1",
  assigned_to_name: "Asha",
  extracted: {
    facts: {
      destination_candidates: { value: ["Kyoto"] },
      primary_intent: { value: ["culture"] },
      party_profile: { value: 4 },
      budget: { value: 125000 },
      date_window: { value: "May 1-8" },
      origin_city: { value: "Delhi" },
    },
    events: [{ timestamp: "2026-04-20T12:00:00.000Z" }],
  },
  analytics: {
    margin_pct: 35,
    quality_score: 82,
    quality_breakdown: {
      completeness: 80,
      feasibility: 70,
      risk: 60,
      profitability: 90,
    },
    requires_review: true,
    review_status: "pending",
    review_metadata: {
      reviewed_by: "owner",
      reviewed_at: "2026-04-26T13:00:00.000Z",
      notes: "Check supplier pricing",
    },
  },
  validation: {
    is_valid: false,
    errors: [],
    warnings: [],
  },
  decision: {
    action: "REVIEW",
    decision_state: "ASK_FOLLOWUP",
    confidence_score: 0.25,
    hard_blockers: ["missing_passport"],
    risk_flags: ["visa_gap"],
    budget_breakdown: null,
  },
  raw_input: {
    fixture_id: "FIX-001",
  },
};

describe("BFF trip adapters", () => {
  it("maps a backend trip to the frontend Trip shape using the richest extraction paths", () => {
    const trip = transformSpineTripToTrip(spineTrip, now);

    expect(trip).toMatchObject({
      id: "trip-123456",
      destination: "Kyoto",
      type: "culture",
      state: "amber",
      age: "2d",
      createdAt: "2026-04-25T12:00:00.000Z",
      updatedAt: "2026-04-26T12:00:00.000Z",
      party: 4,
      dateWindow: "May 1-8",
      origin: "Delhi",
      budget: "$125,000",
      status: "assigned",
      review_status: "pending",
      reviewedBy: "owner",
      reviewedAt: "2026-04-26T13:00:00.000Z",
      reviewNotes: "Check supplier pricing",
      action: "REVIEW",
    });

    expect(trip.analytics?.requiresReview).toBe(true);
    expect(trip.decision?.decision_state).toBe("ASK_FOLLOWUP");
    expect(trip.rawInput).toEqual({ fixture_id: "FIX-001" });
  });

  it("maps backend response envelopes and preserves workspace state semantics", () => {
    const trips = transformSpineTripsResponseToTrips({ items: [spineTrip] }, now);

    expect(trips).toHaveLength(1);
    expect(WORKSPACE_STATES.has(trips[0].state)).toBe(true);
  });

  it("maps a backend trip to the inbox presentation shape", () => {
    const inboxTrip = transformSpineTripToInboxTrip(spineTrip, now);

    expect(inboxTrip).toMatchObject({
      id: "trip-123456",
      reference: "trip-123456",
      destination: "Kyoto",
      tripType: "culture",
      partySize: 4,
      dateWindow: "May 1-8",
      value: 125000,
      priority: "critical",
      priorityScore: 90,
      stage: "options",
      stageNumber: 2,
      assignedTo: "agent-1",
      assignedToName: "Asha",
      submittedAt: "2026-04-25T12:00:00.000Z",
      lastUpdated: "2026-04-26T12:00:00.000Z",
      daysInCurrentStage: 2,
      slaStatus: "on_track",
      customerName: "Customer FIX-001",
    });

    expect(inboxTrip.flags).toEqual(
      expect.arrayContaining([
        "validation_failed",
        "low_confidence",
        "requires_review",
        "high_margin",
        "needs_clarification",
        "missing_information",
        "high_value",
      ])
    );
  });
});
