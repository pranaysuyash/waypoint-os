/**
 * useSpineRun - Async spine pipeline execution with polling
 *
 * Submits a run via POST /api/spine/run, receives a run_id immediately,
 * then polls GET /api/runs/{run_id} every 2s until the run
 * reaches a terminal state (completed / failed / blocked).
 *
 * Returns:
 *   execute(payload)       - start the async run, returns run_id
 *   cancel()               - abort the current run
 *   state                   - RunStatusResponse | null  (updates in real time)
 *   isLoading                - boolean (true while polling)
 *   error                    - Error | null
 *   runId                    - string | null (set immediately after submit)
 */

import { useState, useCallback, useRef } from "react";
import { api, ApiException } from "@/lib/api-client";
import type { SpineRunRequest, RunStatusResponse } from "@/types/spine";

const STATUS_TERMINAL = new Set(["completed", "failed", "blocked"]);
const POLL_INTERVAL_MS = 2_000;
const MAX_WAIT_MS = 180_000;

export function useSpineRun() {
  const [state, setState] = useState<RunStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const abortRef = useRef(false);

  const execute = useCallback(async (payload: SpineRunRequest) => {
    setIsLoading(true);
    setError(null);
    setState(null);
    setRunId(null);
    abortRef.current = false;

    try {
      const accepted = await api.post<{ run_id: string; state: string }>(
        "/api/spine/run",
        payload,
        { retry: 0 }
      );

      if (!accepted.run_id) {
        throw new ApiException("No run_id returned", 500, "NO_RUN_ID");
      }

      setRunId(accepted.run_id);

      const start = Date.now();

      while (Date.now() - start < MAX_WAIT_MS) {
        if (abortRef.current) {
          setIsLoading(false);
          return null;
        }

        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));

        if (abortRef.current) {
          setIsLoading(false);
          return null;
        }

        const status = await api.get<RunStatusResponse>(
          `/api/runs/${accepted.run_id}`
        );

        setState(status);

          if (STATUS_TERMINAL.has(status.state)) {
            setIsLoading(false);

            if (status.state !== "completed") {
              const msg =
                status.error_message ||
                status.block_reason ||
                `Run ended in ${status.state}`;
              const err = new ApiException(msg, 500, status.state);
              setError(err);
              throw err;
            }

            return status;
          }
      }

      throw new ApiException("Run timed out", 504, "RUN_TIMEOUT");
    } catch (err) {
      if (!abortRef.current) {
        setError(err as Error);
        setIsLoading(false);
      }
      throw err;
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current = true;
    setIsLoading(false);
    setRunId(null);
  }, []);

  const reset = useCallback(() => {
    abortRef.current = false;
    setState(null);
    setError(null);
    setIsLoading(false);
    setRunId(null);
  }, []);

  return { state, isLoading, error, runId, execute, cancel, reset };
}
