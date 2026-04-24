/**
 * spine-client.ts - TypeScript client for calling the Python spine via HTTP.
 *
 * Calls spine-api (FastAPI service) instead of spawning a subprocess per request.
 * The spine-api service is persistent and pre-loads all Python modules.
 *
 * In development: connect to localhost:8000 (spine-api running via `uv run ...`)
 * In production: connect to the deployed spine-api service URL
 *
 * Set SPINE_API_URL env var to override the default (e.g., in docker-compose / k8s).
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

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function runSpine(
  request: SpineRunRequest,
  extraHeaders?: Record<string, string>
): Promise<SpineRunResponse> {
  const response = await fetch(`${SPINE_API_URL}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...extraHeaders,
    },
    body: JSON.stringify(request),
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