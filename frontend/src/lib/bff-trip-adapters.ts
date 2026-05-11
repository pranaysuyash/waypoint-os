import type { AgentOperationsMetadata, Trip } from "@/lib/api-client";
import type { FeeCalculationResult, StrategyOutput, PromptBundle } from "@/types/spine";
import type { InboxTrip, TripPriority } from "@/types/governance";

type JsonRecord = Record<string, unknown>;
type TripState = Trip["state"];
type SlaStatus = InboxTrip["slaStatus"];
type TripLifecycleStatus = NonNullable<Trip["status"]>;

const STATUS_TO_STATE: Record<string, TripState> = {
  new: "blue",
  assigned: "amber",
  in_progress: "amber",
  completed: "green",
  cancelled: "red",
};

const STATUS_TO_INBOX_STAGE: Record<string, string> = {
  new: "intake",
  assigned: "options",
  in_progress: "details",
  completed: "booking",
  cancelled: "completed",
};

const STAGE_NUMBERS: Record<string, number> = {
  intake: 1,
  options: 2,
  details: 3,
  review: 4,
  booking: 5,
  completed: 6,
};

const DEFAULT_BUDGET_BREAKDOWN = {
  verdict: "not_realistic",
  buckets: [],
  missing_buckets: [],
  total_estimated_low: 0,
  total_estimated_high: 0,
  budget_stated: null,
  gap: null,
  risks: ["budget_unknown"],
  critical_changes: ["Provide a numeric budget for decomposition"],
  must_confirm: [],
  alternative: null,
  maturity: "heuristic",
};

const WORKSPACE_STATUSES = new Set<TripLifecycleStatus>([
  "assigned",
  "in_progress",
  "ready_to_quote",
  "ready_to_book",
  "blocked",
]);

const INBOX_STATUSES = new Set<TripLifecycleStatus>([
  "new",
  "incomplete",
  "needs_followup",
  "awaiting_customer_details",
  "snoozed",
]);

export function isWorkspaceTrip(trip: Trip): boolean {
  const lifecycleStatus = trip.status;
  return typeof lifecycleStatus === "string" && WORKSPACE_STATUSES.has(lifecycleStatus as TripLifecycleStatus);
}

export function isInboxTrip(trip: Trip): boolean {
  const lifecycleStatus = trip.status;
  return typeof lifecycleStatus === "string" && INBOX_STATUSES.has(lifecycleStatus as TripLifecycleStatus);
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getNestedValue<T = unknown>(
  obj: unknown,
  path: string,
  defaultValue: T
): T {
  const parts = path.split(".");
  let current: unknown = obj;

  for (const part of parts) {
    if (Array.isArray(current)) {
      const index = Number(part);
      if (!Number.isInteger(index)) return defaultValue;
      current = current[index];
      continue;
    }
    if (!isRecord(current)) return defaultValue;
    current = current[part];
  }

  return current === undefined || current === null ? defaultValue : (current as T);
}

function firstPresent<T>(...values: T[]): T | undefined {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

function asRecord(value: unknown): JsonRecord {
  return isRecord(value) ? value : {};
}

function asString(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.length > 0) return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function asNumber(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number(value.replace(/[^\d.-]/g, ""));
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function asUnknownArray(value: unknown): unknown[] | undefined {
  return Array.isArray(value) ? value : undefined;
}

function optionalRecord(value: unknown): Record<string, unknown> | undefined {
  return isRecord(value) ? value : undefined;
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function setIfDefined<K extends keyof AgentOperationsMetadata>(
  target: AgentOperationsMetadata,
  key: K,
  value: AgentOperationsMetadata[K] | undefined
): void {
  if (value !== undefined) {
    target[key] = value;
  }
}

function extractAgentOperations(trip: JsonRecord): AgentOperationsMetadata | undefined {
  const agentOperations: AgentOperationsMetadata = {};
  setIfDefined(agentOperations, "documentReadinessChecklist", optionalRecord(trip.document_readiness_checklist));
  setIfDefined(agentOperations, "documentRiskLevel", optionalString(trip.document_risk_level));
  setIfDefined(agentOperations, "mustConfirmDocuments", asUnknownArray(trip.must_confirm_documents));
  setIfDefined(agentOperations, "destinationIntelligenceSnapshot", optionalRecord(trip.destination_intelligence_snapshot));
  setIfDefined(agentOperations, "destinationRiskLevel", optionalString(trip.destination_risk_level));
  setIfDefined(agentOperations, "destinationIntelligenceRecommendations", asUnknownArray(trip.destination_intelligence_recommendations));
  setIfDefined(agentOperations, "weatherPivotPacket", optionalRecord(trip.weather_pivot_packet));
  setIfDefined(agentOperations, "weatherPivotRiskLevel", optionalString(trip.weather_pivot_risk_level));
  setIfDefined(agentOperations, "constraintFeasibilityAssessment", optionalRecord(trip.constraint_feasibility_assessment));
  setIfDefined(agentOperations, "feasibilityStatus", optionalString(trip.feasibility_status));
  setIfDefined(agentOperations, "proposalReadinessAssessment", optionalRecord(trip.proposal_readiness_assessment));
  setIfDefined(agentOperations, "proposalReadinessStatus", optionalString(trip.proposal_readiness_status));
  setIfDefined(agentOperations, "bookingReadinessAssessment", optionalRecord(trip.booking_readiness_assessment));
  setIfDefined(agentOperations, "bookingReadinessStatus", optionalString(trip.booking_readiness_status));
  setIfDefined(agentOperations, "flightStatusSnapshot", optionalRecord(trip.flight_status_snapshot));
  setIfDefined(agentOperations, "flightDisruptionRiskLevel", optionalString(trip.flight_disruption_risk_level));
  setIfDefined(agentOperations, "ticketPriceWatchAlert", optionalRecord(trip.ticket_price_watch_alert));
  setIfDefined(agentOperations, "quoteRevalidationRequired", typeof trip.quote_revalidation_required === "boolean" ? trip.quote_revalidation_required : undefined);
  setIfDefined(agentOperations, "priceWatchRiskLevel", optionalString(trip.price_watch_risk_level));
  setIfDefined(agentOperations, "safetyAlertPacket", optionalRecord(trip.safety_alert_packet));
  setIfDefined(agentOperations, "safetyRiskLevel", optionalString(trip.safety_risk_level));
  setIfDefined(agentOperations, "gdsSchemaBridge", optionalRecord(trip.gds_schema_bridge));
  setIfDefined(agentOperations, "pnrShadowCheck", optionalRecord(trip.pnr_shadow_check));
  setIfDefined(agentOperations, "pnrShadowRiskLevel", optionalString(trip.pnr_shadow_risk_level));
  setIfDefined(agentOperations, "supplierIntelligenceSnapshot", optionalRecord(trip.supplier_intelligence_snapshot));
  setIfDefined(agentOperations, "supplierRiskLevel", optionalString(trip.supplier_risk_level));
  setIfDefined(agentOperations, "canonicalTravelObjects", asUnknownArray(trip.canonical_travel_objects));
  setIfDefined(agentOperations, "lastAgentAction", optionalString(trip.last_agent_action));
  setIfDefined(agentOperations, "lastAgentActionAt", optionalString(trip.last_agent_action_at));

  return Object.values(agentOperations).some((value) => value !== undefined)
    ? agentOperations
    : undefined;
}

function calculateAge(isoDateString: string, now: Date = new Date()): string {
  const created = new Date(isoDateString);
  const diffMs = now.getTime() - created.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w`;
  return `${Math.floor(diffDays / 30)}mo`;
}

function extractedValue(spineTrip: unknown, field: string, fallback: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, `extracted.facts.${field}.value.0`, undefined),
    getNestedValue(spineTrip, `extracted.facts.${field}.value`, undefined),
    getNestedValue(spineTrip, `extracted.trip_metadata.${field}.value`, undefined),
    getNestedValue(spineTrip, `extracted.trip_metadata.${field}`, undefined),
    getNestedValue(spineTrip, `extracted.${field}.value`, undefined),
    getNestedValue(spineTrip, `extracted.${field}`, undefined),
    fallback
  );
}

function destinationValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.destination_candidates.value.0", undefined),
    extractedValue(spineTrip, "destination", undefined),
    getNestedValue(spineTrip, "destination", undefined),
    "Unknown"
  );
}

function tripTypeValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.primary_intent.value.0", undefined),
    getNestedValue(spineTrip, "extracted.facts.trip_purpose.value.0", undefined),
    extractedValue(spineTrip, "primary_intent", undefined),
    extractedValue(spineTrip, "trip_purpose", undefined),
    "leisure"
  );
}

function partySizeValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.party_profile.value", undefined),
    getNestedValue(spineTrip, "extracted.facts.party_size.value", undefined),
    getNestedValue(spineTrip, "extracted.trip_metadata.party_profile.size", undefined),
    extractedValue(spineTrip, "party_size", undefined),
    getNestedValue(spineTrip, "extracted.party_profile.size", undefined),
    1
  );
}

function budgetValue(spineTrip: unknown): number {
  return asNumber(
    firstPresent(
      getNestedValue(spineTrip, "extracted.facts.budget.value", undefined),
      getNestedValue(spineTrip, "extracted.trip_metadata.budget.value", undefined),
      getNestedValue(spineTrip, "extracted.budget.value", undefined),
      getNestedValue(spineTrip, "extracted.budget", undefined),
      0
    ),
    0
  );
}

function dateWindowValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.date_window.value", undefined),
    extractedValue(spineTrip, "date_window", undefined),
    getNestedValue(spineTrip, "dateWindow", undefined),
    "TBD"
  );
}

function originCityValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.origin_city.value", undefined),
    extractedValue(spineTrip, "origin_city", undefined),
    extractedValue(spineTrip, "origin", undefined),
    "TBD"
  );
}

function computeDaysInCurrentStage(spineTrip: JsonRecord, now: Date): number {
  const timestamps: string[] = [];
  const createdAt = spineTrip.created_at;
  if (typeof createdAt === "string") timestamps.push(createdAt);

  const events = getNestedValue(spineTrip, "extracted.events", []);
  if (Array.isArray(events)) {
    for (const event of events) {
      const timestamp = getNestedValue(event, "timestamp", undefined);
      if (typeof timestamp === "string") timestamps.push(timestamp);
    }
  }

  const validTimes: number[] = [];
  for (const timestamp of timestamps) {
    const time = new Date(timestamp).getTime();
    if (Number.isFinite(time)) validTimes.push(time);
  }
  if (validTimes.length === 0) return 0;

  const mostRecent = Math.max(...validTimes);
  return Math.max(0, Math.floor((now.getTime() - mostRecent) / (1000 * 60 * 60 * 24)));
}

function computeSlaStatus(daysInCurrentStage: number): SlaStatus {
  if (daysInCurrentStage > 7) return "breached";
  if (daysInCurrentStage > 4) return "at_risk";
  return "on_track";
}

function extractCustomerName(trip: Trip): string {
  const fixtureId = getNestedValue<unknown>(trip.rawInput, "fixture_id", undefined);
  if (typeof fixtureId === "string" && fixtureId.length > 0) {
    return `Customer ${fixtureId}`;
  }
  return `Client ${trip.id.slice(-6)}`;
}

function deriveInboxReference(source: JsonRecord, tripId: string): string {
  const explicitReference = asString(
    firstPresent(source.reference, source.trip_reference, source.tripReference, ""),
    ""
  );

  if (explicitReference && explicitReference !== tripId) {
    return explicitReference;
  }

  const raw = tripId.replace(/^trip[-_]/i, "");
  const normalized = raw.replace(/[^a-z0-9]/gi, "").toUpperCase();
  return normalized.slice(0, 4) || tripId.slice(-4).toUpperCase();
}

function extractFlags(trip: Trip, source: JsonRecord): string[] {
  const flags = new Set<string>();
  const validation = asRecord(trip.validation);
  const analytics = asRecord(trip.analytics);
  const decision = asRecord(trip.decision);

  const isValid = firstPresent(validation.isValid, validation.is_valid, true);
  if (isValid === false) {
    flags.add("incomplete");
  }

  const confidence = asNumber(
    firstPresent(decision.confidenceScore, decision.confidence_score, 0),
    0
  );
  if (confidence < 0.5) flags.add("details_unclear");

  if (decision.decisionState === "ASK_FOLLOWUP" || decision.decision_state === "ASK_FOLLOWUP") {
    flags.add("needs_clarification");
  }

  const hardBlockers = firstPresent(decision.hardBlockers, decision.hard_blockers, []);
  if (Array.isArray(hardBlockers) && hardBlockers.length > 0) {
    flags.add("incomplete");
  }

  const assignedTo = asString(firstPresent(source.assignedTo, source.assigned_to), "");
  if (!assignedTo) {
    flags.add("unassigned");
  }

  return Array.from(flags);
}

export function transformSpineTripToTrip(
  spineTrip: unknown,
  now: Date = new Date()
): Trip {
  const trip = asRecord(spineTrip);
  const analytics = asRecord(trip.analytics);
  const validation = asRecord(trip.validation);
  const decision = asRecord(trip.decision);
  const status = asString(trip.status, "new");
  const createdAt = asString(trip.created_at, now.toISOString());
  const budget = budgetValue(trip);

  return {
    id: asString(firstPresent(trip.id, trip.trip_id), ""),
    destination: asString(destinationValue(trip), "Unknown"),
    contactName: asString(getNestedValue(trip, "contactName", "") as string, ""),
    type: asString(tripTypeValue(trip), "leisure"),
    state: STATUS_TO_STATE[status] || (status as TripState) || "blue",
    age: calculateAge(createdAt, now),
    createdAt,
    updatedAt: asString(firstPresent(trip.updated_at, trip.created_at), createdAt),
    party: asNumber(partySizeValue(trip), 1),
    dateWindow: asString(dateWindowValue(trip), "TBD"),
    origin: asString(originCityValue(trip), "TBD"),
    budget: (() => {
      const rawText = getNestedValue(spineTrip, "extracted.facts.budget_raw_text.value", undefined);
      const budgetVal = getNestedValue(spineTrip, "extracted.facts.budget.value", undefined);
      return asString(rawText ?? budgetVal ?? budgetValue(spineTrip), "Budget missing");
    })(),
    packet: trip.extracted ?? undefined,
    status,
    stage: asString(trip.stage, "discovery") || "discovery",
    review_status: (analytics.review_status as Trip["review_status"]) ?? undefined,
    reviewedBy: asString(getNestedValue(analytics, "review_metadata.reviewed_by", ""), "") || undefined,
    reviewedAt: asString(getNestedValue(analytics, "review_metadata.reviewed_at", ""), "") || undefined,
    reviewNotes: asString(getNestedValue(analytics, "review_metadata.notes", ""), "") || undefined,
    action: asString(decision.action, "PENDING"),
    analytics: {
      marginPct: asNumber(analytics.margin_pct, 0),
      qualityScore: asNumber(analytics.quality_score, 0),
      qualityBreakdown: (analytics.quality_breakdown as Trip["analytics"] extends infer A
        ? A extends { qualityBreakdown?: infer Q } ? Q : never
        : never) || {
        completeness: 0,
        feasibility: 0,
        risk: 0,
        profitability: 0,
      },
      requiresReview: Boolean(analytics.requires_review),
      reviewReason: asString(analytics.review_reason, ""),
      feedback_reopen: Boolean(analytics.feedback_reopen),
      recovery_status: asString(analytics.recovery_status, ""),
      recovery_started_at: asString(analytics.recovery_started_at, ""),
      recovery_deadline: asString(analytics.recovery_deadline, ""),
      approvalRequiredForSend: Boolean(analytics.approval_required_for_send),
      sendPolicyReason: asString(analytics.send_policy_reason, ""),
      ownerReviewDeadline: asString(analytics.owner_review_deadline, ""),
      escalationSeverity: analytics.escalation_severity as "high" | "critical" | undefined,
      revisionCount: asNumber(analytics.revision_count, 0),
    },
    validation: ({
      is_valid: Boolean(validation.is_valid),
      errors: Array.isArray(validation.errors) ? validation.errors : [],
      warnings: Array.isArray(validation.warnings) ? validation.warnings : [],
      ambiguity_report: Array.isArray(validation.ambiguity_report)
        ? validation.ambiguity_report
        : [],
      evidence_coverage: asRecord(validation.evidence_coverage),
      readiness: (isRecord(validation.readiness) && Object.keys(validation.readiness).length > 0) ? validation.readiness : undefined,
    } as unknown) as Trip["validation"],
    decision: ({
      packet_id: asString(decision.packet_id, ""),
      current_stage: asString(decision.current_stage, "discovery"),
      operating_mode: asString(decision.operating_mode, "normal_intake"),
      decision_state: asString(decision.decision_state, "ASK_FOLLOWUP"),
      hard_blockers: asStringArray(decision.hard_blockers),
      soft_blockers: asStringArray(decision.soft_blockers),
      ambiguities: Array.isArray(decision.ambiguities) ? decision.ambiguities : [],
      contradictions: asStringArray(decision.contradictions),
      follow_up_questions: Array.isArray(decision.follow_up_questions)
        ? decision.follow_up_questions
        : [],
      branch_options: Array.isArray(decision.branch_options) ? decision.branch_options : [],
      rationale: decision.rationale ?? {
        hard_blockers: [],
        soft_blockers: [],
        contradictions: [],
        confidence: 0,
        confidence_scorecard: { data: 0, judgment: 0, commercial: 0 },
        feasibility: "",
      },
      confidence: decision.confidence ?? {
        data_quality: 0,
        judgment_confidence: 0,
        commercial_confidence: 0,
        overall: 0,
      },
      confidence_score: asNumber(decision.confidence_score, 0),
      risk_flags: asStringArray(decision.risk_flags),
      suitability_flags: Array.isArray(decision.suitability_flags)
        ? decision.suitability_flags
        : [],
      suitability_profile: decision.suitability_profile ?? null,
      commercial_decision: asString(decision.commercial_decision, "NONE"),
      intent_scores: asRecord(decision.intent_scores),
      next_best_action: decision.next_best_action ?? null,
      budget_breakdown: decision.budget_breakdown ?? DEFAULT_BUDGET_BREAKDOWN,
    } as unknown) as Trip["decision"],
    strategy: (trip.strategy as StrategyOutput | undefined) ?? undefined,
    traveler_bundle: (trip.traveler_bundle as PromptBundle | undefined) ?? undefined,
    internal_bundle: (trip.internal_bundle as PromptBundle | undefined) ?? undefined,
    safety: trip.safety || {},
    fees: (trip.fees as FeeCalculationResult | undefined) ?? undefined,
    frontier_result: trip.frontier_result ?? undefined,
    agentOperations: extractAgentOperations(trip),
    rawInput: trip.raw_input || {
      stage: "discovery",
      operating_mode: "normal_intake",
      fixture_id: null,
      execution_ms: 0,
    },
    tripPriorities: asString(
      firstPresent(
        getNestedValue(spineTrip, "trip_priorities", undefined),
        getNestedValue(spineTrip, "extracted.facts.trip_priorities.value", undefined)
      ),
      ""
    ) || undefined,
    dateFlexibility: asString(
      firstPresent(
        getNestedValue(spineTrip, "date_flexibility", undefined),
        getNestedValue(spineTrip, "extracted.facts.date_flexibility.value", undefined)
      ),
      ""
    ) || undefined,
    customerMessage: asString(getNestedValue(spineTrip, "customerMessage", ""), "") || undefined,
    agentNotes: asString(getNestedValue(spineTrip, "agentNotes", ""), "") || undefined,
  };
}

export function transformSpineTripsResponseToTrips(
  spineApiData: unknown,
  now: Date = new Date()
): Trip[] {
  const items = getNestedValue<unknown>(spineApiData, "items", undefined);
  if (Array.isArray(items)) {
    return items.map((item: unknown) => transformSpineTripToTrip(item, now));
  }
  if (Array.isArray(spineApiData)) {
    return spineApiData.map((item) => transformSpineTripToTrip(item, now));
  }
  return [transformSpineTripToTrip(spineApiData, now)];
}

export function transformSpineTripToInboxTrip(
  spineTrip: unknown,
  now: Date = new Date()
): InboxTrip {
  const source = asRecord(spineTrip);
  const trip = transformSpineTripToTrip(source, now);
  const status = asString(source.status, "new");
  const stage = STATUS_TO_INBOX_STAGE[status] || status || "options";
  const daysInCurrentStage = computeDaysInCurrentStage(source, now);
  const slaStatus = computeSlaStatus(daysInCurrentStage);
  const validation = asRecord(source.validation);
  const decision = asRecord(source.decision);
  const analytics = asRecord(source.analytics);
  const confidence = asNumber(decision.confidence_score, 0);

  let priority: TripPriority = "medium";
  let priorityScore = 50;
  if (
    slaStatus === "at_risk" ||
    analytics.requires_review ||
    validation.is_valid === false ||
    confidence < 0.5
  ) {
    priority = "high";
    priorityScore = 75;
  }
  if (slaStatus === "breached" || analytics.escalation_severity === "critical") {
    priority = "critical";
    priorityScore = 90;
  }

  // Urgency: time-pressure signal driven by SLA status
  let urgency = 50;
  if (slaStatus === "breached") urgency = 90;
  else if (slaStatus === "at_risk") urgency = 70;
  else if (daysInCurrentStage > 7) urgency = 60;

  // Importance: value/priority signal
  let importance = 50;
  if (priority === "critical") importance = 90;
  else if (priority === "high") importance = 70;
  if (budgetValue(source) > 100000) importance = Math.min(importance + 10, 100);

  return {
    id: trip.id,
    reference: deriveInboxReference(source, trip.id),
    destination: trip.destination,
    tripType: trip.type,
    partySize: trip.party ?? 1,
    dateWindow: trip.dateWindow ?? "TBD",
    value: budgetValue(source),
    priority,
    priorityScore,
    urgency,
    importance,
    stage,
    stageNumber: STAGE_NUMBERS[stage] || 0,
    assignedTo: asString(firstPresent(source.assignedTo, source.assigned_to), "") || undefined,
    assignedToName: asString(firstPresent(source.assignedToName, source.assigned_to_name), "") || undefined,
    submittedAt: asString(firstPresent(source.createdAt, source.created_at), now.toISOString()),
    lastUpdated: asString(
      firstPresent(source.updated_at, source.updatedAt, source.createdAt, source.created_at),
      now.toISOString()
    ),
    daysInCurrentStage,
    slaStatus,
    customerName: extractCustomerName(trip),
    flags: extractFlags(trip, source),
  };
}

export function transformSpineTripsResponseToInboxTrips(
  spineApiData: unknown,
  now: Date = new Date()
): InboxTrip[] {
  const items = getNestedValue(spineApiData, "items", []);
  return Array.isArray(items)
    ? items
        .flatMap((item) => isInboxTrip(transformSpineTripToTrip(item, now)) ? [transformSpineTripToInboxTrip(item, now)] : [])
    : [];
}
