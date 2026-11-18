import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, validateOrigin, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

export async function POST(request: NextRequest) {
  const csrf = validateOrigin(request);
  if (csrf) return csrf;

  try {
    const body = await request.json();
    const rawActions = Array.isArray(body) ? body : (body.actions || []);

    if (!Array.isArray(rawActions) || rawActions.length === 0) {
      return bffJson({ error: "actions array is required" }, 400);
    }

    const mappedActions = rawActions.map((a: Record<string, unknown>) => ({
      trip_id: a.tripId || a.trip_id || a.reviewId || a.id,
      action: a.action || "approve",
      notes: a.notes || "",
      reassign_to: a.reassignTo || a.reassign_to,
      error_category: a.errorCategory || a.error_category,
      escalation_outcome: a.escalationOutcome || a.escalation_outcome,
      review_workflow_unit_id: a.reviewWorkflowUnitId || a.review_workflow_unit_id,
    }));

    const spineApiUrl = spineUrl("/analytics/reviews/bulk-action");
    const response = await fetch(
      spineApiUrl,
      {
        ...bffFetchOptions(request, "POST", "access_only", {}, mappedActions),
        cache: "no-store",
      }
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
    console.error("Error processing bulk review action via spine_api:", error);
    return bffJson({ error: "Failed to process bulk review action" }, 500);
  }
}
