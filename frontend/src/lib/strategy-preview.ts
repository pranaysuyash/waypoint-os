import type { Trip } from "@/lib/api-client";
import { formatBudgetDisplay } from "@/lib/lead-display";
import { getPlanningBriefStatus, getRequiredPlanningFields, getRecommendedPlanningFields } from "@/lib/planning-status";
import type { StrategyOutput } from "@/types/spine";

function formatFieldList(fields: string[]): string {
  return fields.length > 0 ? fields.join(", ") : "the trip details";
}

function prettyPlanningFieldLabel(field: string): string {
  const normalized = field.trim().toLowerCase();
  if (normalized === "trip priorities / must-haves") return "priorities or must-haves";
  if (normalized === "date flexibility") return "date flexibility";
  if (normalized === "budget range") return "budget";
  if (normalized === "travel window") return "travel window";
  if (normalized === "origin city") return "origin";
  if (normalized === "traveler count") return "group size";
  return normalized;
}

function formatPrettyFieldList(fields: string[]): string {
  const pretty = fields.map(prettyPlanningFieldLabel);
  return formatFieldList(pretty);
}

function cleanTripText(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (/^(tbd|unknown|n\/a|-)+$/i.test(trimmed)) return null;
  return trimmed;
}

function isGenericStoredStrategy(strategy: NonNullable<Trip["strategy"]> | null | undefined): boolean {
  if (!strategy) return false;
  return strategy.session_goal?.trim() === "Generate internal trip draft with documented assumptions for agent review.";
}

function isReadyToBuildOptions(trip: Trip): boolean {
  const highestReadyTier = trip.validation?.readiness?.highest_ready_tier;
  return highestReadyTier === "quote_ready" || highestReadyTier === "proposal_ready" || highestReadyTier === "booking_ready";
}

function isStaleEscalationStrategy(strategy: NonNullable<Trip["strategy"]> | null | undefined, trip: Trip): boolean {
  if (!strategy) return false;
  if (strategy.next_action !== "STOP_NEEDS_REVIEW") return false;
  return isReadyToBuildOptions(trip);
}

function isStaleInternalDraftStrategy(strategy: NonNullable<Trip["strategy"]> | null | undefined, trip: Trip): boolean {
  if (!strategy) return false;
  if (strategy.next_action !== "PROCEED_INTERNAL_DRAFT") return false;
  if (!isReadyToBuildOptions(trip)) return false;

  const goal = strategy.session_goal?.toLowerCase() ?? "";
  const opening = strategy.suggested_opening?.toLowerCase() ?? "";
  return goal.includes("internal") || goal.includes("draft") || opening.includes("internal draft");
}

export function buildTripStrategyPreview(trip?: Trip | null): StrategyOutput | null {
  if (!trip) return null;

  if (
    trip.strategy &&
    !isGenericStoredStrategy(trip.strategy) &&
    !isStaleEscalationStrategy(trip.strategy, trip) &&
    !isStaleInternalDraftStrategy(trip.strategy, trip)
  ) {
    return trip.strategy as StrategyOutput;
  }

  const briefStatus = getPlanningBriefStatus(trip);
  const requiredFields = getRequiredPlanningFields(trip);
  const recommendedFields = getRecommendedPlanningFields(trip);
  const destination = cleanTripText(trip.destination) || "this trip";
  const origin = cleanTripText(trip.origin);
  const budget = formatBudgetDisplay(trip.budget) || "the stated budget";
  const priorities = cleanTripText(trip.tripPriorities) || "trip priorities";
  const purpose = cleanTripText(trip.tripPurpose)?.toLowerCase() || null;
  const isCorporate = Boolean(
    purpose && /(business|corporate|conference|meeting|procurement|offsite|work)/.test(purpose)
  );
  const tripDescriptor = isCorporate ? "business trip" : "trip";
  const openingSuffix = isCorporate ? "with the business requirements in view" : "";

  if (briefStatus === "missing_required_details") {
    return {
      session_goal: `Confirm ${formatPrettyFieldList(requiredFields)} so the planner can build a real option set for ${destination}.`,
      priority_sequence: requiredFields.map((field) => `Confirm ${prettyPlanningFieldLabel(field)}`).slice(0, 5),
      tonal_guardrails: [
        "Stay concise and operator-friendly",
        "Use plain customer language",
        "Do not mention internal blockers unless necessary",
      ],
      risk_flags: requiredFields.map((field) => `Missing ${field.toLowerCase()}`),
      suggested_opening: `Let’s confirm ${requiredFields[0]?.toLowerCase() || "the next detail"} before building options.`,
      exit_criteria: [
        "All required trip details are captured",
        "The planner can build a credible first option set",
        "Operator has enough context to proceed",
      ],
      next_action: "ASK_FOLLOWUP",
      assumptions: [],
      suggested_tone: "direct",
    };
  }

  return {
    session_goal: isCorporate
      ? `Prepare a clear options plan for ${destination} for the ${tripDescriptor} while keeping ${budget} aligned.`
      : `Prepare a clear options plan for ${destination} while keeping ${priorities} and ${budget} aligned.`,
    priority_sequence: [
      origin ? `Check ${origin} and ${destination} together` : `Check the trip details around ${destination}`,
      isCorporate ? "Preserve the corporate/group shape" : `Shape options around ${priorities}`,
      `Keep the budget anchored to ${budget}`,
    ].concat(recommendedFields.length > 0 ? [`Tighten ${formatPrettyFieldList(recommendedFields)}`] : []).slice(0, 5),
    tonal_guardrails: [
      "Keep the options concise and decision-friendly",
      "Balance clarity with speed",
      "Call out assumptions only when they matter",
    ],
    risk_flags: recommendedFields.length > 0
      ? [`Recommended details missing: ${formatPrettyFieldList(recommendedFields)}`]
      : [],
    suggested_opening: isCorporate
      ? `Here’s the options plan for ${destination} ${openingSuffix}.`
      : `Here’s the options plan for ${destination}.`,
    exit_criteria: [
      "Options are structured and easy to compare",
      "Budget and pacing are visible",
      "The next operator step is clear",
    ],
    next_action: "PROCEED_INTERNAL_DRAFT",
    assumptions: recommendedFields.length > 0
      ? [isCorporate
        ? `Assuming ${formatPrettyFieldList(recommendedFields)} can be refined during business option building`
        : `Assuming ${formatPrettyFieldList(recommendedFields)} can be refined during option building`]
      : [],
    suggested_tone: "professional",
  };
}
