import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: tripId } = await params;
    const body = await request.json();
    const { acknowledged_flags } = body;

    if (!acknowledged_flags || !Array.isArray(acknowledged_flags)) {
      return NextResponse.json(
        { error: "acknowledged_flags (string[]) is required" },
        { status: 400 }
      );
    }

    // Forward to spine-api
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(
      `${spineApiUrl}/trips/${encodeURIComponent(tripId)}/suitability/acknowledge`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ acknowledged_flags }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || `Spine API returned ${response.status}` },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error acknowledging suitability flags:", error);
    return NextResponse.json(
      { error: "Failed to acknowledge suitability flags" },
      { status: 500 }
    );
  }
}
