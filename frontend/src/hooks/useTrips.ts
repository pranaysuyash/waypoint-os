import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getTrips,
  getTrip,
  getTripStats,
  getPipeline,
  startPlanningTrip,
  updateTrip,
  type StartPlanningResponse,
  type Trip,
  type TripStats,
  type PipelineStage,
} from "@/lib/api-client";

const QK = {
  trips: (params?: { state?: string; limit?: number; offset?: number; view?: string }) =>
    ["trips", params] as const,
  trip: (id: string | null) => ["trips", id] as const,
  tripStats: () => ["trips", "stats"] as const,
  pipeline: () => ["trips", "pipeline"] as const,
};

const DEFAULT_STALE_TIME = 30_000;

export function useTrips(params?: {
  state?: string;
  limit?: number;
  offset?: number;
  view?: string;
}) {
  const { state, limit, offset, view } = params ?? {};

  const query = useQuery({
    queryKey: QK.trips(params),
    queryFn: () => getTrips({ state, limit, offset, view }),
    staleTime: DEFAULT_STALE_TIME,
  });

  return {
    data: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
}

export function useTrip(id: string | null) {
  const query = useQuery({
    queryKey: QK.trip(id),
    queryFn: () => getTrip(id!),
    enabled: !!id,
    staleTime: DEFAULT_STALE_TIME,
  });

  const queryClient = useQueryClient();

  const replaceTrip = (trip: Trip) => {
    queryClient.setQueryData<Trip>(QK.trip(id), trip);
  };

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
    replaceTrip,
  };
}

export function useTripStats() {
  const query = useQuery({
    queryKey: QK.tripStats(),
    queryFn: () => getTripStats(),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? null, isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useUpdateTrip() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Trip> }) =>
      updateTrip(id, data),
    onSuccess: (updated, { id }) => {
      if (updated) {
        queryClient.setQueryData<Trip>(QK.trip(id), updated);
      }
      queryClient.invalidateQueries({ queryKey: ["trips"] });
    },
  });

  const mutate = async (id: string, data: Partial<Trip>) => {
    return mutation.mutateAsync({ id, data });
  };

  return {
    mutate,
    isSaving: mutation.isPending,
    error: mutation.error as Error | null,
  };
}

export function useStartPlanning() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({
      id,
      agentId,
      agentName,
    }: {
      id: string;
      agentId: string;
      agentName: string;
    }) => startPlanningTrip(id, agentId, agentName),
    onSuccess: (_result, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["governance", "inboxTrips"] });
      queryClient.invalidateQueries({ queryKey: ["governance", "inboxStats"] });
      queryClient.invalidateQueries({ queryKey: QK.trip(id) });
    },
  });

  const mutate = async (
    id: string,
    agentId: string,
    agentName: string
  ): Promise<StartPlanningResponse> => {
    return mutation.mutateAsync({ id, agentId, agentName });
  };

  return {
    mutate,
    isStarting: mutation.isPending,
    error: mutation.error as Error | null,
  };
}

export function usePipeline() {
  const query = useQuery({
    queryKey: QK.pipeline(),
    queryFn: () => getPipeline(),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}
