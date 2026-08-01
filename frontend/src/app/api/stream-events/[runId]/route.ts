/**
 * /api/stream-events/[runId]/route.ts — Next.js BFF SSE proxy
 *
 * EventSource (the browser SSE client) does not support custom request headers,
 * so it cannot send an Authorization: Bearer token directly to the Spine API.
 *
 * This Next.js Route Handler bridges the gap:
 *   Browser EventSource → /api/stream-events/[runId]
 *     → (add Authorization: Bearer <token> from cookie/session)
 *     → Spine API /runs/{runId}/events (SSE stream)
 *     → pipe back to browser
 *
 * Current state: If the Spine API does not yet expose a streaming SSE endpoint,
 * this route falls back to returning a 404 so the client degrades to polling.
 *
 * Auth strategy:
 *   - JWT is stored in an httpOnly cookie (set by the auth flow).
 *   - Route reads it via `cookies()` from next/headers.
 *   - Cookie name: SPINE_AUTH_COOKIE_NAME env var (default: 'spine_auth_token').
 *   - Unauthenticated requests return 401 immediately.
 *
 * Design rationale: See ADR_FRONTEND_SSE_REAL_TIME_STATE_2026-07-29.md
 */

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const SPINE_API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const AUTH_COOKIE_NAME = process.env.SPINE_AUTH_COOKIE_NAME ?? 'spine_auth_token';

// SSE content-type header
const SSE_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache, no-transform',
  Connection: 'keep-alive',
  'X-Accel-Buffering': 'no', // Prevent Nginx from buffering the stream
};

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs'; // Edge runtime doesn't support long-lived SSE from upstream

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ runId: string }> },
) {
  const { runId } = await params;

  if (!runId || typeof runId !== 'string' || !runId.match(/^run_[a-zA-Z0-9_-]+$/)) {
    return NextResponse.json({ error: 'Invalid runId' }, { status: 400 });
  }

  // Read JWT from httpOnly cookie
  const cookieStore = await cookies();
  const authToken = cookieStore.get(AUTH_COOKIE_NAME)?.value;

  if (!authToken) {
    return NextResponse.json(
      { error: 'Unauthorized — no auth token present' },
      { status: 401 },
    );
  }

  // Check if SPINE_API_BASE exposes an SSE streaming endpoint for runs.
  // Upstream URL: GET /runs/{runId}/stream (adjust if backend uses different path)
  const upstreamUrl = `${SPINE_API_BASE}/runs/${runId}/stream`;

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(upstreamUrl, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${authToken}`,
        Accept: 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      // @ts-expect-error — Node.js fetch supports duplex streaming
      duplex: 'half',
    });
  } catch (networkErr) {
    // Spine API is not reachable — client will fall back to polling
    return NextResponse.json(
      { error: 'Upstream unavailable', detail: String(networkErr) },
      { status: 503 },
    );
  }

  if (upstreamResponse.status === 404) {
    // Spine API does not yet expose the SSE endpoint — signal client to use polling
    return NextResponse.json(
      { error: 'SSE not available for this run — use polling' },
      { status: 404 },
    );
  }

  if (!upstreamResponse.ok) {
    const errorBody = await upstreamResponse.text().catch(() => '');
    return NextResponse.json(
      { error: 'Upstream error', status: upstreamResponse.status, detail: errorBody },
      { status: upstreamResponse.status },
    );
  }

  // Pipe the upstream SSE stream directly to the browser.
  // The upstream response body is a ReadableStream<Uint8Array>.
  if (!upstreamResponse.body) {
    return NextResponse.json({ error: 'No stream body from upstream' }, { status: 502 });
  }

  return new Response(upstreamResponse.body, {
    headers: SSE_HEADERS,
    status: 200,
  });
}
