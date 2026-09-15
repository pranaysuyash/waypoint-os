export const WORKSPACE_TRIP_STATUS_LIST = [
  "assigned",
  "in_progress",
  "ready_to_quote",
  "ready_to_book",
  "blocked",
  // Canonical in_trip alias (audit-gated; spine_api/core/trip_lifecycle.py):
  // in-flight trips must appear in the workspace view, not vanish (FND-0120).
  "active",
] as const;

export const WORKSPACE_TRIP_STATUSES = WORKSPACE_TRIP_STATUS_LIST.join(",");
