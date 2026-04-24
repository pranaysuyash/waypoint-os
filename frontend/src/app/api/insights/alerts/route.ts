import { NextRequest, NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const range = searchParams.get("range") || "30d";

  try {
    const response = await fetch(
      `${SPINE_API_URL}/analytics/alerts?range=${range}`,
      {
        cache: "no-store",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Analytics service responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error proxying to analytics alerts:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to fetch alerts" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const { alertId } = await request.json();
    
    // Forward to spine-api
    const response = await fetch(
      `${SPINE_API_URL}/analytics/alerts/${encodeURIComponent(alertId)}/dismiss`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || `Analytics service responded with ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error dismissing alert:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to dismiss alert" },
      { status: 500 }
    );
  }
}