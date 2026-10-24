'use client';

import { useQuery } from '@tanstack/react-query';
import { getWorkItems, type WorkItemQueueResponse } from '@/lib/work-items-api';

/**
 * Classified incoming-work queue for the current agency. Mirrors the repo
 * staleTime convention (useTrips 30s): the queue is operator-glance data,
 * not real-time telemetry — the backend SSE lanes own liveness.
 */
export function useWorkItems(limit = 8) {
  const query = useQuery({
    queryKey: ['work-items', limit],
    queryFn: (): Promise<WorkItemQueueResponse> => getWorkItems(limit),
    staleTime: 30_000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error as Error | null,
  };
}
