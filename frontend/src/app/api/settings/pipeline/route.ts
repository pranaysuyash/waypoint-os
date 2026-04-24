import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${SPINE_API_URL}/api/settings/pipeline`, {
      cache: "no-store",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching pipeline settings from spine_api:", error);
    return NextResponse.json(
      { error: "Failed to fetch pipeline settings" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${SPINE_API_URL}/api/settings/pipeline`, {
      method: "PUT",
      headers: forwardAuthHeaders(request),
      body: JSON.stringify(body),
    });

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
    console.error("Error updating pipeline settings via spine_api:", error);
    return NextResponse.json(
      { error: "Failed to update pipeline settings" },
      { status: 500 }
    );
  }
}
