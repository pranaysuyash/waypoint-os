import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

export async function GET(request: NextRequest) {
  try {
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${spineApiUrl}/health`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Spine API returned ${response.status}`);
    }

    const data = await response.json();
    const nextResponse = NextResponse.json(data);
    nextResponse.headers.set("Cache-Control", "public, max-age=10, s-maxage=10");
    return nextResponse;
  } catch (error) {
    console.error("Error fetching health from spine_api:", error);
    return NextResponse.json(
      { status: "error", error: "Failed to fetch health" },
      { status: 500 }
    );
  }
}
