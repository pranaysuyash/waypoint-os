import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import {
  transformSpineTripsResponseToTrips,
  isWorkspaceTrip,
} from "@/lib/bff-trip-adapters";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

const WORKSPACE_STATUSES = "assigned,in_progress,ready_to_quote,ready_to_book,blocked";

const PIPELINE_ORDER = [
  "assigned",
  "in_progress",
  "ready_to_quote",
  "ready_to_book",
  "blocked",
] as const;

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(
      `${SPINE_API_URL}/trips?status=${WORKSPACE_STATUSES}&limit=10000`,
      {
        ...bffFetchOptions(request, "GET"),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    const trips = transformSpineTripsResponseToTrips(spineApiData).filter(isWorkspaceTrip);

    const counts = new Map<string, number>();
    for (const trip of trips) {
      const label = trip.status || "in_progress";
      counts.set(label, (counts.get(label) ?? 0) + 1);
    }

    return bffJson(
      PIPELINE_ORDER.map((label) => ({
        label,
        count: counts.get(label) ?? 0,
      })),
    );
  } catch (error) {
    console.error("Error building operational pipeline:", error);
    return bffJson({ error: "Failed to fetch pipeline" }, 500);
  }
}
