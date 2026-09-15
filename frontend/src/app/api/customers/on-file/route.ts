import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

/**
 * BFF proxy for E-D slot 2 (on-file traveler memory, display-only):
 * forwards the authenticated agency request to the backend's
 * hydrate-trip endpoint, which returns labeled on-file facts
 * ("source: memory", "observed_at") — never trip-packet data.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const tripId = typeof body?.tripId === "string" ? body.tripId : "";
    if (!tripId) {
      return bffJson({ error: "tripId is required" }, 400);
    }

    const spineApiUrl = spineUrl(`/api/v1/customers/hydrate-trip/${encodeURIComponent(tripId)}`);
    const base = bffFetchOptions(request, "POST");
    const response = await fetch(spineApiUrl, {
      ...base,
      headers: {
        ...base.headers,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ trip_id: tripId }),
      cache: "no-store",
    });

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return bffJson(data);
  } catch (error) {
    console.error("Error fetching on-file memory from spine_api:", error);
    return bffJson({ error: "Failed to fetch on-file memory" }, 500);
  }
}
