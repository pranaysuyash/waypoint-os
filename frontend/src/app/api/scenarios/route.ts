/**
 * GET /api/scenarios
 *
 * Returns list of all scenario IDs and titles.
 * Contract: NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md Section 4.2
 */

import { NextResponse } from "next/server";
import { loadScenarioList } from "@/lib/scenario-loader";

export async function GET() {
  try {
    const scenarios = loadScenarioList();
    return NextResponse.json({ items: scenarios });
  } catch (error) {
    console.error("Failed to load scenarios:", error);
    return NextResponse.json(
      { error: "Failed to load scenarios" },
      { status: 500 }
    );
  }
}