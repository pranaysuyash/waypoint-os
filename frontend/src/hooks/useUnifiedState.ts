import { useQuery } from "@tanstack/react-query";

export interface UnifiedState {
  canonical_total: number;
  stages: Record<string, number>;
  sla_breached: number;
  orphans: any[];
  integrity_meta: {
    sum_stages: number;
    orphan_count: number;
    consistent: boolean;
  };
  timestamp?: string;
  meta?: {
    source: string;
  };
}

/**
 * useUnifiedState Hook
 *
 * Fetches the unified system state from the backend.
 * Keeps raw fetch() (not api-client.ts) because this is a polling endpoint.
 * Always passes credentials: "include" so auth cookies travel securely.
 * cache: "no-store" prevents stale dashboard data.
 */
const QK = {
  unifiedState: () => ["system", "unified-state"] as const,
};

async function getUnifiedState(): Promise<UnifiedState> {
  const response = await fetch("/api/system/unified-state", {
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    throw new Error(`Integrity fetch failed: ${response.statusText}`);
  }

  return (await response.json()) as UnifiedState;
}

export function useUnifiedState() {
  const query = useQuery({
    queryKey: QK.unifiedState(),
    queryFn: getUnifiedState,
    staleTime: 30_000,
  });

  return {
    state: query.data ?? null,
    loading: query.isLoading,
    error: (query.error as Error | null)?.message ?? null,
    refresh: query.refetch,
    isConsistent: query.data?.integrity_meta.consistent ?? true,
  };
}
