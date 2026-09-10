import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, validateOrigin, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

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

    const snoozeUrl = spineUrl(`/trips/${encodeURIComponent(tripId)}/snooze`);
    const response = await fetch(
      snoozeUrl,
      { ...bffFetchOptions(request, "POST", "access_only", {}, { snooze_until: snoozeUntil }), cache: "no-store" }
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
