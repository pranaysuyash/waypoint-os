import { NextRequest, NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${SPINE_API_URL}/api/settings/operational`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error("Spine API operational update error:", errorData);
      return NextResponse.json(
        { error: errorData.detail || "Failed to update operational settings" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error updating operational settings:", error);
    return NextResponse.json(
      { error: "Failed to update operational settings" },
      { status: 500 }
    );
  }
}
