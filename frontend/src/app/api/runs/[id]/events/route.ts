import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: runId } = await params;
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(
      `${spineApiUrl}/runs/${encodeURIComponent(runId)}/events`,
      {
      cache: "no-store",
      headers: forwardAuthHeaders(request),
    }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Run not found" },
          { status: 404 }
        );
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching run events from spine_api:", error);
    return NextResponse.json(
      { error: "Failed to fetch run events" },
      { status: 500 }
    );
  }
}
