import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ tripId: string }> }
) {
  try {
    const { tripId } = await params;
    const spineApiUrl = spineUrl(`/followups/${tripId}/mark-complete`);
    const response = await fetch(
      spineApiUrl,
      {
        ...bffFetchOptions(request, "PATCH"),
        method: "PATCH",
        cache: "no-store",
      }
    );

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return bffJson(data);
  } catch (error) {
    console.error("Error marking followup complete:", error);
    return bffJson({ error: "Failed to mark followup complete" }, 500);
  }
}
