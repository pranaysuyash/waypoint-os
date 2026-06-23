import type { Trip } from "@/lib/api-client";
import { getPlanningHeaderTitle, getPlanningRecencyLabel } from "@/lib/planning-status";

function formatTripPickerReference(value: string): string {
  const normalized = value.trim().replace(/^trip_/i, "");
  const tail = normalized.split("_").pop()?.trim() || normalized;
  return tail.slice(0, 4).toUpperCase() || tail;
}

export function formatTripPickerLabel(trip: Trip): string {
  const title = getPlanningHeaderTitle(trip);
  const recency = getPlanningRecencyLabel(trip.age);
  const ref = formatTripPickerReference(trip.id);

  return [title, recency, ref].filter(Boolean).join(" · ");
}
