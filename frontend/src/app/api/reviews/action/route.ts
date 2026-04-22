import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { reviewId, action } = body;

    if (!reviewId) {
      return NextResponse.json({ error: "reviewId is required" }, { status: 400 });
    }

    return NextResponse.json({
      success: true,
      review: {
        id: reviewId,
        status: action === "approve" ? "approved" : action === "reject" ? "rejected" : "revision_needed",
        reviewedAt: new Date().toISOString(),
        reviewedBy: "owner",
      },
    });
  } catch (error) {
    console.error("Error processing review action:", error);
    return NextResponse.json(
      { error: "Failed to process review action" },
      { status: 500 }
    );
  }
}
