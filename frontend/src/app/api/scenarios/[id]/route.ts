/**
 * GET /api/scenarios/[id]
 *
 * Returns full scenario by ID.
 * Contract: NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md Section 4.3
 */

import { NextRequest, NextResponse } from "next/server";
import { loadScenarioById } from "@/lib/scenario-loader";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const scenario = loadScenarioById(id);

    if (!scenario) {
      return NextResponse.json(
        { error: "Scenario not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(scenario);
  } catch (error) {
    console.error("Failed to load scenario:", error);
    return NextResponse.json(
      { error: "Failed to load scenario" },
      { status: 500 }
    );
  }
}