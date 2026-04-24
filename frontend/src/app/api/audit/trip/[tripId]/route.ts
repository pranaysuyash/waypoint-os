import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ tripId: string }> }
) {
  try {
    const { tripId } = await params;

    // Backend doesn't have a dedicated /audit/trip endpoint, so we filter client-side
    const response = await fetch(`${SPINE_API_URL}/audit?limit=1000`, {
      cache: "no-store",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    const events = data.items || [];
    const tripEvents = events.filter(
      (e: any) => e?.details?.trip_id === tripId
    );

    return NextResponse.json(tripEvents);
  } catch (error) {
    console.error("Error fetching audit events for trip:", error);
    return NextResponse.json(
      { error: "Failed to fetch audit events for trip" },
      { status: 500 }
    );
  }
}
