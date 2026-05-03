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
  const canonical = trip?.tripPriorities?.trim();
  if (canonical && canonical.toLowerCase() !== "none") return canonical;
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

function formatPlanningFieldListTitleCase(fields: string[]): string {
  const normalized = fields
    .map((field) => field.trim())
    .filter(Boolean)
    .map((field) => field.charAt(0).toLowerCase() + field.slice(1));

  if (normalized.length === 0) return "required trip details";
  if (normalized.length === 1) return normalized[0]!;
  if (normalized.length === 2) return `${normalized[0]} and ${normalized[1]}`;
  return `${normalized.slice(0, -1).join(", ")}, and ${normalized.at(-1)}`;
}

export function getRequiredPlanningFields(trip?: Trip | null): string[] {
  if (!trip) return [];

  const requiredFields: string[] = [];

  if (formatBudgetDisplay(trip.budget) === "Budget missing") {
    requiredFields.push("Budget range");
  }

  if (needsOriginCity(trip) && isMissingDisplayValue(trip.origin)) {
    requiredFields.push("Origin city");
  }

  if (isMissingDisplayValue(trip.destination)) {
    requiredFields.push("Destination");
  }

  if (isMissingDisplayValue(trip.dateWindow)) {
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

  const hasDateFlex = trip?.dateFlexibility?.trim() && trip.dateFlexibility.trim().toLowerCase() !== "none";
  if (!hasDateFlex && (!trip?.dateWindow?.trim() || hasApproximateDateWindow(trip.dateWindow))) {
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

export function getPlanningLockedTabHint(trip?: Trip | null, stage?: string): string | null {
  if (!trip || !stage || canAccessPlanningStage(trip, stage)) return null;

  const requiredFields = getRequiredPlanningFields(trip);
  const normalized = requiredFields.map((field) => field.toLowerCase());

  if (normalized.length === 1 && normalized[0] === "budget range") {
    return "Budget needed";
  }

  if (normalized.length === 1 && normalized[0] === "origin city") {
    return "Origin needed";
  }

  if (normalized.length === 2 && normalized.includes("budget range") && normalized.includes("origin city")) {
    return "Budget + origin needed";
  }

  return "Complete customer details";
}

export function getPlanningUnlockHint(trip?: Trip | null): string | null {
  if (!trip || !hasPlanningBriefBlocker(trip)) return null;
  const requiredFields = getRequiredPlanningFields(trip);
  return `Complete ${formatPlanningFieldListTitleCase(requiredFields)} to unlock quote, options, output, and safety review.`;
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
  const cleanDestination = isMissingDisplayValue(trip.destination) ? null : trip.destination;
  const simplifiedType = trip.type?.replace(/\bleisure\b/gi, "").replace(/\s+/g, " ").trim();
  return formatLeadTitle(cleanDestination, simplifiedType || trip.type);
}

export function getPlanningIdentityLine(trip?: Trip | null): string {
  if (!trip) return "";

  return [
    formatCustomerDisplay(trip.rawInput),
    formatPartySizeDisplay(trip.party),
    formatDateWindowDisplay(trip.dateWindow),
  ]
    .filter(Boolean)
    .join(" · ");
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
  if (hasPlanningBriefBlocker(trip)) return "Missing customer details";
  return "Ready to build options";
}

export function getPlanningBlockerBody(isLeadReview: boolean, trip?: Trip | null): string {
  if (isLeadReview) return "Budget and trip details need confirmation.";
  if (hasPlanningBriefBlocker(trip)) {
    const requiredFields = getRequiredPlanningFields(trip);
    if (requiredFields.length === 0) return "Confirm any must-have trip details.";
    return `Confirm ${formatPlanningFieldList(requiredFields)} before building options.`;
  }
  return "Required trip details are complete.";
}

export function getPlanningSuggestedNextMove(isLeadReview: boolean, trip?: Trip | null): string {
  if (isLeadReview) return "Review the lead and confirm missing details with the traveler.";

  const requiredFields = getRequiredPlanningFields(trip);
  if (requiredFields.length > 0) {
    return `Ask the traveler for ${formatPlanningFieldList(requiredFields).toLowerCase()}.`;
  }

  const recommendedFields = getRecommendedPlanningFields(trip);
  if (recommendedFields.length > 0) {
    return "Add recommended details or continue to options.";
  }

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
  const missingDetails = getPlanningMissingDetails(trip);
  const requiredFields = missingDetails.filter((d) => d.requirement === "Required").map((d) => d.label.toLowerCase());
  const recommendedFields = missingDetails.filter((d) => d.requirement === "Recommended").map((d) => d.label.toLowerCase());

  const extraRequests: (string | null)[] = [];

  if (requiredFields.includes("budget range")) {
    extraRequests.push("your approximate budget range");
  }
  if (requiredFields.includes("origin city")) {
    extraRequests.push("your departure city");
  }
  if (requiredFields.includes("destination")) {
    extraRequests.push("your destination");
  }
  if (requiredFields.includes("travel window")) {
    extraRequests.push("your travel dates");
  }
  if (requiredFields.includes("traveler count")) {
    extraRequests.push("your party size");
  }
  if (recommendedFields.includes("trip priorities / must-haves")) {
    extraRequests.push("any must-have activities, hotel preferences, or trip priorities");
  }
  if (recommendedFields.includes("date flexibility")) {
    extraRequests.push("how flexible your dates are");
  }

  const allRequests = extraRequests.filter(Boolean);
  if (allRequests.length === 0) {
    return `Hi, I have what I need to start planning. I will move ahead with building options and share the next update shortly.`;
  }

  return `Hi, to start planning properly, could you confirm ${allRequests.join(", ")}?`;
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
    const requiredFields = getRequiredPlanningFields(trip);
    const normalized = requiredFields.map((field) => field.toLowerCase());

    if (normalized.length === 1 && normalized[0] === "budget range") {
      return "Next: confirm budget before building options.";
    }

    if (normalized.length === 1 && normalized[0] === "origin city") {
      return "Next: confirm origin before building options.";
    }

    if (normalized.length === 2 && normalized.includes("budget range") && normalized.includes("origin city")) {
      return "Next: confirm budget and origin before building options.";
    }

    return `Next: confirm ${formatPlanningFieldList(requiredFields)} before building options.`;
  }
  if (getPlanningBriefStatus(trip) === "missing_recommended_details") {
    return "Next: review recommended details before building options.";
  }
  return "Next: trip details are complete. Options builder is pending.";
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
