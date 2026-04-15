/**
 * spine-client.ts - TypeScript client for calling the Python spine via subprocess.
 *
 * This module spawns the spine-wrapper.py Python script as a child process
 * and handles input/output serialization.
 */

import { spawn } from "child_process";
import path from "path";
import { SpineStage, OperatingMode } from "@/types/spine";

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

export interface SpineRunResponse {
  packet: unknown;
  validation: unknown;
  decision: unknown;
  strategy: unknown;
  internal_bundle: unknown;
  traveler_bundle: unknown;
  leakage: {
    ok: boolean;
    items: string[];
    [key: string]: unknown;
  };
  assertions: unknown;
  run_ts: string;
}

export interface SpineError {
  error: string;
  error_type: string;
}

const SPINE_WRAPPER_PATH = path.join(
  process.cwd(),
  "src",
  "lib",
  "spine-wrapper.py"
);

export async function runSpine(
  request: SpineRunRequest
): Promise<SpineRunResponse> {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python3", [SPINE_WRAPPER_PATH], {
      stdio: ["pipe", "pipe", "pipe"],
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";

    pythonProcess.stdout?.on("data", (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr?.on("data", (data) => {
      stderr += data.toString();
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Spine subprocess exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout) as SpineRunResponse | SpineError;
        if ("error" in result) {
          reject(new Error(`Spine error: ${result.error} (${result.error_type})`));
          return;
        }
        resolve(result);
      } catch (parseError) {
        reject(new Error(`Failed to parse spine output: ${stdout}`));
      }
    });

    pythonProcess.on("error", (err) => {
      reject(new Error(`Failed to spawn spine subprocess: ${err.message}`));
    });

    // Write input to stdin
    const input = JSON.stringify(request);
    pythonProcess.stdin?.write(input);
    pythonProcess.stdin?.end();
  });
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

  // Validate stage
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

  // Validate operating_mode
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

  // Validate strict_leakage
  if (typeof req.strict_leakage !== "boolean") {
    errors.push("strict_leakage must be a boolean");
  }

  // Validate optional string fields
  const stringFields = ["raw_note", "owner_note", "itinerary_text", "scenario_id"];
  for (const field of stringFields) {
    if (req[field] !== undefined && req[field] !== null && typeof req[field] !== "string") {
      errors.push(`${field} must be a string or null`);
    }
  }

  // Validate structured_json
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