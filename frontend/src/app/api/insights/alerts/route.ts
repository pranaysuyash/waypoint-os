import { NextRequest, NextResponse } from "next/server";

const ANALYTICS_SERVICE_URL = process.env.ANALYTICS_SERVICE_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const range = searchParams.get("range") || "30d";

  try {
    const response = await fetch(
      `${ANALYTICS_SERVICE_URL}/analytics/alerts?range=${range}`,
      {
        cache: "no-store",
      }
    );

    if (!response.ok) {
      throw new Error(`Analytics service responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error proxying to analytics alerts:", error);
    return NextResponse.json(
      { error: "Failed to fetch alerts" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const { alertId } = await request.json();
    
    // Forward to spine-api
    const response = await fetch(
      `${process.env.ANALYTICS_SERVICE_URL || "http://127.0.0.1:8000"}/analytics/alerts/${alertId}/dismiss`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Analytics service responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error dismissing alert:", error);
    return NextResponse.json(
      { error: "Failed to dismiss alert" },
      { status: 500 }
    );
  }
}