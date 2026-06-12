'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createSeasonalCampaign,
  updateSeasonalCampaign,
  deleteSeasonalCampaign,
  listSeasonalCampaigns,
  simulateSeasonalCampaign,
  preflightSeasonalCampaign,
  dispatchSeasonalCampaign,
  type SeasonalCampaign,
  type SeasonalCampaignListResponse,
  type CreateSeasonalCampaignRequest,
  type UpdateSeasonalCampaignRequest,
  type SimulateSeasonalCampaignResponse,
  type SeasonPreflightResponse,
  type SeasonDispatchResponse,
} from '@/lib/api-client';

const SEASONAL_CAMPAIGNS_QUERY_KEY = ['seasonal', 'campaigns'] as const;
const STALE_TIME_MS = 45_000;

export type { SeasonalCampaign, SeasonalCampaignListResponse, CreateSeasonalCampaignRequest, UpdateSeasonalCampaignRequest, SimulateSeasonalCampaignResponse, SeasonPreflightResponse, SeasonDispatchResponse };

export function useSeasonalCampaigns() {
  const query = useQuery({
    queryKey: SEASONAL_CAMPAIGNS_QUERY_KEY,
    queryFn: listSeasonalCampaigns,
    staleTime: STALE_TIME_MS,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  return {
    campaigns: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: (query.error as Error) ?? null,
    refetch: async () => {
      await query.refetch();
    },
  };
}

function invalidateCampaigns(queryClient: ReturnType<typeof useQueryClient>) {
  return queryClient.invalidateQueries({ queryKey: SEASONAL_CAMPAIGNS_QUERY_KEY });
}

export function useCreateSeasonalCampaign() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: CreateSeasonalCampaignRequest) => createSeasonalCampaign(payload),
    onSuccess: () => {
      invalidateCampaigns(queryClient);
    },
  });

  const mutate = async (payload: CreateSeasonalCampaignRequest): Promise<SeasonalCampaign | null> => {
    try {
      return await mutation.mutateAsync(payload);
    } catch (err) {
      console.error('Failed to create seasonal campaign:', err);
      return null;
    }
  };

  return {
    mutate,
    isSaving: mutation.isPending,
    error: (mutation.error as Error) ?? null,
  };
}

export function useUpdateSeasonalCampaign() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: { planId: string; request: UpdateSeasonalCampaignRequest }) =>
      updateSeasonalCampaign(payload.planId, payload.request),
    onSuccess: () => {
      invalidateCampaigns(queryClient);
    },
  });

  const mutate = async (planId: string, request: UpdateSeasonalCampaignRequest): Promise<SeasonalCampaign | null> => {
    try {
      return await mutation.mutateAsync({ planId, request });
    } catch (err) {
      console.error('Failed to update seasonal campaign:', err);
      return null;
    }
  };

  return {
    mutate,
    isSaving: mutation.isPending,
    error: (mutation.error as Error) ?? null,
  };
}

export function useDeleteSeasonalCampaign() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (planId: string) => deleteSeasonalCampaign(planId),
    onSuccess: () => {
      invalidateCampaigns(queryClient);
    },
  });

  const mutate = async (planId: string): Promise<boolean> => {
    try {
      const result = await mutation.mutateAsync(planId);
      return result?.ok ?? false;
    } catch (err) {
      console.error('Failed to delete seasonal campaign:', err);
      return false;
    }
  };

  return {
    mutate,
    isSaving: mutation.isPending,
    error: (mutation.error as Error) ?? null,
  };
}

export function useSimulateSeasonalCampaign() {
  const mutation = useMutation({
    mutationFn: ({ planId, scenario }: { planId: string; scenario: string }) =>
      simulateSeasonalCampaign(planId, scenario),
  });

  const mutate = async (
    planId: string,
    scenario = 'baseline',
  ): Promise<SimulateSeasonalCampaignResponse | null> => {
    try {
      return await mutation.mutateAsync({ planId, scenario });
    } catch (err) {
      console.error('Failed to run campaign simulation:', err);
      return null;
    }
  };

  return {
    mutate,
    isRunning: mutation.isPending,
    error: (mutation.error as Error) ?? null,
  };
}

export function usePreflightSeasonalCampaign() {
  const mutation = useMutation({
    mutationFn: (planId: string) => preflightSeasonalCampaign(planId),
  });

  const mutate = async (planId: string): Promise<SeasonPreflightResponse | null> => {
    try {
      return await mutation.mutateAsync(planId);
    } catch (err) {
      console.error('Failed to run preflight:', err);
      return null;
    }
  };

  return {
    mutate,
    isRunning: mutation.isPending,
    error: (mutation.error as Error) ?? null,
  };
}

export function useDispatchSeasonalCampaign() {
  const mutation = useMutation({
    mutationFn: ({ planId, dryRun }: { planId: string; dryRun: boolean }) =>
      dispatchSeasonalCampaign(planId, dryRun),
  });

  const mutate = async (
    planId: string,
    dryRun: boolean,
  ): Promise<SeasonDispatchResponse | null> => {
    try {
      return await mutation.mutateAsync({ planId, dryRun });
    } catch (err) {
      console.error('Failed to dispatch campaign:', err);
      return null;
    }
  };

  return {
    mutate,
    isRunning: mutation.isPending,
    error: (mutation.error as Error) ?? null,
  };
}
