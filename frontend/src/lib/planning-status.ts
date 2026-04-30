import type { Trip } from "@/lib/api-client";
import {
  formatBudgetDisplay,
  formatCustomerDisplay,
  formatDateWindowDisplay,
  formatInquiryReference,
  formatLeadTitle,
  formatPartySizeDisplay,
} from "@/lib/lead-display";

const CORE_DETAIL_SOFT_BLOCKERS = new Set(["incomplete_intake"]);
const BLOCKED_PLANNING_ALLOWED_STAGES = new Set(["intake", "packet", "timeline"]);

export type PlanningBriefStatus =
  | "complete"
  | "missing_required_details"
  | "missing_recommended_details";

export interface PlanningMissingDetail {
  label: string;
  requirement: "Required" | "Recommended";
}

function hasApproximateDateWindow(dateWindow?: string | null): boolean {
  const normalized = dateWindow?.trim().toLowerCase();
  if (!normalized) return false;
  return normalized.includes("around") || normalized.includes("approx") || normalized.includes("flex");
}

function isMissingDisplayValue(value?: string | null): boolean {
  const normalized = value?.trim().toLowerCase();
  if (!normalized) return true;
  return ["tbd", "to confirm", "unknown", "not set", "n/a", "na", "—", "-"].includes(normalized);
}

function hasValidationWarning(trip: Trip | null | undefined, fieldName: string): boolean {
  return Boolean(trip?.validation?.warnings?.some((warning) => warning.field === fieldName));
}

function readPlanningPriorityValue(trip?: Trip | null): string | null {
  const rawValue = trip?.activityProvenance?.trim();
  return rawValue && rawValue.toLowerCase() !== "none" ? rawValue : null;
}

function hasPlanningSoftBlocker(trip?: Trip | null): boolean {
  if (!trip) return false;
  const softBlockers = trip.decision?.soft_blockers ?? [];
  return softBlockers.some((blocker) => CORE_DETAIL_SOFT_BLOCKERS.has(blocker));
}

function needsOriginCity(trip?: Trip | null): boolean {
  if (!trip) return false;
  return hasValidationWarning(trip, "origin_city");
}

function formatPlanningFieldList(fields: string[]): string {
  const normalized = fields
    .map((field) => field.charAt(0).toLowerCase() + field.slice(1))
    .filter(Boolean);

  if (normalized.length === 0) return "required trip details";
  if (normalized.length === 1) return normalized[0]!;
  if (normalized.length === 2) return `${normalized[0]} and ${normalized[1]}`;
  return `${normalized.slice(0, -1).join(", ")}, and ${normalized.at(-1)}`;
}

export function getRequiredPlanningFields(trip?: Trip | null): string[] {
  if (!trip) return [];

  const requiredFields: string[] = [];

  if (formatBudgetDisplay(trip.budget) === "Budget missing" || hasValidationWarning(trip, "budget_raw_text")) {
    requiredFields.push("Budget range");
  }

  if (needsOriginCity(trip) && isMissingDisplayValue(trip.origin)) {
    requiredFields.push("Origin city");
  }

  if (isMissingDisplayValue(trip.destination)) {
    requiredFields.push("Destination");
  }

  if (!trip.dateWindow?.trim()) {
    requiredFields.push("Travel window");
  }

  if (!trip.party) {
    requiredFields.push("Traveler count");
  }

  return [...new Set(requiredFields)];
}

export function getRecommendedPlanningFields(trip?: Trip | null): string[] {
  if (!trip) return [];

  const recommendedFields: string[] = [];

  if (!readPlanningPriorityValue(trip)) {
    recommendedFields.push("Trip priorities / must-haves");
  }

  if (!trip.dateWindow?.trim() || hasApproximateDateWindow(trip.dateWindow)) {
    recommendedFields.push("Date flexibility");
  }

  return recommendedFields;
}

export function getPlanningBriefStatus(trip?: Trip | null): PlanningBriefStatus {
  if (!trip) return "complete";
  if (getRequiredPlanningFields(trip).length > 0) return "missing_required_details";
  if (getRecommendedPlanningFields(trip).length > 0 || hasPlanningSoftBlocker(trip)) {
    return "missing_recommended_details";
  }
  return "complete";
}

export function hasPlanningBriefBlocker(trip?: Trip | null): boolean {
  return getPlanningBriefStatus(trip) === "missing_required_details";
}

export function canAccessPlanningStage(
  trip: Trip | null | undefined,
  stage: string,
): boolean {
  if (!trip) return true;
  if (getPlanningBriefStatus(trip) !== "missing_required_details") return true;
  return BLOCKED_PLANNING_ALLOWED_STAGES.has(stage);
}

export function getPlanningStageGateReason(trip?: Trip | null, stage?: string): string | null {
  if (!trip || !stage || canAccessPlanningStage(trip, stage)) return null;
  const requiredFields = getRequiredPlanningFields(trip);
  return `Confirm ${formatPlanningFieldList(requiredFields)} first.`;
}

export function getPlanningStatusTone(trip?: Trip | null): Trip["state"] {
  if (!trip) return "blue";
  if (hasPlanningBriefBlocker(trip)) return "blue";
  return trip.state;
}

export function getPlanningStatusLabel(trip?: Trip | null): string {
  if (!trip) return "Need Trip Options";
  if (hasPlanningBriefBlocker(trip)) return "Need Customer Details";
  if (trip.state === "red") return "Needs Review";
  if (trip.status === "in_progress") return "In Progress";
  return "Need Trip Options";
}

export function getPlanningHeaderTitle(trip?: Trip | null): string {
  if (!trip) return "Trip planning";
  const simplifiedType = trip.type?.replace(/\bleisure\b/gi, "").replace(/\s+/g, " ").trim();
  return formatLeadTitle(trip.destination, simplifiedType || trip.type);
}

export function getPlanningIdentityLine(trip?: Trip | null): string {
  if (!trip) return "";

  return [
    formatCustomerDisplay(trip.rawInput),
    formatPartySizeDisplay(trip.party),
    formatDateWindowDisplay(trip.dateWindow),
  ].join(" · ");
}

export function getPlanningQueueLine(trip?: Trip | null): string {
  if (!trip?.id) return "In planning";
  return `In planning · Inquiry Ref: ${formatInquiryReference(trip.id)}`;
}

export function getPlanningRecencyLabel(age?: string | null): string {
  const normalized = age?.trim().toLowerCase();

  if (!normalized) return "Updated recently";
  if (normalized === "today") return "Updated today";
  if (normalized === "yesterday") return "Updated yesterday";

  return `Updated ${age}`;
}

export function getPlanningBlockerTitle(isLeadReview: boolean, trip?: Trip | null): string {
  if (isLeadReview) return "Missing before planning";
  if (hasPlanningBriefBlocker(trip)) return "Before building options";
  return "Missing before quote";
}

export function getPlanningBlockerBody(isLeadReview: boolean, trip?: Trip | null): string {
  if (isLeadReview) return "Budget and trip details need confirmation.";
  if (hasPlanningBriefBlocker(trip)) return "Confirm budget and any must-have trip details.";
  return "No blocking issues found yet. Some customer details may still need confirmation before quoting.";
}

export function getPlanningSuggestedNextMove(isLeadReview: boolean, trip?: Trip | null): string {
  if (isLeadReview) return "Review the lead and confirm missing details with the traveler.";
  if (hasPlanningBriefBlocker(trip)) return "Ask the traveler for budget range and trip priorities.";

  const decisionState = trip?.decision?.decision_state;

  switch (decisionState) {
    case "PROCEED_TRAVELER_SAFE":
      return "Send quote to traveler.";
    case "PROCEED_INTERNAL_DRAFT":
      return "Finalize internal draft before sending.";
    case "BRANCH_OPTIONS":
      return "Prepare multiple options for traveler.";
    case "STOP_NEEDS_REVIEW":
    case "STOP_REVIEW":
      return "Resolve blockers before proceeding.";
    case "ASK_FOLLOWUP":
      return "Follow up with traveler for more info.";
    default:
      return "Review assessment output.";
  }
}

export function getPlanningMissingDetails(trip?: Trip | null): PlanningMissingDetail[] {
  if (!trip) return [];

  return [
    ...getRequiredPlanningFields(trip).map((label) => ({ label, requirement: "Required" as const })),
    ...getRecommendedPlanningFields(trip).map((label) => ({ label, requirement: "Recommended" as const })),
  ];
}

export function getPlanningFollowUpDraft(trip?: Trip | null): string {
  const missingDetails = getPlanningMissingDetails(trip).map((detail) => detail.label.toLowerCase());
  const needsOriginCity = missingDetails.includes("origin city");
  const needsDateFlexibility = missingDetails.includes("date flexibility");

  const extraRequests = [
    needsOriginCity ? "your departure city" : null,
    needsDateFlexibility ? "how flexible your dates are" : null,
    "any must-have activities, hotel preferences, or trip priorities",
  ].filter(Boolean);

  return `Hi, to start planning properly, could you confirm your approximate budget range${needsOriginCity ? ", your departure city," : ""}${needsDateFlexibility ? ", how flexible your dates are," : ""} and ${extraRequests.at(-1)}?`;
}

export function getPlanningPrimaryActionLabel(trip?: Trip | null): string {
  const briefStatus = getPlanningBriefStatus(trip);
  if (briefStatus === "missing_required_details") return "Draft follow-up";
  if (briefStatus === "missing_recommended_details") return "Continue to options";
  return "Build trip options";
}

export function getPlanningNextAction(trip?: Trip | null): string {
  if (!trip) return "Next: review assessment output.";
  if (trip.state === "red" && !hasPlanningBriefBlocker(trip)) {
    return "Next: resolve review blockers and unblock the trip plan.";
  }
  if (getPlanningBriefStatus(trip) === "missing_required_details") {
    return "Next: confirm budget and trip details before building options.";
  }
  if (getPlanningBriefStatus(trip) === "missing_recommended_details") {
    return "Next: refine the brief or continue to options.";
  }
  return "Next: build package options.";
}

export function getPlanningSummaryText(label: string, total: number): string {
  const normalized = label.trim().toLowerCase().replace(/\s+/g, "_");

  switch (normalized) {
    case "assigned":
      return `${total} ${total === 1 ? "trip" : "trips"} in planning · planning started`;
    case "in_progress":
      return `${total} ${total === 1 ? "trip" : "trips"} in planning · actively being built`;
    case "ready_to_quote":
      return `${total} ${total === 1 ? "trip" : "trips"} in planning · ready for quote review`;
    case "ready_to_book":
      return `${total} ${total === 1 ? "trip" : "trips"} in planning · ready for booking`;
    case "blocked":
      return `${total} ${total === 1 ? "trip" : "trips"} in planning · needs attention`;
    default:
      return `${total} ${total === 1 ? "trip" : "trips"} in planning`;
  }
}
