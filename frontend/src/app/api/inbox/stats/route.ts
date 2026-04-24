import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${SPINE_API_URL}/trips?limit=1000`, {
      cache: "no-store",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    const trips = data.items || [];

    const total = trips.length;
    const unassigned = trips.filter(
      (t: any) => !t.assigned_to && t.status === "new"
    ).length;
    const critical = trips.filter(
      (t: any) =>
        t.analytics?.escalation_severity === "critical" ||
        t.analytics?.requires_review === true
    ).length;
    const atRisk = trips.filter(
      (t: any) =>
        t.analytics?.escalation_severity === "warning" ||
        t.analytics?.approval_required_for_send === true
    ).length;

    return NextResponse.json({ total, unassigned, critical, atRisk });
  } catch (error) {
    console.error("Error fetching inbox stats from spine_api:", error);
    return NextResponse.json(
      { error: "Failed to fetch inbox stats" },
      { status: 500 }
    );
  }
}
