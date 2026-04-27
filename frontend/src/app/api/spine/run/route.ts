/**
 * Dedicated proxy for /api/spine/run
 *
 * The spine pipeline can take 15-30+ seconds to run.
 * The generic proxy has a 10s timeout which causes 504 errors.
 * This route uses a 60s timeout to allow long-running spine runs.
 */

import { NextRequest } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";

const SPINE_RUN_TIMEOUT_MS = 60_000;

export async function POST(request: NextRequest) {
  return proxyRequest(request, {
    backendPath: "run",
    timeoutMs: SPINE_RUN_TIMEOUT_MS,
  });
}
