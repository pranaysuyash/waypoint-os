import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Forward request to spine-api analytics endpoint
    const response = await fetch("http://localhost:8000/analytics/pipeline", {
      method: "GET",
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
    console.error("Error fetching pipeline from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch pipeline" },
      { status: 500 }
    );
  }
}
