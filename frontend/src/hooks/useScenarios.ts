/**
 * Custom hook for fetching and managing scenario data
 */

import { useState, useEffect, useCallback } from "react";
import { getScenarios, getScenario, type ScenarioListItem, type ScenarioDetail } from "@/lib/api-client";

export function useScenarios() {
  const [data, setData] = useState<ScenarioListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await getScenarios();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch scenarios:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useScenario(id: string | null) {
  const [data, setData] = useState<ScenarioDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!id) {
      setData(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    getScenario(id)
      .then(setData)
      .catch((err) => {
        setError(err);
        console.error("Failed to fetch scenario:", err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [id]);

  return { data, isLoading, error };
}
