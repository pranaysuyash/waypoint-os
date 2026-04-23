import { NextRequest, NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tripIds, assignTo, reason } = body;

    if (!tripIds || !Array.isArray(tripIds) || !assignTo) {
      return NextResponse.json(
        { error: "tripIds (string[]) and assignTo are required" },
        { status: 400 }
      );
    }

    const results = [];
    const failures = [];

    for (const tripId of tripIds) {
      try {
        const response = await fetch(
          `${SPINE_API_URL}/trips/${encodeURIComponent(tripId)}/assign`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              agent_id: assignTo,
              agent_name: assignTo,
              assigned_by: "owner",
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          failures.push({
            tripId,
            error: errorData.detail || `Status ${response.status}`,
          });
        } else {
          results.push(tripId);
        }
      } catch (err) {
        failures.push({
          tripId,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    }

    return NextResponse.json({
      success: failures.length === 0,
      assigned: results.length,
      failures: failures.length > 0 ? failures : undefined,
    });
  } catch (error) {
    console.error("Error assigning trips via spine-api:", error);
    return NextResponse.json(
      { error: "Failed to assign trips" },
      { status: 500 }
    );
  }
}
