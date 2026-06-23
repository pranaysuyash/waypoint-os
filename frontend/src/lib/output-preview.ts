import type { Trip } from "@/lib/api-client";
import type { DecisionOutput, PromptBundle, StrategyOutput } from "@/types/spine";
import { buildTripStrategyPreview } from "@/lib/strategy-preview";

interface OutputPreviewResult {
  internalBundle: PromptBundle | null;
  travelerBundle: PromptBundle | null;
  isDerived: boolean;
}

function cleanText(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function isGenericInternalOpening(value: string | null | undefined): boolean {
  if (!value) return false;
  const normalized = value.toLowerCase();
  return normalized.includes("internal draft") || normalized.includes("agent review");
}

function deriveSafeOpening(
  strategy: StrategyOutput | null | undefined,
  decision: DecisionOutput | null | undefined,
  destination: string,
): string {
  const rawOpening = cleanText(strategy?.suggested_opening);
  const hasGenericInternalOpening = isGenericInternalOpening(rawOpening);

  if (!hasGenericInternalOpening && rawOpening) {
    return rawOpening;
  }

  if (decision?.decision_state === "ASK_FOLLOWUP") {
    return `I just need to confirm a couple of details before I can finalize the options for ${destination}.`;
  }

  if (decision?.decision_state === "BRANCH_OPTIONS") {
    return `Here are the options to compare for ${destination}.`;
  }

  if (decision?.decision_state === "STOP_NEEDS_REVIEW") {
    return `This trip needs a quick review before I can send a final customer-ready draft for ${destination}.`;
  }

  return `Here’s the options plan for ${destination}.`;
}

function normalizeFollowUpQuestions(
  questions: DecisionOutput["follow_up_questions"] | null | undefined,
): PromptBundle["follow_up_sequence"] {
  return (questions ?? [])
    .slice()
    .filter((question) => Boolean(question && typeof question === "object"))
    .map((question, index) => {
      const record = question as Record<string, unknown>;
      return {
        field_name: typeof record.field_name === "string" ? record.field_name : `follow_up_${index + 1}`,
        question: typeof record.question === "string" ? record.question : "",
        priority: typeof record.priority === "string" ? record.priority : "normal",
        suggested_values: Array.isArray(record.suggested_values) ? record.suggested_values : [],
      };
    })
    .filter((question) => question.question.length > 0);
}

function sortQuestionsByPriority(
  questions: DecisionOutput["follow_up_questions"] | null | undefined,
): DecisionOutput["follow_up_questions"] {
  const priorityRank: Record<string, number> = {
    critical: 0,
    high: 1,
    normal: 2,
    medium: 2,
    low: 3,
  };

  return [...(questions ?? [])].sort((left, right) => {
    const leftPriority = typeof left.priority === "string" ? left.priority.toLowerCase() : "normal";
    const rightPriority = typeof right.priority === "string" ? right.priority.toLowerCase() : "normal";
    return (priorityRank[leftPriority] ?? 4) - (priorityRank[rightPriority] ?? 4);
  });
}

function buildTravelerMessage(
  strategy: StrategyOutput | null | undefined,
  decision: DecisionOutput | null | undefined,
  destination: string,
): string {
  const opening = deriveSafeOpening(strategy, decision, destination);
  const messageParts = [opening];

  if (decision?.decision_state === "ASK_FOLLOWUP" && (decision.follow_up_questions ?? []).length > 0) {
    for (const question of sortQuestionsByPriority(decision.follow_up_questions).slice(0, 3)) {
      const priority = typeof question.priority === "string" ? question.priority.toLowerCase() : "normal";
      if (priority === "critical" || priority === "high") {
        const qText = cleanText(question.question);
        if (qText) messageParts.push(qText);
      }
    }
  } else if (decision?.decision_state === "PROCEED_TRAVELER_SAFE") {
    if (decision.operating_mode === "audit") {
      messageParts.push("Here’s my review comparing your plan with current market options.");
    } else if (decision.operating_mode === "coordinator_group") {
      messageParts.push("Options organized by group follow, plus a group summary.");
    }
  } else if (decision?.decision_state === "BRANCH_OPTIONS") {
    messageParts.push("Here are the options to compare side by side.");
  } else if (decision?.decision_state === "STOP_NEEDS_REVIEW") {
    messageParts.push("This case needs review before a customer-ready draft can be sent.");
  }

  return messageParts.join("\n");
}

function buildInternalMessage(
  strategy: StrategyOutput | null | undefined,
  decision: DecisionOutput | null | undefined,
): string {
  const opening = deriveSafeOpening(strategy, decision, "the trip");
  const parts = [opening];

  if (decision?.decision_state === "ASK_FOLLOWUP" && (decision.follow_up_questions ?? []).length > 0) {
    for (const question of sortQuestionsByPriority(decision.follow_up_questions).slice(0, 5)) {
      const field = cleanText((question as Record<string, unknown>).field_name) || "unknown_field";
      const questionText = cleanText((question as Record<string, unknown>).question) || "";
      const priority = cleanText((question as Record<string, unknown>).priority) || "normal";
      const suggested = Array.isArray((question as Record<string, unknown>).suggested_values)
        ? (question as Record<string, unknown>).suggested_values as unknown[]
        : [];
      if (questionText) {
        if (suggested.length > 0) {
          parts.push(`[${priority.toUpperCase()}] ${field}: ${questionText} (Suggested: ${suggested.map((value) => String(value)).join(", ")})`);
        } else {
          parts.push(`[${priority.toUpperCase()}] ${field}: ${questionText}`);
        }
      }
    }
  }

  return parts.join("\n");
}

export function buildTripOutputPreview(trip?: Trip | null): OutputPreviewResult {
  if (!trip) {
    return { internalBundle: null, travelerBundle: null, isDerived: false };
  }

  const strategy = (trip.strategy as StrategyOutput | null | undefined) ?? null;
  const decision = (trip.decision as DecisionOutput | null | undefined) ?? null;
  const strategyPreview = buildTripStrategyPreview(trip);

  if (!strategy && !decision) {
    return { internalBundle: null, travelerBundle: null, isDerived: false };
  }

  const destination = cleanText(trip.destination) || "the trip";
  const suggestedOpening = deriveSafeOpening(strategyPreview ?? strategy, decision, destination);
  const travelerFollowUpSequence = normalizeFollowUpQuestions(decision?.follow_up_questions);
  const travelerBundle: PromptBundle = {
    system_context: `Session Goal: ${cleanText(strategyPreview?.session_goal) || cleanText(strategy?.session_goal) || `Prepare a customer-ready draft for ${destination}.`}`,
    user_message: buildTravelerMessage({ ...strategy, suggested_opening: suggestedOpening } as StrategyOutput, decision, destination),
    follow_up_sequence: travelerFollowUpSequence,
    branch_prompts: [],
    internal_notes: "",
    constraints: [
      "NEVER mention internal concepts: hypotheses, contradictions, blockers, ambiguities",
      "NEVER reveal internal decision states or confidence scores",
      "DO NOT share owner-only constraints or internal notes",
      "Frame all questions as natural conversation, not as 'data collection'",
    ],
    audience: "traveler",
  };

  const internalBundle: PromptBundle = {
    system_context: [
      "INTERNAL OUTPUT PREVIEW (DERIVED)",
      `Decision State: ${decision?.decision_state || "unknown"}`,
      `Destination: ${destination}`,
    ].join("\n"),
    user_message: buildInternalMessage({ ...strategy, suggested_opening: suggestedOpening } as StrategyOutput, decision),
    follow_up_sequence: travelerFollowUpSequence,
    branch_prompts: [],
    internal_notes: "Derived preview from persisted trip strategy and decision because the generated bundle is not stored yet.",
    constraints: [
      "Include all internal context in notes",
      "Document assumptions explicitly",
      "Flag any new contradictions or ambiguities detected",
      "Maintain full audit trail",
    ],
    audience: "internal",
  };

  return {
    internalBundle,
    travelerBundle,
    isDerived: true,
  };
}
