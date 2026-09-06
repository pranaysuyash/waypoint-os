import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";

/**
 * BFF proxy for trip stats (F-40): forwards the authenticated request to the
 * spine backend's GET /stats. The frontend `useTripStats` hook calls
 * `/api/stats`; without this route the contract 404'd end to end.
 */
export async function GET(request: NextRequest) {
  try {
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/stats`;
    const response = await fetch(spineApiUrl, { ...bffFetchOptions(request, "GET"), cache: "no-store" });

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const stats = await response.json();
    return bffJson(stats);
  } catch (error) {
    console.error("Error fetching trip stats from spine_api:", error);
    return bffJson({ error: "Failed to fetch trip stats" }, 500);
  }
}
