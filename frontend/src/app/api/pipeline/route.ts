import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

export async function GET(request: NextRequest) {
  try {
    // Forward request to spine_api analytics endpoint
    const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${SPINE_API_URL}/analytics/pipeline`, {
      method: "GET",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching pipeline from spine_api:", error);
    return NextResponse.json(
      { error: "Failed to fetch pipeline" },
      { status: 500 }
    );
  }
}
