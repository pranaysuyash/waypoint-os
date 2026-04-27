import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, validateOrigin, isAuthStatus } from "@/lib/bff-auth";
import { transformSpineTripToTrip } from "@/lib/bff-trip-adapters";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    
    const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    // Forward request to spine_api
    const spineApiUrl = `${SPINE_API_URL}/trips/${encodeURIComponent(id)}`;

    const response = await fetch(spineApiUrl, bffFetchOptions(request, "GET"));

    if (!response.ok) {
      if (response.status === 404) {
        return bffJson({ error: "Trip not found" }, 404);
      }
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    const transformedTrip = transformSpineTripToTrip(spineApiData);
    
    return bffJson(transformedTrip);
  } catch (error) {
    console.error("Error fetching trip from spine_api:", error);
    return bffJson({ error: "Failed to fetch trip" }, 500);
  }
}

const PATCHABLE_FIELDS = new Set([
  "customerMessage",
  "agentNotes",
  "budget",
  "party",
  "dateWindow",
  "origin",
  "destination",
  "type",
  "state",
  "status",
]);

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const csrf = validateOrigin(request);
    if (csrf) return csrf;

    const { id } = await params;
    const body = await request.json();
    
    // Map frontend 'state' to backend 'status' if present
    const updates: Record<string, any> = { ...body };
    if (updates.state && !updates.status) {
      // Inverse map for state -> status
      const inverseStatusMap: Record<string, string> = {
        'blue': 'new',
        'amber': 'assigned',
        'green': 'completed',
        'red': 'cancelled'
      };
      updates.status = inverseStatusMap[updates.state as string] || updates.state;
      delete updates.state;
    }

    // Forward request to spine_api
    const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const spineApiUrl = `${SPINE_API_URL}/trips/${encodeURIComponent(id)}`;

    const response = await fetch(
      spineApiUrl,
      bffFetchOptions(
        request,
        "PATCH",
        "access_only",
        { "Content-Type": "application/json" },
        updates
      )
    );

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      const errorData = await response.json().catch(() => ({}));
      const detail = errorData.detail;
      const detailMessage =
        typeof detail === "string"
          ? detail
          : typeof detail?.message === "string"
            ? detail.message
            : undefined;
      const detailFailures = Array.isArray(detail?.failures) ? detail.failures : undefined;
      return bffJson(
        {
          message: detailMessage || `Spine API returned ${response.status}`,
          details: detailFailures,
          error: detail || errorData.error || null,
        },
        response.status
      );
    }

    const spineApiData = await response.json();
    const transformedTrip = transformSpineTripToTrip(spineApiData);
    
    return bffJson(transformedTrip);
  } catch (error) {
    console.error("Error patching trip via proxy:", error);
    return bffJson({ error: "Failed to update trip" }, 500);
  }
}
