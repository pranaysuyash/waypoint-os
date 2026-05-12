const UNKNOWN_FIELD_PROMPTS: Record<string, string> = {
  origin_city: "Which city will the travelers depart from?",
  date_window: "What are the exact travel dates or date range?",
  destination_candidates: "Which destination(s) is the traveler considering?",
  budget_raw_text: "What budget range should we plan within?",
  trip_purpose: "What is the purpose of this trip (family holiday, honeymoon, business, etc.)?",
  party_size: "How many travelers are going?",
};

const PLANNING_DETAIL_PROMPTS: Record<string, string> = {
  budget: UNKNOWN_FIELD_PROMPTS.budget_raw_text,
  dates: "What are your exact travel dates or preferred date range?",
  destination: "Which destination(s) are you considering?",
  origin: UNKNOWN_FIELD_PROMPTS.origin_city,
  priorities: "What are your must-haves for this trip (hotel style, pace, activities, room setup)?",
  flexibility: "How flexible are your dates if pricing or availability changes?",
  customerName: "What is the full name of the primary traveler or contact?",
};

export function getTravelerPromptForUnknownField(fieldName: string): string | null {
  return UNKNOWN_FIELD_PROMPTS[fieldName] ?? null;
}

export function getTravelerPromptForPlanningDetail(detailId: string): string | null {
  return PLANNING_DETAIL_PROMPTS[detailId] ?? null;
}

