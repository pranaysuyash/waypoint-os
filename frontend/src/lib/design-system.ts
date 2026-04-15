export const STATE_COLORS = {
  PROCEED_TRAVELER_SAFE: "state-green",
  PROCEED_INTERNAL_DRAFT: "state-amber",
  BRANCH_OPTIONS: "state-amber",
  STOP_NEEDS_REVIEW: "state-red",
  ASK_FOLLOWUP: "state-blue",
} as const;

export type StateColorKey = keyof typeof STATE_COLORS;