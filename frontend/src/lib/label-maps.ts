export const FIELD_LABELS: Record<string, string> = {
  destination_candidates: "Destinations",
  origin_city: "Origin City",
  date_window: "Travel Dates",
  date_start: "Start Date",
  date_end: "End Date",
  flight_hotel_mismatch: "Flight / Hotel Mismatch",
  budget_raw_text: "Budget",
  budget_currency: "Budget Currency",
  budget_scope: "Budget Scope",
  budget_flexibility: "Budget Flexibility",
  party_size: "Party Size",
  party_composition: "Party Composition",
  lead_source: "Lead Source",
  activity_provenance: "Activity Interests",
  date_year_confidence: "Date Confidence",
  trip_purpose: "Trip Purpose",
  pace_preference: "Pace",
  hard_constraints: "Constraints",
  special_requirements: "Special Requirements",
  accommodation_preference: "Accommodation",
  transport_preference: "Transport",
  dietary_requirements: "Dietary Needs",
  visa_status: "Visa Status",
  child_ages: "Children's Ages",
  trip_type_inferred: "Trip Type",
  budget_tier: "Budget Tier",
  travel_style: "Travel Style",
  group_composition: "Group Composition",
  season: "Season",
  duration_category: "Duration",
  flexibility: "Flexibility",
  risk_tolerance: "Risk Tolerance",
};

export const SIGNAL_LABELS: Record<string, string> = {
  trip_type_inferred: "Trip Type",
  budget_tier: "Budget Tier",
  pace_preference: "Pace",
  travel_style: "Travel Style",
  group_composition: "Group Composition",
  season: "Season",
  duration_category: "Duration",
  flexibility: "Flexibility",
  risk_tolerance: "Risk Tolerance",
};

export const AMBIGUITY_TYPE_LABELS: Record<string, string> = {
  vague_range: "Vague Range",
  conflicting: "Conflicting Info",
  ambiguous: "Ambiguous",
  partial: "Partial",
  inferred: "Inferred",
  unconfirmed: "Unconfirmed",
};

export const STAGE_LABELS: Record<string, string> = {
  intake: "Intake",
  packet: "Trip Details",
  validation: "Validation",
  decision: "Quote Assessment",
  strategy: "Options",
  safety: "Risk Review",
  output: "Output",
  blocked_result: "Blocked",
};

export const DECISION_STATE_LABELS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE: "Ready to Book",
  PROCEED_INTERNAL_DRAFT: "Draft Quote",
  BRANCH_OPTIONS: "Needs Options",
  STOP_NEEDS_REVIEW: "Needs Attention",
  STOP_REVIEW: "Needs Attention",
  ASK_FOLLOWUP: "Waiting on Customer",
};

export const REVIEW_STATUS_LABELS: Record<string, string> = {
  pending: "Pending Review",
  approved: "Approved",
  rejected: "Declined",
  escalated: "Escalated",
  revision_needed: "Changes Requested",
};

export const SUITABILITY_STATUS_LABELS: Record<string, string> = {
  suitable: "Suitable",
  caution: "Needs Review",
  unsuitable: "Not Suitable",
};

export const STATUS_LABELS: Record<string, string> = {
  in_progress: "In Progress",
  completed: "Completed",
  pending: "Pending",
  unknown: "Unclassified Event",
  failed: "Failed",
  blocked: "Blocked",
  skipped: "Skipped",
};

export const FLAG_LABELS: Record<string, string> = {
  age_too_young: "Age Too Young",
  age_too_old: "Age Too Old",
  weight_exceeds_limit: "Weight Exceeds Limit",
  toddler_water_unsafe: "Water Activity Not Safe for Toddlers",
  toddler_height_unsafe: "Height Restriction Excludes Toddlers",
  toddler_late_night: "Late Night Not Suitable for Toddlers",
  elderly_intense: "Physical Intensity Unsafe for Elderly",
  elderly_extreme: "Extreme Intensity Not Suitable for Elderly",
  elderly_walking_heavy: "Walking-Heavy Activity Unsuitable",
  elderly_stairs_heavy: "Stairs Unsafe for Elderly Travelers",
  elderly_water_challenges: "Water Activity Challenges for Elderly",
  elderly_height_unsuitable: "Height Activity Not Suitable for Elderly",
  elderly_mobility_risk: "Mobility Risk for Elderly Travelers",
  budget_luxury_mismatch: "Luxury Activity Exceeds Budget",
  toddler_pacing: "Too Many Activities for Toddler",
  elderly_overload: "Physical Overload in Itinerary",
  itinerary_coherence: "Itinerary Pacing Concern",
};

export function titleCase(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

export function labelOrTitle(mapping: Record<string, string>, key: string, fallback?: string): string {
  return mapping[key] || fallback || titleCase(key);
}

export const BLOCKER_LABELS: Record<string, string> = {
  extraction_quality: "Required trip details are still incomplete",
  budget_unknown: "Budget range needs confirmation",
  date_window_missing: "Travel window needs confirmation",
  destination_ambiguous: "Destination choice needs confirmation",
  policy_violation: "Requires owner policy review",
  suitability_critical: "Traveler suitability concern requires acknowledgment",
};

export function formatBlockerLabel(code: string): string {
  const normalized = code.trim().toLowerCase();
  return BLOCKER_LABELS[normalized] || titleCase(code);
}

export const AUTHORITY_LABELS: Record<string, string> = {
  explicit_user: "Client stated",
  derived_signal: "System inferred",
  operator_override: "Operator confirmed",
  system_default: "System default",
  repeat_memory: "Traveler memory",
};

export function formatPacketAuthority(authority?: string | null): string {
  if (!authority) return "-";
  return AUTHORITY_LABELS[authority] || titleCase(authority);
}

const PACKET_ENUM_LABELS: Record<string, string> = {
  semi_open: "Semi-open",
  open_market: "Open market",
  nothing_booked: "Nothing booked yet",
  partially_booked: "Partially booked",
  fully_booked: "Fully booked",
  flexible: "Flexible",
  soft: "Flexible",
  hard: "Fixed",
  strict: "Fixed",
  total: "Total trip",
  per_person: "Per person",
  international: "International",
  domestic: "Domestic",
};

export function formatPacketValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (Array.isArray(value)) return value.map((item) => formatPacketValue(item)).join(", ");
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>).filter(
      ([, v]) => v !== null && v !== undefined && v !== "",
    );
    if (entries.length === 0) return "-";
    return entries
      .map(([k, v]) => `${String(v)} ${k.replace(/_/g, " ")}`)
      .join(", ");
  }
  const str = String(value);
  return PACKET_ENUM_LABELS[str] ?? str;
}
