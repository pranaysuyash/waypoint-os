import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string; step_name: string }> }
) {
  try {
    const { id: runId, step_name: stepName } = await params;
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(
      `${spineApiUrl}/runs/${encodeURIComponent(runId)}/steps/${encodeURIComponent(stepName)}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Run or step not found" },
          { status: 404 }
        );
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching run step from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch run step" },
      { status: 500 }
    );
  }
}
