import type { Trip } from "@/lib/api-client";
import { getPlanningBriefStatus, getRequiredPlanningFields, getRecommendedPlanningFields } from "@/lib/planning-status";
import type { StrategyOutput } from "@/types/spine";

function formatFieldList(fields: string[]): string {
  return fields.length > 0 ? fields.join(", ") : "the trip details";
}

function cleanTripText(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (/^(tbd|unknown|n\/a|-)+$/i.test(trimmed)) return null;
  return trimmed;
}

export function buildTripStrategyPreview(trip?: Trip | null): StrategyOutput | null {
  if (!trip) return null;

  if (trip.strategy) {
    return trip.strategy as StrategyOutput;
  }

  const briefStatus = getPlanningBriefStatus(trip);
  const requiredFields = getRequiredPlanningFields(trip);
  const recommendedFields = getRecommendedPlanningFields(trip);
  const missingRequired = formatFieldList(requiredFields);
  const missingRecommended = formatFieldList(recommendedFields);
  const destination = cleanTripText(trip.destination) || "this trip";
  const origin = cleanTripText(trip.origin);
  const budget = cleanTripText(trip.budget) || "the stated budget";
  const priorities = cleanTripText(trip.tripPriorities) || "trip priorities";

  if (briefStatus === "missing_required_details") {
    return {
      session_goal: `Confirm ${missingRequired} so the planner can build a real option set for ${destination}.`,
      priority_sequence: requiredFields.map((field) => `Confirm ${field.toLowerCase()}`).slice(0, 5),
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
    session_goal: `Prepare a clear options plan for ${destination} while keeping ${priorities} and ${budget} aligned.`,
    priority_sequence: [
      origin ? `Check ${origin} and ${destination} together` : `Check the trip details around ${destination}`,
      `Shape options around ${priorities}`,
      `Keep the budget anchored to ${budget}`,
    ].concat(recommendedFields.length > 0 ? [`Tighten ${missingRecommended}`] : []).slice(0, 5),
    tonal_guardrails: [
      "Keep the options concise and decision-friendly",
      "Balance clarity with speed",
      "Call out assumptions only when they matter",
    ],
    risk_flags: recommendedFields.length > 0
      ? [`Recommended details missing: ${missingRecommended}`]
      : [],
    suggested_opening: `Here’s the options plan for ${destination}.`,
    exit_criteria: [
      "Options are structured and easy to compare",
      "Budget and pacing are visible",
      "The next operator step is clear",
    ],
    next_action: "PROCEED_INTERNAL_DRAFT",
    assumptions: recommendedFields.length > 0
      ? [`Assuming ${missingRecommended} can be refined during option building`]
      : [],
    suggested_tone: "professional",
  };
}
