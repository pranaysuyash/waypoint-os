import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: tripId } = await params;
    const body = await request.json();
    const { unassigned_by } = body;

    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(
      `${spineApiUrl}/trips/${encodeURIComponent(tripId)}/unassign`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unassigned_by: unassigned_by || "system",
        }),
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Trip not found" },
          { status: 404 }
        );
      }
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || `Spine API returned ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error unassigning trip:", error);
    return NextResponse.json(
      { error: "Failed to unassign trip" },
      { status: 500 }
    );
  }
}
