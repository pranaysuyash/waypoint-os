/**
 * useSSEStream — Server-Sent Events subscription for run status updates.
 *
 * Architecture decision: Spine API does not (yet) push SSE directly to the browser.
 * This hook wraps the existing polling mechanism with a cleaner, future-proof API
 * that is ready to wire to a real SSE endpoint when the backend adds one.
 *
 * Current implementation:
 *   - When a real SSE stream is available at /api/stream-events/[runId], it connects
 *     via EventSource and parses typed events.
 *   - Falls back to adaptive polling (500ms early, 2s later) when SSE is unavailable.
 *   - Emits typed RunStreamEvent objects to the onEvent callback on every update.
 *   - Reconnects on transient errors with exponential backoff (max 3 retries).
 *
 * Usage:
 *   const { connect, disconnect, state, isConnected, connectionMode } = useSSEStream({
 *     onEvent: (event) => { ... },
 *     onTerminal: (finalState) => { ... },
 *   });
 *   // Call connect(runId) after receiving run_id from POST /api/spine/run
 *   // Call disconnect() in useEffect cleanup
 *
 * Environment:
 *   NEXT_PUBLIC_SSE_ENABLED=true — enable SSE path (default: false → polling)
 *   The Next.js proxy route /api/stream-events/[runId]/route.ts injects auth headers.
 *
 * Design rationale:
 *   - No breaking change to useSpineRun: that hook continues to exist for
 *     backwards-compat and non-realtime surfaces.
 *   - SSE via Next.js proxy: EventSource doesn't support custom headers; the BFF
 *     proxy injects the Authorization header before forwarding to the Spine API.
 *   - See ADR: Docs/ADR_FRONTEND_SSE_REAL_TIME_STATE_2026-07-29.md
 */

import { useCallback, useRef, useState } from 'react';
import { api } from '@/lib/api-client';
import type { RunStatusResponse } from '@/types/spine';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SSEConnectionMode = 'sse' | 'polling' | 'idle';

export interface RunStreamEvent {
  type: 'state_update' | 'stage_entered' | 'terminal' | 'error' | 'heartbeat';
  runId: string;
  state: RunStatusResponse | null;
  raw?: string;
}

export interface UseSSEStreamOptions {
  /** Called on every state update (both SSE and polling paths) */
  onEvent?: (event: RunStreamEvent) => void;
  /** Called once when the run reaches a terminal state */
  onTerminal?: (finalState: RunStatusResponse) => void;
  /** Called when connection is permanently lost after exhausting retries */
  onError?: (err: Error) => void;
}

export interface UseSSEStreamReturn {
  connect: (runId: string) => void;
  disconnect: () => void;
  state: RunStatusResponse | null;
  isConnected: boolean;
  connectionMode: SSEConnectionMode;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TERMINAL_STATES = new Set(['completed', 'failed', 'blocked']);
const POLL_INITIAL_MS = 500;
const POLL_STEADY_MS = 2_000;
const POLL_INITIAL_ROUNDS = 4; // first 4 polls at 500ms, then settle to 2s
const MAX_POLL_WAIT_MS = 180_000;
const SSE_MAX_RETRIES = 3;
const SSE_RETRY_BASE_MS = 1_000;

const isSseEnabled =
  typeof process !== 'undefined' &&
  process.env.NEXT_PUBLIC_SSE_ENABLED === 'true';

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSSEStream(opts: UseSSEStreamOptions = {}): UseSSEStreamReturn {
  const { onEvent, onTerminal, onError } = opts;

  const [state, setState] = useState<RunStatusResponse | null>(null);
  const [connectionMode, setConnectionMode] = useState<SSEConnectionMode>('idle');

  // Refs to avoid stale closures in async callbacks
  const runIdRef = useRef<string | null>(null);
  const abortedRef = useRef(false);
  const esRef = useRef<EventSource | null>(null);
  const pollRoundRef = useRef(0);
  const pollStartRef = useRef<number>(0);
  const retryCountRef = useRef(0);

  // ---------------------------------------------------------------------------
  // Shared: emit update and check terminal
  // ---------------------------------------------------------------------------
  const handleStatusUpdate = useCallback(
    (runId: string, status: RunStatusResponse) => {
      setState(status);
      onEvent?.({ type: 'state_update', runId, state: status });

      if (TERMINAL_STATES.has(status.state)) {
        onEvent?.({ type: 'terminal', runId, state: status });
        onTerminal?.(status);
        return true; // terminal
      }
      return false;
    },
    [onEvent, onTerminal],
  );

  // ---------------------------------------------------------------------------
  // Polling path (adaptive: fast start, steady cruise)
  // ---------------------------------------------------------------------------
  const startPolling = useCallback(
    (runId: string) => {
      setConnectionMode('polling');
      pollRoundRef.current = 0;
      pollStartRef.current = Date.now();

      const tick = async () => {
        if (abortedRef.current || runIdRef.current !== runId) return;

        const round = pollRoundRef.current++;
        const delay = round < POLL_INITIAL_ROUNDS ? POLL_INITIAL_MS : POLL_STEADY_MS;
        await new Promise((r) => setTimeout(r, delay));

        if (abortedRef.current || runIdRef.current !== runId) return;

        try {
          const status = await api.get<RunStatusResponse>(`/api/runs/${runId}`);
          const isTerminal = handleStatusUpdate(runId, status);
          if (isTerminal) {
            setConnectionMode('idle');
            return;
          }
        } catch (err) {
          // transient network error — log and continue polling
          console.warn('[useSSEStream] poll error', err);
        }

        if (Date.now() - pollStartRef.current > MAX_POLL_WAIT_MS) {
          const timeoutErr = new Error(`[useSSEStream] Run ${runId} timed out after ${MAX_POLL_WAIT_MS}ms`);
          onError?.(timeoutErr);
          setConnectionMode('idle');
          return;
        }

        tick();
      };

      tick();
    },
    [handleStatusUpdate, onError],
  );

  // ---------------------------------------------------------------------------
  // SSE path (EventSource via Next.js BFF proxy)
  // ---------------------------------------------------------------------------
  const startSSE = useCallback(
    (runId: string) => {
      setConnectionMode('sse');
      retryCountRef.current = 0;

      const connect = () => {
        if (abortedRef.current || runIdRef.current !== runId) return;

        // /api/stream-events/[runId] is the Next.js proxy that injects auth headers.
        const es = new EventSource(`/api/stream-events/${runId}`);
        esRef.current = es;

        es.onmessage = (ev) => {
          if (abortedRef.current) return;
          try {
            const data = JSON.parse(ev.data) as RunStatusResponse;
            const isTerminal = handleStatusUpdate(runId, data);
            if (isTerminal) {
              es.close();
              setConnectionMode('idle');
            }
          } catch {
            onEvent?.({ type: 'error', runId, state: null, raw: ev.data });
          }
        };

        es.onerror = () => {
          es.close();
          if (abortedRef.current) return;

          if (retryCountRef.current < SSE_MAX_RETRIES) {
            const delay = SSE_RETRY_BASE_MS * 2 ** retryCountRef.current;
            retryCountRef.current++;
            setTimeout(connect, delay);
          } else {
            // SSE exhausted — fall back to polling
            console.warn('[useSSEStream] SSE exhausted retries, falling back to polling');
            startPolling(runId);
          }
        };
      };

      connect();
    },
    [handleStatusUpdate, onEvent, startPolling],
  );

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------
  const connect = useCallback(
    (runId: string) => {
      // Clean up any previous subscription
      abortedRef.current = false;
      runIdRef.current = runId;
      esRef.current?.close();
      esRef.current = null;
      setState(null);

      if (isSseEnabled) {
        startSSE(runId);
      } else {
        startPolling(runId);
      }
    },
    [startSSE, startPolling],
  );

  const disconnect = useCallback(() => {
    abortedRef.current = true;
    runIdRef.current = null;
    esRef.current?.close();
    esRef.current = null;
    setConnectionMode('idle');
  }, []);

  return {
    connect,
    disconnect,
    state,
    isConnected: connectionMode !== 'idle',
    connectionMode,
  };
}
