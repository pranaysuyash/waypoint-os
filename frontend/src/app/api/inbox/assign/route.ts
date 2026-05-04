import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";

/**
 * POST /api/inbox/assign — proxy to backend /inbox/assign.
 *
 * Accepts: { tripIds: string[], assignTo: string, notifyAssignee?: boolean }
 * Forwards to backend as-is (camelCase matches backend contract).
 */
export async function POST(request: NextRequest) {
  try {
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/inbox/assign`;

    const response = await fetch(
      spineApiUrl,
      bffFetchOptions(request, "POST", "access_only", { "Content-Type": "application/json" }, await request.json()),
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
    console.error("Error proxying inbox assign:", error);
    return bffJson({ error: "Failed to assign trips" }, 500);
  }
}
