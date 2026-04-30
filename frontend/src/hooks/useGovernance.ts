import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  TripReview,
  ReviewFilters,
  ReviewActionRequest,
  InsightsSummary,
  TimeRange,
  StageMetrics,
  TeamMemberMetrics,
  BottleneckAnalysis,
  RevenueMetrics,
  TeamMember,
  WorkloadDistribution,
  InboxTrip,
  InboxFilters,
  BulkActionRequest,
  AssignmentRequest,
  OperationalAlert,
} from "@/types/governance";
import * as governanceApi from "@/lib/governance-api";

const QK = {
  reviews: (f?: ReviewFilters) => ["governance", "reviews", f] as const,
  insightsSummary: (t: TimeRange) => ["governance", "insightsSummary", t] as const,
  pipelineMetrics: (t: TimeRange) => ["governance", "pipelineMetrics", t] as const,
  teamMetrics: (t: TimeRange) => ["governance", "teamMetrics", t] as const,
  bottleneckAnalysis: (t: TimeRange) => ["governance", "bottleneckAnalysis", t] as const,
  revenueMetrics: (t: TimeRange) => ["governance", "revenueMetrics", t] as const,
  operationalAlerts: () => ["governance", "operationalAlerts"] as const,
  teamMembers: () => ["governance", "teamMembers"] as const,
  workloadDistribution: () => ["governance", "workloadDistribution"] as const,
  inboxTrips: (f?: InboxFilters, p?: number, l?: number) =>
    ["governance", "inboxTrips", f, p, l] as const,
  inboxStats: () => ["governance", "inboxStats"] as const,
};

const DEFAULT_STALE_TIME = 30_000;

export function useReviews(filters?: ReviewFilters) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: QK.reviews(filters),
    queryFn: () => governanceApi.getReviews(filters),
    staleTime: DEFAULT_STALE_TIME,
  });

  const submitAction = useMutation({
    mutationFn: (request: ReviewActionRequest) =>
      governanceApi.submitReviewAction(request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["governance", "reviews"] }),
  });

  const bulkAction = useMutation({
    mutationFn: (requests: ReviewActionRequest[]) =>
      governanceApi.bulkReviewAction(requests),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["governance", "reviews"] }),
  });

  return {
    data: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
    submitAction: submitAction.mutateAsync,
    bulkAction: bulkAction.mutateAsync,
  };
}

export function useInsightsSummary(timeRange: TimeRange = "30d") {
  const query = useQuery({
    queryKey: QK.insightsSummary(timeRange),
    queryFn: () => governanceApi.getInsightsSummary(timeRange),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? null, isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function usePipelineMetrics(timeRange: TimeRange = "30d") {
  const query = useQuery({
    queryKey: QK.pipelineMetrics(timeRange),
    queryFn: () => governanceApi.getPipelineMetrics(timeRange),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useTeamMetrics(timeRange: TimeRange = "30d") {
  const query = useQuery({
    queryKey: QK.teamMetrics(timeRange),
    queryFn: () => governanceApi.getTeamMetrics(timeRange),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useBottleneckAnalysis(timeRange: TimeRange = "30d") {
  const query = useQuery({
    queryKey: QK.bottleneckAnalysis(timeRange),
    queryFn: () => governanceApi.getBottleneckAnalysis(timeRange),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useRevenueMetrics(timeRange: TimeRange = "30d") {
  const query = useQuery({
    queryKey: QK.revenueMetrics(timeRange),
    queryFn: () => governanceApi.getRevenueMetrics(timeRange),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? null, isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useOperationalAlerts() {
  const query = useQuery({
    queryKey: QK.operationalAlerts(),
    queryFn: () => governanceApi.getOperationalAlerts(),
    staleTime: DEFAULT_STALE_TIME,
  });

  const queryClient = useQueryClient();

  const dismiss = async (id: string) => {
    await governanceApi.dismissAlert(id);
    queryClient.setQueryData<OperationalAlert[]>(QK.operationalAlerts(), (prev) =>
      prev?.filter((a) => a.id !== id)
    );
  };

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch, dismiss };
}

export function useTeamMembers() {
  const query = useQuery({
    queryKey: QK.teamMembers(),
    queryFn: () => governanceApi.getTeamMembers(),
    staleTime: DEFAULT_STALE_TIME,
  });

  const queryClient = useQueryClient();

  const inviteMember = async (data: { email: string; name: string; role: string; capacity?: number }) => {
    const result = await governanceApi.inviteTeamMember(data);
    queryClient.invalidateQueries({ queryKey: QK.teamMembers() });
    return result;
  };

  const updateMember = async (id: string, data: Partial<TeamMember>) => {
    const result = await governanceApi.updateTeamMember(id, data);
    queryClient.invalidateQueries({ queryKey: QK.teamMembers() });
    return result;
  };

  const deactivateMember = async (id: string) => {
    const result = await governanceApi.deactivateTeamMember(id);
    queryClient.invalidateQueries({ queryKey: QK.teamMembers() });
    return result;
  };

  return {
    data: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
    inviteMember,
    updateMember,
    deactivateMember,
  };
}

export function useWorkloadDistribution() {
  const query = useQuery({
    queryKey: QK.workloadDistribution(),
    queryFn: () => governanceApi.getWorkloadDistribution(),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useInboxTrips(
  filters?: InboxFilters,
  page: number = 1,
  limit: number = 20
) {
  const query = useQuery({
    queryKey: QK.inboxTrips(filters, page, limit),
    queryFn: () => governanceApi.getInboxTrips(filters, page, limit),
    staleTime: DEFAULT_STALE_TIME,
  });

  const queryClient = useQueryClient();

  const assignTrips = async (request: AssignmentRequest) => {
    const result = await governanceApi.assignTrips(request);
    queryClient.invalidateQueries({ queryKey: ["governance", "inboxTrips"] });
    queryClient.invalidateQueries({ queryKey: QK.inboxStats() });
    return result;
  };

  const bulkAction = async (request: BulkActionRequest) => {
    const result = await governanceApi.bulkInboxAction(request);
    queryClient.invalidateQueries({ queryKey: ["governance", "inboxTrips"] });
    queryClient.invalidateQueries({ queryKey: QK.inboxStats() });
    return result;
  };

  const snoozeTrip = async (tripId: string, snoozeUntil: string) => {
    const result = await governanceApi.snoozeTrip(tripId, snoozeUntil);
    queryClient.invalidateQueries({ queryKey: ["governance", "inboxTrips"] });
    queryClient.invalidateQueries({ queryKey: QK.inboxStats() });
    return result;
  };

  return {
    data: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    hasMore: query.data?.hasMore ?? false,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
    assignTrips,
    bulkAction,
    snoozeTrip,
  };
}

export function useInboxStats() {
  const query = useQuery({
    queryKey: QK.inboxStats(),
    queryFn: () => governanceApi.getInboxStats(),
    staleTime: DEFAULT_STALE_TIME,
  });

  return { data: query.data ?? null, isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}
