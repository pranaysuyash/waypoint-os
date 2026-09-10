import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, validateOrigin, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

export async function POST(request: NextRequest) {
  const csrf = validateOrigin(request);
  if (csrf) return csrf;

  try {
    const body = await request.json();
    const {
      reviewId,
      action,
      notes,
      reassignTo,
      errorCategory,
      escalationOutcome,
      reviewWorkflowUnitId,
    } = body;

    if (!reviewId) {
      return bffJson({ error: "reviewId is required" }, 400);
    }

    const reviewActionUrl = spineUrl(`/trips/${encodeURIComponent(reviewId)}/review/action`);
    const response = await fetch(
      reviewActionUrl,
      { ...bffFetchOptions(request, "POST", "access_only", {}, {
        action,
        notes,
        reassign_to: reassignTo,
        error_category: errorCategory,
        escalation_outcome: escalationOutcome,
        review_workflow_unit_id: reviewWorkflowUnitId,
      }), cache: "no-store" }
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
    console.error("Error processing review action via spine_api:", error);
    return bffJson({ error: "Failed to process review action" }, 500);
  }
}
