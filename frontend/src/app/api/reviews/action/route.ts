import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { reviewId, action, notes, reassignTo, errorCategory } = body;

    if (!reviewId) {
      return NextResponse.json(
        { error: "reviewId is required" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${SPINE_API_URL}/trips/${encodeURIComponent(reviewId)}/review/action`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action,
          notes,
          reassign_to: reassignTo,
          error_category: errorCategory,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        {
          error: errorData.detail || `Spine API returned ${response.status}`,
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error processing review action via spine-api:", error);
    return NextResponse.json(
      { error: "Failed to process review action" },
      { status: 500 }
    );
  }
}
