import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";

export async function PATCH(
  request: NextRequest,
  { params }: { params: { tripId: string } }
) {
  try {
    const { tripId } = params;
    const body = await request.json();
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/followups/${tripId}/reschedule`;
    const response = await fetch(
      spineApiUrl,
      {
        ...bffFetchOptions(request, "PATCH"),
        method: "PATCH",
        body: JSON.stringify(body),
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
    console.error("Error rescheduling followup:", error);
    return bffJson({ error: "Failed to reschedule followup" }, 500);
  }
}
