import { NextResponse } from "next/server";

// Mock stats data (in production, this would be calculated from actual trip data)
export async function GET() {
  try {
    return NextResponse.json({
      active: 12,
      pendingReview: 5,
      readyToBook: 8,
      needsAttention: 2,
    });
  } catch (error) {
    console.error("Error fetching stats:", error);
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
