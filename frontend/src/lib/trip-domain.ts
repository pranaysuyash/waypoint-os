export const WORKSPACE_TRIP_STATUS_LIST = [
  "assigned",
  "in_progress",
  "ready_to_quote",
  "ready_to_book",
  "blocked",
] as const;

export const WORKSPACE_TRIP_STATUSES = WORKSPACE_TRIP_STATUS_LIST.join(",");
