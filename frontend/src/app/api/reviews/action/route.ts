import { NextRequest, NextResponse } from "next/server";

const ANALYTICS_SERVICE_URL = process.env.ANALYTICS_SERVICE_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { reviewId, action, notes, reassignTo } = body;

    if (!reviewId) {
      return NextResponse.json({ error: "reviewId is required" }, { status: 400 });
    }

    // Proxy to backend: POST /trips/{tripId}/review/action
    const response = await fetch(`${ANALYTICS_SERVICE_URL}/trips/${reviewId}/review/action`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
        notes: notes || "",
        reassign_to: reassignTo,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend error (${response.status}):`, errorText);
      return NextResponse.json(
        { error: `Backend service responded with ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error processing review action:", error);
    return NextResponse.json(
      { error: "Internal server error in BFF action proxy" },
      { status: 500 }
    );
  }
}
