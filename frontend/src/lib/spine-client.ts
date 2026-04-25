/**
 * spine-client.ts — TypeScript client for calling the Python spine via HTTP.
 *
 * All calls go through the Next.js BFF catch-all proxy at /api/spine/[...path],
 * which forwards cookies (including access_token) transparently to FastAPI.
 *
 * The client does NOT manage tokens. Authentication is handled entirely by:
 *   1. FastAPI sets access_token + refresh_token as httpOnly cookies
 *   2. Next.js middleware checks access_token cookie for page-route guards
 *   3. This client just calls /api/spine/* and the browser sends cookies automatically
 *
 * Set SPINE_API_URL env var to override the default (e.g., in docker-compose / k8s).
 * In production, the BFF is the gateway — no direct connection to FastAPI.
 */

import { SpineStage, OperatingMode, SpineRunResponse } from "@/types/spine";

export interface SpineRunRequest {
  raw_note?: string | null;
  owner_note?: string | null;
  structured_json?: Record<string, unknown> | null;
  itinerary_text?: string | null;
  stage: SpineStage;
  operating_mode: OperatingMode;
  strict_leakage: boolean;
  scenario_id?: string | null;
}

export type { SpineRunResponse };

// BFF proxy prefix — browser sends cookies automatically
const SPINE_PREFIX = "/api/spine";

export async function runSpine(
  request: SpineRunRequest,
): Promise<SpineRunResponse> {
  const response = await fetch(`${SPINE_PREFIX}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(request),
    credentials: "include", // ensure cookies are sent
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as {
      detail?: { message?: string; error?: string; error_type?: string };
      error?: string;
      error_type?: string;
    };
    const detail = errorBody.detail;
    const message = detail?.message || detail?.error || errorBody.error || response.statusText;
    const errorType = detail?.error_type || errorBody.error_type || "HTTPError";
    throw new Error(
      detail
        ? `Spine error: ${message} (${errorType})`
        : `Spine API returned ${response.status}: ${response.statusText}`
    );
  }

  const result = (await response.json()) as SpineRunResponse;
  return result;
}

export function validateSpineRequest(request: unknown): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!request || typeof request !== "object") {
    return { valid: false, errors: ["Request must be an object"] };
  }

  const req = request as Record<string, unknown>;

  const validStages: SpineStage[] = [
    "discovery",
    "shortlist",
    "proposal",
    "booking",
  ];
  if (!req.stage || !validStages.includes(req.stage as SpineStage)) {
    errors.push(
      `stage must be one of: ${validStages.join(", ")}. Got: ${req.stage}`
    );
  }

  const validModes: OperatingMode[] = [
    "normal_intake",
    "audit",
    "emergency",
    "follow_up",
    "cancellation",
    "post_trip",
    "coordinator_group",
    "owner_review",
  ];
  if (
    !req.operating_mode ||
    !validModes.includes(req.operating_mode as OperatingMode)
  ) {
    errors.push(
      `operating_mode must be one of: ${validModes.join(", ")}. Got: ${req.operating_mode}`
    );
  }

  if (typeof req.strict_leakage !== "boolean") {
    errors.push("strict_leakage must be a boolean");
  }

  const stringFields = ["raw_note", "owner_note", "itinerary_text", "scenario_id"];
  for (const field of stringFields) {
    if (req[field] !== undefined && req[field] !== null && typeof req[field] !== "string") {
      errors.push(`${field} must be a string or null`);
    }
  }

  if (
    req.structured_json !== undefined &&
    req.structured_json !== null &&
    typeof req.structured_json !== "object"
  ) {
    errors.push("structured_json must be an object or null");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}