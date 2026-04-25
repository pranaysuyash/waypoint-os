/**
 * Agency Settings Hook
 *
 * Fetches and manages agency configuration (profile + operational + autonomy).
 * Uses the centralized JSON API client (api-client.ts) for consistent
 * credential handling, retries, and error shaping.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  getAgencySettings,
  updateAgencyOperational,
  updateAgencyAutonomy,
  type AgencySettings as AgencySettingsType,
  type AgencyAutonomy as AgencyAutonomyType,
  type UpdateOperationalPayload,
  type UpdateAutonomyPayload,
} from "@/lib/api-client";

const LOADING_DELAY_MS = 300;

export type AgencySettings = AgencySettingsType;
export type AgencyAutonomy = AgencyAutonomyType;
export type { UpdateOperationalPayload, UpdateAutonomyPayload };

export function useAgencySettings() {
  const [data, setData] = useState<AgencySettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadSettings = useCallback(async () => {
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(true);
    }, LOADING_DELAY_MS);

    setError(null);

    try {
      const result = await getAgencySettings();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch agency settings:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [loadSettings]);

  return { data, isLoading, error, refetch: loadSettings };
}

export function useUpdateOperationalSettings() {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(
    async (payload: UpdateOperationalPayload): Promise<AgencySettings | null> => {
      setIsSaving(true);
      setError(null);

      try {
        const result = await updateAgencyOperational(payload);
        return result;
      } catch (err) {
        setError(err as Error);
        console.error("Failed to update operational settings:", err);
        return null;
      } finally {
        setIsSaving(false);
      }
    },
    []
  );

  return { mutate, isSaving, error };
}

export function useUpdateAutonomyPolicy() {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(
    async (payload: UpdateAutonomyPayload): Promise<AgencyAutonomy | null> => {
      setIsSaving(true);
      setError(null);

      try {
        const result = await updateAgencyAutonomy(payload);
        return result;
      } catch (err) {
        setError(err as Error);
        console.error("Failed to update autonomy policy:", err);
        return null;
      } finally {
        setIsSaving(false);
      }
    },
    []
  );

  return { mutate, isSaving, error };
}
