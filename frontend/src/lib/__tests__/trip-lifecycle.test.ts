import { describe, expect, it } from "vitest";

import {
  decisionStateLabel,
  deriveTripLifecycle,
  getAllowedActions,
  getNeedsInformation,
  isTripEscalated,
} from "@/lib/trip-lifecycle";
import type { Trip } from "@/lib/api-client";

/**
 * Fixtures mirror the VERIFIED API contract fields on `Trip`
 * (status / stage / decision.decision_state / review_status / agentOperations).
 * No assumed shapes — these are the fields bff-trip-adapters.ts actually maps.
 */
function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: "trip_test",
    destination: "Tokyo",
    type: "leisure",
    state: "blue",
    age: "2h",
    createdAt: "2026-09-01T00:00:00Z",
    updatedAt: "2026-09-01T01:00:00Z",
    ...overrides,
  };
}

describe("deriveTripLifecycle", () => {
  it("maps a fresh trip to intake", () => {
    const derived = deriveTripLifecycle(makeTrip({ status: "new", stage: "discovery" }));
    expect(derived.state).toBe("intake");
    expect(derived.tone).toBe("neutral");
    expect(derived.nextActions.length).toBeGreaterThan(0);
  });

  it("maps intake-blocked statuses to needs_information", () => {
    for (const status of ["incomplete", "needs_followup", "needs_clarification", "awaiting_customer_details"]) {
      const derived = deriveTripLifecycle(makeTrip({ status, stage: "discovery" }));
      expect(derived.state).toBe("needs_information");
      expect(derived.tone).toBe("warn");
    }
  });

  it("maps ASK_FOLLOWUP decision state to needs_information with a blocker", () => {
    const derived = deriveTripLifecycle(
      makeTrip({
        status: "active",
        decision: { decision_state: "ASK_FOLLOWUP" } as Trip["decision"],
      }),
    );
    expect(derived.state).toBe("needs_information");
    expect(derived.blockers.some((b) => b.id === "missing_info")).toBe(true);
  });

  it("maps PROCEED_TRAVELER_SAFE to awaiting_customer_approval", () => {
    const derived = deriveTripLifecycle(
      makeTrip({
        status: "active",
        stage: "proposal",
        decision: { decision_state: "PROCEED_TRAVELER_SAFE" } as Trip["decision"],
      }),
    );
    expect(derived.state).toBe("awaiting_customer_approval");
    expect(derived.tone).toBe("info");
  });

  it("maps quote-ready statuses to planning", () => {
    const derived = deriveTripLifecycle(makeTrip({ status: "ready_to_quote", stage: "shortlist" }));
    expect(derived.state).toBe("planning");
  });

  it("maps booking stage and ready_to_book to booked_side", () => {
    expect(deriveTripLifecycle(makeTrip({ stage: "booking" })).state).toBe("booked_side");
    expect(deriveTripLifecycle(makeTrip({ status: "ready_to_book", stage: "proposal" })).state).toBe(
      "booked_side",
    );
  });

  it("maps review escalation to escalated with a danger blocker", () => {
    const derived = deriveTripLifecycle(
      makeTrip({ status: "active", stage: "proposal", review_status: "escalated" }),
    );
    expect(derived.state).toBe("escalated");
    expect(derived.tone).toBe("danger");
    expect(derived.blockers.some((b) => b.severity === "danger")).toBe(true);
  });

  it("maps status escalation to escalated", () => {
    const derived = deriveTripLifecycle(makeTrip({ status: "escalated" }));
    expect(derived.state).toBe("escalated");
  });

  it("escalation outranks other states regardless of stage", () => {
    const derived = deriveTripLifecycle(
      makeTrip({
        status: "ready_to_book",
        stage: "booking",
        review_status: "escalated",
      }),
    );
    expect(derived.state).toBe("escalated");
  });

  it("maps completed status to completed", () => {
    const derived = deriveTripLifecycle(makeTrip({ status: "completed" }));
    expect(derived.state).toBe("completed");
    expect(derived.tone).toBe("success");
  });

  it("maps delivered (review-approved) status to completed (F-34)", () => {
    const derived = deriveTripLifecycle(makeTrip({ status: "delivered", stage: "output" }));
    expect(derived.state).toBe("completed");
    expect(derived.tone).toBe("success");
  });

  it("maps active (intake-complete) status to intake, not invisible (F-33)", () => {
    const derived = deriveTripLifecycle(makeTrip({ status: "active", stage: "discovery" }));
    expect(derived.state).toBe("intake");
  });

  it("surfaces review pending/rejected/revision as blockers", () => {
    const pending = deriveTripLifecycle(makeTrip({ status: "active", review_status: "pending" }));
    expect(pending.blockers.some((b) => b.id === "review_pending")).toBe(true);

    const rejected = deriveTripLifecycle(makeTrip({ status: "active", review_status: "rejected" }));
    expect(rejected.blockers.some((b) => b.id === "review_rejected" && b.severity === "danger")).toBe(true);

    const revision = deriveTripLifecycle(
      makeTrip({ status: "active", review_status: "revision_needed" }),
    );
    expect(revision.blockers.some((b) => b.id === "revision_needed")).toBe(true);
  });

  it("surfaces non-ready booking readiness as a blocker", () => {
    const derived = deriveTripLifecycle(
      makeTrip({
        status: "active",
        agentOperations: { bookingReadinessStatus: "awaiting_documents" },
      } as Partial<Trip>),
    );
    expect(
      derived.blockers.some((b) => b.id === "booking_readiness" && b.label.includes("awaiting_documents")),
    ).toBe(true);
  });

  it("degrades unknown vocabularies to intake without crashing", () => {
    const derived = deriveTripLifecycle(
      makeTrip({ status: "some_future_status", stage: "some_future_stage" }),
    );
    expect(derived.state).toBe("intake");
  });
});

describe("isTripEscalated", () => {
  it("is true only for escalated derivation", () => {
    expect(isTripEscalated(makeTrip({ review_status: "escalated" }))).toBe(true);
    expect(isTripEscalated(makeTrip({ status: "active" }))).toBe(false);
  });
});

describe("decisionStateLabel", () => {
  it("maps known states and passes unknowns through", () => {
    expect(decisionStateLabel("ASK_FOLLOWUP")).toBe("Waiting on Customer");
    expect(decisionStateLabel("PROCEED_TRAVELER_SAFE")).toBe("Ready to Book");
    expect(decisionStateLabel("SOME_NEW_STATE")).toBe("SOME_NEW_STATE");
    expect(decisionStateLabel(undefined)).toBe("");
  });
});

describe("getNeedsInformation (I-4)", () => {
  it("consolidates ASK_FOLLOWUP + blocked status into one answer with sources", () => {
    const needed = getNeedsInformation(
      makeTrip({ status: "needs_followup", decision: { decision_state: "ASK_FOLLOWUP" } as Trip["decision"] }),
    );
    expect(needed.needed).toBe(true);
    expect(needed.sources).toContain("status");
    expect(needed.sources).toContain("decision_state");
  });

  it("reports follow_up_status as a source when not completed", () => {
    const needed = getNeedsInformation(
      makeTrip({
        status: "active",
        analytics: { follow_up_status: "pending" },
      } as Partial<Trip>),
    );
    expect(needed.needed).toBe(true);
    expect(needed.sources).toContain("follow_up_status");
    expect(needed.followUpStatus).toBe("pending");
  });

  it("is false for clean in-progress trips", () => {
    const needed = getNeedsInformation(makeTrip({ status: "in_progress", stage: "proposal" }));
    expect(needed.needed).toBe(false);
  });
});

describe("getAllowedActions (I-3)", () => {
  it("forbids quote generation while needs_information", () => {
    const actions = getAllowedActions(makeTrip({ status: "incomplete" }));
    expect(actions.forbidden.some((f) => f.includes("NB01"))).toBe(true);
    expect(actions.nextActions.length).toBeGreaterThan(0);
  });

  it("forbids self-promotion while escalated", () => {
    const actions = getAllowedActions(makeTrip({ status: "active", review_status: "escalated" }));
    expect(actions.forbidden.some((f) => f.includes("human resolve"))).toBe(true);
  });
});

describe("recovery blocker (I-5)", () => {
  it("surfaces analytics recovery_status as a blocker", () => {
    const derived = deriveTripLifecycle(
      makeTrip({ status: "active", analytics: { recovery_status: "IN_RECOVERY" } } as Partial<Trip>),
    );
    expect(derived.blockers.some((b) => b.id === "recovery")).toBe(true);
  });
});
