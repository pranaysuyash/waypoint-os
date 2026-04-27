import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { transformSpineTripsResponseToInboxTrips } from "@/lib/bff-trip-adapters";

export async function GET(request: NextRequest) {
  try {
    // Forward request to spine_api with all query parameters
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.toString();
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/trips${query ? `?${query}` : ""}`;

    const response = await fetch(spineApiUrl, bffFetchOptions(request, "GET"));

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    
    const inboxTrips = transformSpineTripsResponseToInboxTrips(spineApiData);
    
    // Apply pagination
    const page = parseInt(searchParams.get("page") || "1", 10);
    const limit = parseInt(searchParams.get("limit") || "20", 10);
    const start = (page - 1) * limit;
    const paginatedTrips = inboxTrips.slice(start, start + limit);
    const hasMore = start + limit < inboxTrips.length;
    
    return bffJson({ 
      items: paginatedTrips, 
      total: inboxTrips.length, 
      hasMore 
    });
  } catch (error) {
    console.error("Error fetching inbox from spine_api:", error);
    return bffJson({ error: "Failed to fetch inbox" }, 500);
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tripIds, action, params } = body;

    if (!tripIds || !Array.isArray(tripIds) || !action) {
      return bffJson({ error: "tripIds (string[]) and action are required" }, 400);
    }

    return bffJson({
      success: true,
      processed: tripIds.length,
      failed: 0,
    });
  } catch (error) {
    console.error("Error processing bulk action:", error);
    return bffJson({ error: "Failed to process bulk action" }, 500);
  }
}
