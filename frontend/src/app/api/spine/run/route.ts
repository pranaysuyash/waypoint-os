/**
 * POST /api/spine/run
 *
 * BFF route handler for the spine run endpoint.
 *
 * Calls spine_api (persistent FastAPI service) and forwards the canonical
 * SpineRunResponse directly without ad-hoc remapping.
 *
 * Error handling:
 *   - 400: bad request / validation failure
 *   - 422: strict leakage failure (ok=false from spine_api)
 *   - 500: spine_api internal error
 *
 * Canonical contract: SpineRunResponse {
 *   ok: boolean,
 *   run_id: string,
 *   packet, validation, decision, strategy: backend objects | null,
 *   traveler_bundle, internal_bundle: PromptBundle | null,
 *   safety: { strict_leakage, leakage_passed, leakage_errors },
 *   meta: { stage, operating_mode, fixture_id, execution_ms }
 * }
 */

import { NextRequest, NextResponse } from "next/server";
import { runSpine, validateSpineRequest } from "@/lib/spine-client";
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
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 }
    );
  }

  const validation = validateSpineRequest(body);
  if (!validation.valid) {
    return NextResponse.json(
      { error: "Validation failed", details: validation.errors },
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

  try {
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

    if (!result.ok) {
      return NextResponse.json(
        {
          ok: false,
          run_id: result.run_id,
          safety: result.safety,
          meta: result.meta,
          error: "Strict leakage failure",
        },
        { status: 422 }
      );
    }

    return NextResponse.json(result);

  } catch (error) {
    console.error("Spine run error:", error);

    if (error instanceof Error) {
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