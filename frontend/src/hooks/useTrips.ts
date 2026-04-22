/**
 * Custom hook for fetching and managing trip data
 * 
 * NOTE: These hooks use a delayed loading pattern to prevent flickering.
 * Loading states only appear if the fetch takes >300ms, otherwise data
 * appears instantly.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  getTrips,
  getTrip,
  getTripStats,
  getPipeline,
  updateTrip,
  type Trip,
  type TripStats,
  type PipelineStage,
} from "@/lib/api-client";

// Delay before showing loading state (prevents flicker on fast loads)
const LOADING_DELAY_MS = 300;

export function useTrips(params?: {
  state?: string;
  limit?: number;
  offset?: number;
}) {
  const [data, setData] = useState<Trip[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const hasFetched = useRef(false);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const paramsKey = JSON.stringify(params);

  const fetch = useCallback(async () => {
    // Clear any existing loading timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    // Only show loading after delay (prevents flicker)
    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(true);
    }, LOADING_DELAY_MS);

    setError(null);
    
    try {
      const result = await getTrips(params);
      setData(result.items);
      setTotal(result.total);
      hasFetched.current = true;
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch trips:", err);
    } finally {
      // Clear loading timeout and hide loading
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetch();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [fetch]);

  return { data, total, isLoading, error, refetch: fetch };
}

export function useTrip(id: string | null) {
  const [data, setData] = useState<Trip | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!id) {
      setData(null);
      setError(null);
      setIsLoading(false);
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
      return;
    }

    // Clear any existing loading timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    // Only show loading after delay
    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(true);
    }, LOADING_DELAY_MS);

    setError(null);

    getTrip(id)
      .then((trip) => {
        setData(trip);
      })
      .catch((err) => {
        setError(err);
        console.error("Failed to fetch trip:", err);
      })
      .finally(() => {
        if (loadingTimeoutRef.current) {
          clearTimeout(loadingTimeoutRef.current);
          loadingTimeoutRef.current = null;
        }
        setIsLoading(false);
      });

    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [id]);

  return { data, isLoading, error };
}

export function useTripStats() {
  const [data, setData] = useState<TripStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const fetch = useCallback(async () => {
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(true);
    }, LOADING_DELAY_MS);

    setError(null);
    
    try {
      const result = await getTripStats();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch trip stats:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useUpdateTrip() {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (id: string, data: Partial<Trip>): Promise<Trip | null> => {
    setIsSaving(true);
    setError(null);
    try {
      const updated = await updateTrip(id, data);
      return updated;
    } catch (err) {
      setError(err as Error);
      console.error("Failed to update trip:", err);
      return null;
    } finally {
      setIsSaving(false);
    }
  }, []);

  return { mutate, isSaving, error };
}

export function usePipeline() {
  const [data, setData] = useState<PipelineStage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const fetch = useCallback(async () => {
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(true);
    }, LOADING_DELAY_MS);

    setError(null);
    
    try {
      const result = await getPipeline();
      setData(result);
    } catch (err) {
      setError(err as Error);
      setData([]); // Reset to empty on error
      console.error("Failed to fetch pipeline:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}
