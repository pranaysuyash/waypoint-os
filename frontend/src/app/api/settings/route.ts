import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${SPINE_API_URL}/api/settings`, {
      method: "GET",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error("Spine API settings error:", errorData.detail || response.status);
      return NextResponse.json(
        { error: errorData.detail || "Failed to fetch settings" },
        { status: response.status }
      );
    }

    const data = await response.json();
    const nextResponse = NextResponse.json(data);
    nextResponse.headers.set("Cache-Control", "public, max-age=300, s-maxage=300");
    return nextResponse;
  } catch (error) {
    console.error("Error fetching settings from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch settings" },
      { status: 500 }
    );
  }
}
