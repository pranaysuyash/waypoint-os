import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import {
  transformSpineTripsResponseToTrips,
  isWorkspaceTrip,
} from "@/lib/bff-trip-adapters";
import { WORKSPACE_TRIP_STATUS_LIST, WORKSPACE_TRIP_STATUSES } from "@/lib/trip-domain";
import { spineUrl } from "@/lib/proxy-core";

const PIPELINE_ORDER = WORKSPACE_TRIP_STATUS_LIST;

export async function GET(request: NextRequest) {
  try {
    const tripsUrl = spineUrl(`/trips?status=${WORKSPACE_TRIP_STATUSES}&limit=10000`);
    const response = await fetch(
      tripsUrl,
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
