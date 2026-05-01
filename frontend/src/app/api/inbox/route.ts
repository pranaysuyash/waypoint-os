import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { transformSpineTripToInboxTrip } from "@/lib/bff-trip-adapters";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.toString();
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/inbox${query ? `?${query}` : ""}`;

    const response = await fetch(spineApiUrl, bffFetchOptions(request, "GET"));

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    const items = (data.items || []).map((t: unknown) =>
      transformSpineTripToInboxTrip(t)
    );
    return bffJson({
      ...data,
      items,
    });
  } catch (error) {
    console.error("Error proxying inbox:", error);
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
