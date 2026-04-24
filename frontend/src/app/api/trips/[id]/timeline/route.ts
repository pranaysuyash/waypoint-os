import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { searchParams } = new URL(request.url);
  const stage = searchParams.get("stage");
  const { id } = await params;
  const tripId = id;

  if (!tripId) {
    return NextResponse.json(
      { error: "Trip ID is required" },
      { status: 400 }
    );
  }

  try {
    const url = stage
      ? `${SPINE_API_URL}/api/trips/${encodeURIComponent(tripId)}/timeline?stage=${stage}`
      : `${SPINE_API_URL}/api/trips/${encodeURIComponent(tripId)}/timeline`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Trip not found" },
          { status: 404 }
        );
      }
      throw new Error(`Spine API responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error fetching timeline for trip ${tripId}:`, error);
    return NextResponse.json(
      { error: "Failed to fetch trip timeline" },
      { status: 500 }
    );
  }
}
