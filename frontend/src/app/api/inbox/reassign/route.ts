import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { trip_id, agent_id, agent_name } = body;

    if (!trip_id || !agent_id) {
      return NextResponse.json(
        { error: "trip_id and agent_id are required" },
        { status: 400 }
      );
    }

    const url = new URL(`${SPINE_API_URL}/trips/${encodeURIComponent(trip_id)}/reassign`);
    url.searchParams.set("agent_id", agent_id);
    url.searchParams.set("agent_name", agent_name || agent_id);
    url.searchParams.set("reassigned_by", "owner");

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: forwardAuthHeaders(request),
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
    console.error("Error reassigning trip via spine-api:", error);
    return NextResponse.json(
      { error: "Failed to reassign trip" },
      { status: 500 }
    );
  }
}
