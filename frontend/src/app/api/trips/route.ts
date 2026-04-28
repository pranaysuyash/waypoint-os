import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import {
  transformSpineTripsResponseToTrips,
  WORKSPACE_STATES,
} from "@/lib/bff-trip-adapters";
import type { Trip } from "@/lib/api-client";
import type { SpineRunRequest } from "@/types/generated/spine-api";

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

export async function POST(req: Request) {
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
    };

    // TODO: Call spine pipeline (reuse existing logic if available)
    // const result = await executeSpinePipeline(spinRequest);

    // Temporarily return mock for testing structure
    const trip: Trip = {
      id: crypto.randomUUID(),
      destination: "TBD",
      type: "unknown",
      state: "blue",
      age: "0",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      followUpDueDate: body.follow_up_due_date ?? undefined,
      status: "open",
      customerMessage: body.raw_note,
      agentNotes: body.owner_note,
    };

    return bffJson(trip, 201);
  } catch (error) {
    console.error("Error creating trip:", error);
    return bffJson({ error: "Failed to create trip" }, 500);
  }
}
