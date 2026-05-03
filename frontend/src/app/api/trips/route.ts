import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import {
  transformSpineTripsResponseToTrips,
  isWorkspaceTrip,
} from "@/lib/bff-trip-adapters";
import type { SpineRunRequest } from "@/types/generated/spine-api";

// Kill switch for call capture feature
// Set DISABLE_CALL_CAPTURE=true to disable POST /api/trips
// Read at call time (not module level) so env changes are picked up at runtime

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
      transformedItems = transformedItems.filter(isWorkspaceTrip);
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

export async function POST(req: NextRequest) {
  // Read at call time so tests can set process.env.DISABLE_CALL_CAPTURE after import
  if (process.env.DISABLE_CALL_CAPTURE === "true") {
    return bffJson(
      { error: "Call capture feature is temporarily disabled" },
      503  // Service Unavailable
    );
  }

  try {
    const body = await req.json();

    // Validate required field
    if (!body.raw_note) {
      return bffJson({ error: "raw_note required" }, 400);
    }

    const spinRequest: SpineRunRequest = {
      raw_note: body.raw_note,
      owner_note: body.owner_note ?? "",
      structured_json: body.structured_json ?? null,
      itinerary_text: body.itinerary_text ?? null,
      stage: body.stage ?? "discovery",
      operating_mode: body.operating_mode ?? "normal_intake",
      strict_leakage: body.strict_leakage ?? false,
      scenario_id: body.scenario_id ?? null,
      follow_up_due_date: body.follow_up_due_date ?? undefined,
      pace_preference: body.pace_preference ?? undefined,
      lead_source: body.lead_source ?? undefined,
      activity_provenance: body.activity_provenance ?? undefined,
      date_year_confidence: body.date_year_confidence ?? undefined,
    };

    // Forward to spine API /run endpoint (async pipeline execution)
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/run`;
    const response = await fetch(
      spineApiUrl,
      bffFetchOptions(req, "POST", undefined, { "Content-Type": "application/json" }, spinRequest),
    );

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      console.error(`Spine API returned ${response.status}`);
      return bffJson({ error: "Failed to submit trip for processing" }, 502);
    }

    const result = await response.json();
    // Returns { run_id, state: "queued" } — frontend polls /api/runs/{run_id}
    return bffJson(result, 202);
  } catch (error) {
    console.error("Error creating trip:", error);
    return bffJson({ error: "Failed to create trip" }, 500);
  }
}
