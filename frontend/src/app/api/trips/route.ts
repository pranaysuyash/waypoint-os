import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import {
  transformSpineTripsResponseToTrips,
  WORKSPACE_STATES,
} from "@/lib/bff-trip-adapters";
import type { Trip } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const view = searchParams.get("view");

    // Strip our custom param before forwarding to spine_api
    const forwardParams = new URLSearchParams(searchParams.toString());
    forwardParams.delete("view");
    const query = forwardParams.toString();
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/trips${query ? `?${query}` : ""}`;

    const response = await fetch(spineApiUrl, bffFetchOptions(request, "GET"));

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    let transformedItems = transformSpineTripsResponseToTrips(spineApiData);

    // Server-side view filter — canonical definitions live here
    if (view === "workspace") {
      transformedItems = transformedItems.filter(
        (trip: Trip) => WORKSPACE_STATES.has(trip.state)
      );
    }

    return bffJson({
      items: transformedItems,
      total: transformedItems.length,
    });
  } catch (error) {
    console.error("Error fetching trips from spine_api:", error);
    return bffJson({ error: "Failed to fetch trips" }, 500);
  }
}
