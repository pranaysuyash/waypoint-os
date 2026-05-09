/**
 * BFF route: GET /api/auth/validate-code/[code]
 *
 * Validates a workspace invitation code and returns the agency name.
 * Used by the /join/[code] page before the user fills in the signup form.
 *
 * This is a public endpoint - no auth cookie required. The backend /api/auth/*
 * prefix is on the PUBLIC_PREFIXES allowlist in FastAPI's auth middleware.
 *
 * Returns:
 *   200 { valid: true, agency_name, agency_id, code_type }
 *   404 { error: "Invitation code not found" }
 */

import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson } from "@/lib/bff-auth";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ code: string }> }
) {
  const { code } = await params;
  const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/auth/validate-code/${encodeURIComponent(code)}`;

  try {
    const response = await fetch(spineApiUrl, bffFetchOptions(request, "GET"));

    if (response.status === 404) {
      return bffJson({ error: "Invitation code not found" }, 404);
    }

    if (!response.ok) {
      return bffJson({ error: "Failed to validate code" }, response.status);
    }

    const data = await response.json();
    return bffJson(data);
  } catch {
    return bffJson({ error: "Backend unavailable" }, 502);
  }
}
