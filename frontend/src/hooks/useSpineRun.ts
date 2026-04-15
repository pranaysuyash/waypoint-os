/**
 * Custom hook for running spine operations
 */

import { useState, useCallback } from "react";
import { runSpine } from "@/lib/api-client";
import type { SpineRunRequest, SpineRunResponse } from "@/types/spine";

export function useSpineRun() {
  const [data, setData] = useState<SpineRunResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async (request: SpineRunRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await runSpine(request);
      setData(result);
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      console.error("Spine run failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return { data, isLoading, error, execute, reset };
}
