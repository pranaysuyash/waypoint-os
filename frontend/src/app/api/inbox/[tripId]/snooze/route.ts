import { NextRequest, NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ tripId: string }> }
) {
  try {
    const { tripId } = await params;
    const body = await request.json();
    const { snoozeUntil } = body;

    if (!snoozeUntil) {
      return NextResponse.json(
        { error: "snoozeUntil is required" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${SPINE_API_URL}/trips/${encodeURIComponent(tripId)}/snooze`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ snooze_until: snoozeUntil }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || `Spine API returned ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error snoozing trip via spine-api:", error);
    return NextResponse.json(
      { error: "Failed to snooze trip" },
      { status: 500 }
    );
  }
}
