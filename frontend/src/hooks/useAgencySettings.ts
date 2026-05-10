/**
 * Agency Settings Hook
 *
 * Fetches and manages agency configuration (profile + operational + autonomy).
 * Uses the centralized JSON API client (api-client.ts) for consistent
 * credential handling, retries, and error shaping.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getAgencySettings,
  updateAgencyOperational,
  updateAgencyAutonomy,
  type AgencySettings as AgencySettingsType,
  type AgencyAutonomy as AgencyAutonomyType,
  type UpdateOperationalPayload,
  type UpdateAutonomyPayload,
} from "@/lib/api-client";

const SETTINGS_QUERY_KEY = ["agency", "settings"] as const;
const SETTINGS_STALE_TIME_MS = 60_000;

export type AgencySettings = AgencySettingsType;
export type AgencyAutonomy = AgencyAutonomyType;
export type { UpdateOperationalPayload, UpdateAutonomyPayload };

export function useAgencySettings() {
  const query = useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: getAgencySettings,
    staleTime: SETTINGS_STALE_TIME_MS,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: (query.error as Error) ?? null,
    refetch: async () => {
      await query.refetch();
    },
  };
}

export function useUpdateOperationalSettings() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: UpdateOperationalPayload) => updateAgencyOperational(payload),
    onSuccess: (result) => {
      if (result) {
        queryClient.setQueryData(SETTINGS_QUERY_KEY, result);
      }
    },
  });

  const mutate = async (payload: UpdateOperationalPayload): Promise<AgencySettings | null> => {
    try {
      return await mutation.mutateAsync(payload);
    } catch (err) {
      console.error("Failed to update operational settings:", err);
      return null;
    }
  };

  return { mutate, isSaving: mutation.isPending, error: (mutation.error as Error) ?? null };
}

export function useUpdateAutonomyPolicy() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: UpdateAutonomyPayload) => updateAgencyAutonomy(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    },
  });

  const mutate = async (payload: UpdateAutonomyPayload): Promise<AgencyAutonomy | null> => {
    try {
      return await mutation.mutateAsync(payload);
    } catch (err) {
      console.error("Failed to update autonomy policy:", err);
      return null;
    }
  };

  return { mutate, isSaving: mutation.isPending, error: (mutation.error as Error) ?? null };
}
