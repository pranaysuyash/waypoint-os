/**
 * trip-lifecycle.ts — Derived trip lifecycle read-model (register N-4).
 *
 * One canonical derivation joining the six unjoined status vocabularies the
 * backend already persists (trip.status, trip.stage, decision.decision_state,
 * review_status, readiness snapshots) onto the blueprint lifecycle:
 *
 *   intake → needs_information → feasibility → planning →
 *   awaiting_customer_approval → booked_side → in_trip → completed
 *   (+ escalated reachable from anywhere)
 *
 * This is the operator-facing projection ONLY: the state machine underneath
 * (spine_api/core/trip_status.py) remains the enforcement layer. See
 * Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md §5 N-4.
 *
 * Inputs are the verified API contract fields on `Trip` (@/lib/api-client) —
 * no assumed shapes. Unknown values degrade to the most conservative state
 * with the raw signal surfaced as a blocker, never silently dropped.
 */

import type { Trip } from "@/lib/api-client";

export type TripLifecycleState =
  | "intake"
  | "needs_information"
  | "feasibility"
  | "planning"
  | "awaiting_customer_approval"
  | "booked_side"
  | "in_trip"
  | "completed"
  | "escalated";

export type TripBlockerSeverity = "info" | "warn" | "danger";

export interface TripBlocker {
  id: string;
  label: string;
  severity: TripBlockerSeverity;
}

export interface TripLifecycleDerived {
  state: TripLifecycleState;
  label: string;
  tone: "neutral" | "info" | "warn" | "danger" | "success";
  nextActions: string[];
  blockers: TripBlocker[];
}

/** Backend trip statuses meaning intake is blocked (mirrors spine_api/core/trip_status.py). */
const INTAKE_BLOCKED_STATUSES = new Set([
  "incomplete",
  "needs_followup",
  "needs_clarification",
  "awaiting_customer_details",
]);

const DECISION_STATE_LABELS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE: "Ready to Book",
  PROCEED_INTERNAL_DRAFT: "Draft Quote",
  BRANCH_OPTIONS: "Needs Options",
  STOP_NEEDS_REVIEW: "Needs Attention",
  STOP_REVIEW: "Needs Attention",
  ASK_FOLLOWUP: "Waiting on Customer",
};

export function decisionStateLabel(decisionState?: string): string {
  if (!decisionState) return "";
  return DECISION_STATE_LABELS[decisionState] ?? decisionState;
}

function buildBlockers(trip: Trip): TripBlocker[] {
  const blockers: TripBlocker[] = [];
  const status = (trip.status ?? "").toLowerCase();
  const decisionState = trip.decision?.decision_state;

  if (trip.review_status === "escalated" || status === "escalated") {
    blockers.push({ id: "escalated", label: "Escalated — needs an owner", severity: "danger" });
  }
  if (trip.review_status === "rejected") {
    blockers.push({ id: "review_rejected", label: "Quote declined by reviewer", severity: "danger" });
  }
  if (trip.review_status === "revision_needed") {
    blockers.push({ id: "revision_needed", label: "Revisions requested", severity: "warn" });
  }
  if (status === "blocked") {
    blockers.push({ id: "status_blocked", label: "Trip is blocked", severity: "warn" });
  }
  if (INTAKE_BLOCKED_STATUSES.has(status) || decisionState === "ASK_FOLLOWUP") {
    blockers.push({ id: "missing_info", label: "Customer information missing", severity: "warn" });
  }
  if (trip.review_status === "pending") {
    blockers.push({ id: "review_pending", label: "Awaiting review", severity: "info" });
  }

  // Recovery mode (I-5): analytics.recovery_status IN_RECOVERY previously had
  // no aggregated surface — trips sat in recovery invisible to queues.
  const recoveryStatus = getAnalyticsString(trip, "recovery_status");
  if (recoveryStatus) {
    blockers.push({ id: "recovery", label: `In recovery (${recoveryStatus})`, severity: "warn" });
  }

  const bookingReadiness = trip.agentOperations?.bookingReadinessStatus;
  if (bookingReadiness && bookingReadiness !== "ready") {
    blockers.push({
      id: "booking_readiness",
      label: `Booking readiness: ${bookingReadiness}`,
      severity: "warn",
    });
  }

  return blockers;
}

/** Read a string out of trip analytics without any shape assumptions. */
function getAnalyticsString(trip: Trip, key: string): string | undefined {
  const analytics = (trip as { analytics?: Record<string, unknown> }).analytics;
  if (!analytics || typeof analytics !== "object") return undefined;
  const value = analytics[key];
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

/**
 * I-4: unified needs-information answer. One concept previously lived in
 * three places (inbox lead status, follow_up_status pending/snoozed/completed,
 * decision ASK_FOLLOWUP) — this consolidates them into a single read-model
 * answer with the contributing sources named.
 */
export interface NeedsInformation {
  needed: boolean;
  sources: string[];
  followUpStatus?: string;
}

export function getNeedsInformation(trip: Trip): NeedsInformation {
  const sources: string[] = [];
  const status = (trip.status ?? "").toLowerCase();
  const decisionState = trip.decision?.decision_state;

  if (INTAKE_BLOCKED_STATUSES.has(status)) sources.push("status");
  if (decisionState === "ASK_FOLLOWUP") sources.push("decision_state");

  const analytics = (trip as { analytics?: Record<string, unknown> }).analytics;
  const followUpStatus =
    typeof trip.followUpDueDate === "string" && trip.followUpDueDate
      ? undefined
      : typeof analytics?.follow_up_status === "string"
        ? (analytics.follow_up_status as string)
        : undefined;
  if (followUpStatus && followUpStatus !== "completed") sources.push("follow_up_status");

  return {
    needed: sources.length > 0,
    sources,
    followUpStatus,
  };
}

/**
 * I-3: operator-facing allowed/next actions for the trip's lifecycle state,
 * computed from the same derivation the LifecycleChip renders — one answer
 * everywhere.
 */
export function getAllowedActions(trip: Trip): {
  nextActions: string[];
  forbidden: string[];
} {
  const derived = deriveTripLifecycle(trip);
  const forbidden: string[] = [];
  if (derived.state === "needs_information") {
    forbidden.push("Quote generation (NB01 gate)");
  }
  if (derived.state === "escalated") {
    forbidden.push("Status self-promotion (human resolve required)");
  }
  if (derived.state === "awaiting_customer_approval") {
    forbidden.push("Non-refundable bookings");
  }
  return { nextActions: derived.nextActions, forbidden };
}

/**
 * Derive the operator-facing lifecycle state. Precedence: escalated >
 * completed > in_trip (canonical "active" alias) > needs_information >
 * awaiting_customer_approval > booked_side > planning > feasibility > intake.
 */
export function deriveTripLifecycle(trip: Trip): TripLifecycleDerived {
  const status = (trip.status ?? "").toLowerCase();
  const stage = (trip.stage ?? "").toLowerCase();
  const decisionState = trip.decision?.decision_state;

  const blockers = buildBlockers(trip);

  let state: TripLifecycleState;
  if (trip.review_status === "escalated" || status === "escalated") {
    state = "escalated";
  } else if (status === "completed" || status === "delivered") {
    // "delivered" = review-approval terminal state (src/analytics/review.py:101);
    // recognized alongside "completed" (F-34).
    state = "completed";
  } else if (INTAKE_BLOCKED_STATUSES.has(status) || decisionState === "ASK_FOLLOWUP") {
    state = "needs_information";
  } else if (decisionState === "PROCEED_TRAVELER_SAFE") {
    state = "awaiting_customer_approval";
  } else if (stage === "booking" || status === "ready_to_book") {
    state = "booked_side";
  } else if (status === "ready_to_quote" || stage === "shortlist" || stage === "proposal") {
    state = "planning";
  } else if (
    decisionState === "PROCEED_INTERNAL_DRAFT" ||
    decisionState === "BRANCH_OPTIONS" ||
    decisionState === "STOP_NEEDS_REVIEW" ||
    decisionState === "STOP_REVIEW"
  ) {
    state = "feasibility";
  } else if (status === "active") {
    // Canonical in_trip alias, audit-gated in the ratified 12-state machine
    // (spine_api/core/trip_lifecycle.py): an active trip is in-flight work,
    // not an intake lead (FND-0120). Lowest-precedence positive state — the
    // richer signals above (needs_information, decision states, stages)
    // always outrank the raw alias.
    state = "in_trip";
  } else {
    state = "intake";
  }

  const LABELS: Record<TripLifecycleState, { label: string; tone: TripLifecycleDerived["tone"] }> = {
    intake: { label: "Intake", tone: "neutral" },
    needs_information: { label: "Needs Information", tone: "warn" },
    feasibility: { label: "Feasibility", tone: "info" },
    planning: { label: "Planning", tone: "info" },
    awaiting_customer_approval: { label: "Awaiting Customer", tone: "info" },
    booked_side: { label: "Booked Side", tone: "success" },
    in_trip: { label: "In Trip", tone: "info" },
    completed: { label: "Completed", tone: "success" },
    escalated: { label: "Escalated", tone: "danger" },
  };

  const NEXT_ACTIONS: Record<TripLifecycleState, string[]> = {
    intake: ["Review extracted packet", "Fill in missing trip details"],
    needs_information: ["Send follow-up to customer", "Fill missing fields manually"],
    feasibility: ["Review options", "Run quote assessment"],
    planning: ["Review options", "Run quote assessment"],
    awaiting_customer_approval: ["Send quote to customer", "Await customer response"],
    booked_side: ["Execute booking tasks", "Confirm components"],
    in_trip: ["Monitor disruptions", "Stand by for traveler requests"],
    completed: ["Archive trip", "Collect feedback"],
    escalated: ["Take over or reassign", "Resolve the blocking issue"],
  };

  return {
    state,
    label: LABELS[state].label,
    tone: LABELS[state].tone,
    nextActions: NEXT_ACTIONS[state],
    blockers,
  };
}

/** True when the trip currently sits in the escalation path (review or status). */
export function isTripEscalated(trip: Trip): boolean {
  return deriveTripLifecycle(trip).state === "escalated";
}
