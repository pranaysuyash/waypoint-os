import { describe, expect, it } from "vitest";
import {
  isInboxTrip,
  isWorkspaceTrip,
  transformSpineTripToInboxTrip,
  transformSpineTripsResponseToInboxTrips,
  transformSpineTripToTrip,
  transformSpineTripsResponseToTrips,
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
    expect(isWorkspaceTrip(trips[0])).toBe(true);
  });

  it("excludes completed and cancelled lifecycle records from the workspace queue", () => {
    const completedTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "completed" },
      now
    );
    const cancelledTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "cancelled" },
      now
    );

    expect(isWorkspaceTrip(completedTrip)).toBe(false);
    expect(isWorkspaceTrip(cancelledTrip)).toBe(false);
  });

  it("keeps only lead lifecycle records in the inbox queue", () => {
    const incompleteTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "incomplete", assigned_to: null, assigned_to_name: null },
      now
    );
    const newTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "new", assigned_to: null, assigned_to_name: null },
      now
    );
    const assignedTrip = transformSpineTripToTrip(spineTrip, now);
    const inProgressTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "in_progress" },
      now
    );
    const completedTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "completed" },
      now
    );
    const cancelledTrip = transformSpineTripToTrip(
      { ...spineTrip, status: "cancelled" },
      now
    );

    expect(isInboxTrip(newTrip)).toBe(true);
    expect(isInboxTrip(incompleteTrip)).toBe(true);
    expect(isInboxTrip(assignedTrip)).toBe(false);
    expect(isInboxTrip(inProgressTrip)).toBe(false);
    expect(isInboxTrip(completedTrip)).toBe(false);
    expect(isInboxTrip(cancelledTrip)).toBe(false);
  });

  it("maps a backend trip to the inbox presentation shape", () => {
    const inboxTrip = transformSpineTripToInboxTrip(spineTrip, now);

    expect(inboxTrip).toMatchObject({
      id: "trip-123456",
      reference: "1234",
      destination: "Kyoto",
      tripType: "culture",
      partySize: 4,
      dateWindow: "May 1-8",
      value: 125000,
      priority: "high",
      priorityScore: 75,
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
        "incomplete",
        "details_unclear",
        "needs_clarification",
      ])
    );
  });

  it("reserves critical priority for true urgency, not ordinary incomplete leads", () => {
    const urgentTrip = transformSpineTripToInboxTrip(
      {
        ...spineTrip,
        analytics: {
          ...spineTrip.analytics,
          escalation_severity: "critical",
        },
      },
      now
    );

    expect(urgentTrip.priority).toBe("critical");
    expect(urgentTrip.priorityScore).toBe(90);
  });

  it("filters planning trips out of inbox responses after start planning", () => {
    const inboxTrips = transformSpineTripsResponseToInboxTrips(
      {
        items: [
          { ...spineTrip, id: "trip-new", status: "incomplete", assigned_to: null, assigned_to_name: null },
          { ...spineTrip, id: "trip-planning", status: "assigned" },
          { ...spineTrip, id: "trip-done", status: "completed" },
        ],
      },
      now
    );

    expect(inboxTrips).toHaveLength(1);
    expect(inboxTrips[0]).toMatchObject({
      id: "trip-new",
      reference: "NEW",
    });
  });
});
