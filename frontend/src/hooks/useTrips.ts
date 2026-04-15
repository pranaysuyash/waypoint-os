/**
 * Custom hook for fetching and managing trip data
 */

import { useState, useEffect, useCallback } from "react";
import {
  getTrips,
  getTrip,
  getTripStats,
  getPipeline,
  type Trip,
  type TripStats,
  type PipelineStage,
} from "@/lib/api-client";

export function useTrips(params?: {
  state?: string;
  limit?: number;
  offset?: number;
}) {
  const [data, setData] = useState<Trip[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await getTrips(params);
      setData(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch trips:", err);
    } finally {
      setIsLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, total, isLoading, error, refetch: fetch };
}

export function useTrip(id: string | null) {
  const [data, setData] = useState<Trip | null>(null);
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

    getTrip(id)
      .then(setData)
      .catch((err) => {
        setError(err);
        console.error("Failed to fetch trip:", err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [id]);

  return { data, isLoading, error };
}

export function useTripStats() {
  const [data, setData] = useState<TripStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await getTripStats();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch trip stats:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function usePipeline() {
  const [data, setData] = useState<PipelineStage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await getPipeline();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch pipeline:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}
