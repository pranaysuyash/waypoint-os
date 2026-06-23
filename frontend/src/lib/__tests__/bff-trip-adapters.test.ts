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
        trip_purpose: { value: ["family holiday"] },
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
    contradictions: [
      {
        field_name: "flight_hotel_mismatch",
        values: ["Flight arrives after check-in", "Hotel check-in is same-day"],
      },
    ],
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
      tripPurpose: "family holiday",
      state: "amber",
      age: "2d",
      createdAt: "2026-04-25T12:00:00.000Z",
      updatedAt: "2026-04-26T12:00:00.000Z",
      party: 4,
      dateWindow: "May 1-8",
      origin: "Delhi",
      budget: "125000",
      status: "assigned",
      review_status: "pending",
      reviewedBy: "owner",
      reviewedAt: "2026-04-26T13:00:00.000Z",
      reviewNotes: "Check supplier pricing",
      action: "REVIEW",
    });

    expect(trip.analytics?.requiresReview).toBe(true);
    expect(trip.decision?.decision_state).toBe("ASK_FOLLOWUP");
    expect(trip.decision?.contradictions).toEqual(["flight_hotel_mismatch"]);
    expect(trip.rawInput).toEqual({ fixture_id: "FIX-001" });

    // packet is hydrated directly from extracted without reshaping
    expect(trip.packet).toEqual(spineTrip.extracted);
  });

  it("keeps missing budget as a missing display value instead of fabricating zero", () => {
    const tripWithoutBudget = transformSpineTripToTrip(
      {
        ...spineTrip,
        extracted: {
          ...spineTrip.extracted,
          facts: {
            ...spineTrip.extracted.facts,
            budget: undefined,
          },
        },
        budget: null,
      },
      now
    );

    expect(tripWithoutBudget.budget).toBe("Budget missing");
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
      tripPurpose: "family holiday",
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

  it("preserves validation.readiness from backend response", () => {
    const tripWithReadiness = transformSpineTripToTrip(
      {
        ...spineTrip,
        validation: {
          is_valid: true,
          errors: [],
          warnings: [],
          readiness: {
            highest_ready_tier: "quote_ready",
            suggested_next_stage: "shortlist",
            should_auto_advance_stage: false,
            missing_for_next: ["trip_priorities", "date_flexibility"],
            tiers: {
              intake_minimum: { tier: "intake_minimum", ready: true, met: ["destination_candidates", "date_window"], unmet: [] },
              quote_ready: { tier: "quote_ready", ready: true, met: [], unmet: [] },
              proposal_ready: { tier: "proposal_ready", ready: false, met: [], unmet: ["trip_priorities", "date_flexibility"] },
              booking_ready: { tier: "booking_ready", ready: false, met: [], unmet: ["booking_data"] },
            },
          },
        },
      },
      now
    );

    expect((tripWithReadiness.validation as Record<string, unknown>)?.readiness).toMatchObject({
      highest_ready_tier: "quote_ready",
      suggested_next_stage: "shortlist",
      should_auto_advance_stage: false,
      missing_for_next: ["trip_priorities", "date_flexibility"],
    });
  });

  it("gracefully handles missing readiness in backend response", () => {
    const tripWithoutReadiness = transformSpineTripToTrip(spineTrip, now);
    expect((tripWithoutReadiness.validation as Record<string, unknown>)?.readiness).toBeUndefined();
  });

  it("preserves backend product-agent operation packets for operator surfaces", () => {
    const tripWithAgentOperations = transformSpineTripToTrip(
      {
        ...spineTrip,
        document_readiness_checklist: {
          risk_level: "high",
          operator_next_action: "verify_documents",
        },
        destination_intelligence_snapshot: {
          risk_level: "medium",
          checked_at: "2026-05-04T00:00:00.000Z",
        },
        weather_pivot_packet: {
          risk_level: "medium",
          operator_next_action: "review_weather_pivots",
        },
        booking_readiness_assessment: {
          status: "blocked",
          operator_next_action: "collect_booking_data",
        },
        flight_status_snapshot: {
          risk_level: "high",
          operator_next_action: "review_delay",
        },
        ticket_price_watch_alert: {
          risk_level: "medium",
          operator_next_action: "revalidate_quote",
        },
        quote_revalidation_required: true,
        safety_alert_packet: {
          risk_level: "low",
          operator_next_action: "monitor_safety_alerts",
        },
        gds_schema_bridge: {
          object_count: 2,
        },
        pnr_shadow_check: {
          risk_level: "high",
          issues: [{ category: "traveler_name_mismatch" }],
        },
        supplier_intelligence_snapshot: {
          supplier_risks: [{ supplier: "Slow Hotel DMC" }],
        },
        supplier_risk_level: "medium",
        last_agent_action: "supplier_intelligence_agent",
        last_agent_action_at: "2026-05-04T01:00:00.000Z",
      },
      now
    );

    expect(tripWithAgentOperations.agentOperations).toMatchObject({
      documentReadinessChecklist: {
        risk_level: "high",
        operator_next_action: "verify_documents",
      },
      destinationIntelligenceSnapshot: {
        risk_level: "medium",
      },
      bookingReadinessAssessment: {
        status: "blocked",
      },
      quoteRevalidationRequired: true,
      supplierRiskLevel: "medium",
      lastAgentAction: "supplier_intelligence_agent",
      lastAgentActionAt: "2026-05-04T01:00:00.000Z",
    });
  });

  it("preserves frontier_result on trip transform without reshaping payload", () => {
    const tripWithFrontier = transformSpineTripToTrip(
      {
        ...spineTrip,
        frontier_result: {
          ghost_triggered: true,
          ghost_workflow_id: "fw-7",
          sentiment_score: 0.91,
          anxiety_alert: false,
          specialty_knowledge: [{ niche: "visa", checklists: ["check passport"], urgency: "high" }],
        },
      },
      now
    );

    expect(tripWithFrontier).toMatchObject({
      frontier_result: {
        ghost_triggered: true,
        ghost_workflow_id: "fw-7",
        sentiment_score: 0.91,
      },
    });
  });

  it("handles manual field edits stored at top-level (three-tier fallback)", () => {
    const tripWithManualEdits = {
      id: "trip-manual-123",
      status: "incomplete",
      created_at: "2026-05-01T12:00:00.000Z",
      updated_at: "2026-05-16T12:00:00.000Z",
      // Top-level fields set by user via PATCH
      dateWindow: "June 15-22, 2026",
      destination: "Paris",
      budget: 15000,
      origin: "New York",
      extracted: {
        facts: {
          // No AI extractions; only top-level manual edits exist
        },
      },
      validation: { is_valid: true, errors: [], warnings: [] },
      decision: { action: "QUOTE", confidence_score: 0.8, hard_blockers: [] },
    };

    const trip = transformSpineTripToTrip(tripWithManualEdits, now);

    // Verify adapters fall back to top-level fields when extraction missing
    expect(trip.dateWindow).toBe("June 15-22, 2026");
    expect(trip.destination).toBe("Paris");
    expect(trip.budget).toBe("15000");
    expect(trip.origin).toBe("New York");
  });

  it("top-level canonical field wins over AI extraction when both present", () => {
    const tripWithBoth = {
      id: "trip-priority-123",
      status: "assigned",
      created_at: "2026-05-01T12:00:00.000Z",
      updated_at: "2026-05-16T12:00:00.000Z",
      // Top-level origin: set by user PATCH or TripResponse canonical field
      origin: "User-Entered Origin",
      extracted: {
        facts: {
          // AI also has a value, but manual edit takes priority
          origin_city: {
            value: "AI-Extracted Origin",
            confidence: 0.9,
            authority_level: "ai_extraction",
          },
        },
      },
      validation: { is_valid: true, errors: [], warnings: [] },
      decision: { action: "QUOTE", confidence_score: 0.8, hard_blockers: [] },
    };

    const trip = transformSpineTripToTrip(tripWithBoth, now);

    // manual/top-level → extracted → raw inference; manual edit must win
    expect(trip.origin).toBe("User-Entered Origin");
  });

  // ── Canonical field priority: remaining four resolver functions ────────

  const baseTrip = {
    id: "trip-canon-base",
    status: "assigned",
    created_at: "2026-05-01T12:00:00.000Z",
    updated_at: "2026-05-16T12:00:00.000Z",
    validation: { is_valid: true, errors: [], warnings: [] },
    decision: { action: "QUOTE", confidence_score: 0.8, hard_blockers: [] },
  };

  it("top-level destination beats extracted destination", () => {
    const trip = transformSpineTripToTrip({
      ...baseTrip,
      destination: "Manual Destination",
      extracted: {
        facts: {
          destination_candidates: { value: ["AI Destination"] },
        },
      },
    }, now);
    expect(trip.destination).toBe("Manual Destination");
  });

  it("top-level dateWindow beats extracted date window", () => {
    const trip = transformSpineTripToTrip({
      ...baseTrip,
      dateWindow: "July 1-7, 2026",
      extracted: {
        facts: {
          date_window: { value: "AI Date Window" },
        },
      },
    }, now);
    expect(trip.dateWindow).toBe("July 1-7, 2026");
  });

  it("top-level tripType beats extracted trip type", () => {
    const trip = transformSpineTripToTrip({
      ...baseTrip,
      tripType: "adventure",
      extracted: {
        facts: {
          primary_intent: { value: ["luxury"] },
        },
      },
    }, now);
    expect(trip.type).toBe("adventure");
  });

  it("top-level party beats extracted party size", () => {
    const trip = transformSpineTripToTrip({
      ...baseTrip,
      party: 4,
      extracted: {
        facts: {
          party_profile: { value: 9 },
        },
      },
    }, now);
    expect(trip.party).toBe(4);
  });

  it("extracted fact wins over raw inference when no top-level canonical value present", () => {
    const trip = transformSpineTripToTrip({
      ...baseTrip,
      // No top-level destination, dateWindow, party, or tripType
      extracted: {
        facts: {
          destination_candidates: { value: ["AI-Only Destination"] },
          date_window: { value: "AI-Only DateWindow" },
          party_profile: { value: 3 },
          primary_intent: { value: ["honeymoon"] },
        },
      },
    }, now);
    expect(trip.destination).toBe("AI-Only Destination");
    expect(trip.dateWindow).toBe("AI-Only DateWindow");
    expect(trip.party).toBe(3);
    expect(trip.type).toBe("honeymoon");
  });
});
