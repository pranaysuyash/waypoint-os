'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  actOnWorkItem,
  getWorkItems,
  type WorkItemAction,
  type WorkItemQueueResponse,
} from '@/lib/work-items-api';

/**
 * Classified incoming-work queue for the current agency. Mirrors the repo
 * staleTime convention (useTrips 30s): the queue is operator-glance data,
 * not real-time telemetry — the backend SSE lanes own liveness.
 */
export function useWorkItems(limit = 8, includeDone = false) {
  const query = useQuery({
    queryKey: ['work-items', limit, includeDone],
    queryFn: (): Promise<WorkItemQueueResponse> => getWorkItems(limit, includeDone),
    staleTime: 30_000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error as Error | null,
  };
}

/**
 * Outcome-state lifecycle mutation (map §14): claim / unclaim / dismiss /
 * resolve a queue item. Invalidates every work-items query on success so
 * panels re-fetch regardless of their limit key.
 */
export function useWorkItemAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, action, note }: { itemId: string; action: WorkItemAction; note?: string }) =>
      actOnWorkItem(itemId, action, note),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['work-items'] });
    },
  });
}
