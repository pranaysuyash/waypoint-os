import type { Trip } from "@/lib/api-client";
import { getPlanningHeaderTitle, getPlanningRecencyLabel } from "@/lib/planning-status";

function formatTripPickerReference(value: string): string {
  const normalized = value.trim().replace(/^trip_/i, "");
  const parts = normalized.split("_").filter(Boolean);
  let candidate = parts[parts.length - 1] || normalized;
  if (candidate.length <= 2 && parts.length > 1) {
    candidate = parts.find((p) => p.length >= 4 && !/^\d+$/.test(p)) || parts.join("");
  }
  return candidate.slice(0, 4).toUpperCase() || candidate.toUpperCase();
}

export function formatTripPickerLabel(trip: Trip): string {
  const baseTitle = getPlanningHeaderTitle(trip);
  const strategyWithOption = trip.strategy as
    | (Trip["strategy"] & { recommended_option?: { name?: unknown } })
    | undefined;
  const strategyName =
    typeof strategyWithOption?.recommended_option?.name === "string"
      ? strategyWithOption.recommended_option.name.trim()
      : "";
  const title =
    baseTitle === "Trip details incomplete" && strategyName
      ? strategyName
      : baseTitle;
  const recency = getPlanningRecencyLabel(trip.age);
  const ref = formatTripPickerReference(trip.id);

  return [title, recency, ref].filter(Boolean).join(" · ");
}
