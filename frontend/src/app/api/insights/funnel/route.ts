import { NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const response = await fetch(`${SPINE_API_URL}/analytics/funnel`, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching funnel from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch funnel" },
      { status: 500 }
    );
  }
}
