import { NextRequest, NextResponse } from "next/server";
import { bffFetchOptions, bffJson, validateOrigin, isAuthStatus } from "@/lib/bff-auth";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ tripId: string }> }
) {
  const csrf = validateOrigin(request);
  if (csrf) return csrf;

  try {
    const { tripId } = await params;
    const body = await request.json();
    const { snoozeUntil } = body;

    if (!snoozeUntil) {
      return bffJson({ error: "snoozeUntil is required" }, 400);
    }

    const response = await fetch(
      `${SPINE_API_URL}/trips/${encodeURIComponent(tripId)}/snooze`,
      bffFetchOptions(request, "POST", "access_only", {}, { snooze_until: snoozeUntil })
    );

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      const errorData = await response.json().catch(() => ({}));
      return bffJson(
        { error: errorData.detail || `Spine API returned ${response.status}` },
        response.status
      );
    }

    const data = await response.json();
    return bffJson(data);
  } catch (error) {
    console.error("Error snoozing trip via spine_api:", error);
    return bffJson({ error: "Failed to snooze trip" }, 500);
  }
}
