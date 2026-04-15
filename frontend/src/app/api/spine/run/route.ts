/**
 * POST /api/spine/run
 *
 * BFF route handler for the spine run endpoint.
 * Validates input, calls the Python spine via subprocess, and returns JSON.
 *
 * Contract: NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md Section 4.1
 */

import { NextRequest, NextResponse } from "next/server";
import { runSpine, validateSpineRequest, SpineRunResponse } from "@/lib/spine-client";
import { SpineStage, OperatingMode } from "@/types/spine";

const VALID_STAGES: SpineStage[] = [
  "discovery",
  "shortlist",
  "proposal",
  "booking",
];

const VALID_MODES: OperatingMode[] = [
  "normal_intake",
  "audit",
  "emergency",
  "follow_up",
  "cancellation",
  "post_trip",
  "coordinator_group",
  "owner_review",
];

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json(
        { error: "Invalid JSON body" },
        { status: 400 }
      );
    }

    // Validate request structure
    const validation = validateSpineRequest(body);
    if (!validation.valid) {
      return NextResponse.json(
        {
          error: "Validation failed",
          details: validation.errors,
        },
        { status: 400 }
      );
    }

    const req = body as {
      raw_note?: string | null;
      owner_note?: string | null;
      structured_json?: Record<string, unknown> | null;
      itinerary_text?: string | null;
      stage: SpineStage;
      operating_mode: OperatingMode;
      strict_leakage: boolean;
      scenario_id?: string | null;
    };

    // Additional enum validation at runtime
    if (!VALID_STAGES.includes(req.stage)) {
      return NextResponse.json(
        {
          error: `Invalid stage: ${req.stage}`,
          details: `stage must be one of: ${VALID_STAGES.join(", ")}`,
        },
        { status: 400 }
      );
    }

    if (!VALID_MODES.includes(req.operating_mode)) {
      return NextResponse.json(
        {
          error: `Invalid operating_mode: ${req.operating_mode}`,
          details: `operating_mode must be one of: ${VALID_MODES.join(", ")}`,
        },
        { status: 400 }
      );
    }

    // Call spine via subprocess
    const result = await runSpine({
      raw_note: req.raw_note ?? null,
      owner_note: req.owner_note ?? null,
      structured_json: req.structured_json ?? null,
      itinerary_text: req.itinerary_text ?? null,
      stage: req.stage,
      operating_mode: req.operating_mode,
      strict_leakage: req.strict_leakage,
      scenario_id: req.scenario_id ?? null,
    });

    // Return normalized response matching the contract
    const response = {
      packet: result.packet,
      validation: result.validation,
      decision: result.decision,
      strategy: result.strategy,
      internal_bundle: result.internal_bundle,
      traveler_bundle: result.traveler_bundle,
      leakage: {
        ok: (result.leakage as Record<string, boolean | string[]>)?.is_safe ?? true,
        items: (result.leakage as Record<string, string[]>)?.leaks ?? [],
      },
      assertions: result.assertions,
      run_ts: result.run_ts,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("Spine run error:", error);

    // Handle known error types
    if (error instanceof Error) {
      // Check for subprocess errors
      if (error.message.includes("subprocess")) {
        return NextResponse.json(
          { error: "Spine execution failed", details: error.message },
          { status: 500 }
        );
      }

      return NextResponse.json(
        { error: "Spine run failed", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}