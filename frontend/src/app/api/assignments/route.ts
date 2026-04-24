import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const agentId = searchParams.get("agent_id");

  try {
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const url = agentId
      ? `${spineApiUrl}/assignments?agent_id=${encodeURIComponent(agentId)}`
      : `${spineApiUrl}/assignments`;

    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching assignments from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch assignments" },
      { status: 500 }
    );
  }
}
