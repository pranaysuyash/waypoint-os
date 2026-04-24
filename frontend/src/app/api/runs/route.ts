import { NextResponse } from "next/server";

export async function GET() {
  try {
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${spineApiUrl}/runs`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching runs from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch runs" },
      { status: 500 }
    );
  }
}
