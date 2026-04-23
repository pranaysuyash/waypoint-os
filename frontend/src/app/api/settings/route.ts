import { NextRequest, NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const response = await fetch(`${SPINE_API_URL}/api/settings`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Spine API settings error:", errorText);
      return NextResponse.json(
        { error: "Failed to fetch settings" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching settings from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch settings" },
      { status: 500 }
    );
  }
}
