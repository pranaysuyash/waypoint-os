/**
 * Governance Hooks
 * 
 * Custom hooks for governance features:
 * - Reviews and approvals
 * - Analytics and insights
 * - Team management
 * - Inbox operations
 * 
 * All hooks use delayed loading pattern to prevent flickering.
 */

import { useState, useEffect, useCallback, useRef } from "react";
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
} from "@/types/governance";
import * as governanceApi from "@/lib/governance-api";

// Delay before showing loading state (prevents flicker on fast loads)
const LOADING_DELAY_MS = 300;

// ============================================================================
// REVIEWS HOOK
// ============================================================================

export function useReviews(filters?: ReviewFilters) {
  const [data, setData] = useState<TripReview[]>([]);
  const [total, setTotal] = useState(0);
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
      const result = await governanceApi.getReviews(filters);
      setData(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch reviews:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetch();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [fetch]);

  const submitAction = useCallback(async (request: ReviewActionRequest) => {
    return governanceApi.submitReviewAction(request);
  }, []);

  const bulkAction = useCallback(async (requests: ReviewActionRequest[]) => {
    return governanceApi.bulkReviewAction(requests);
  }, []);

  return { data, total, isLoading, error, refetch: fetch, submitAction, bulkAction };
}

// ============================================================================
// INSIGHTS HOOKS
// ============================================================================

export function useInsightsSummary(timeRange: TimeRange = "30d") {
  const [data, setData] = useState<InsightsSummary | null>(null);
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
      const result = await governanceApi.getInsightsSummary(timeRange);
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch insights summary:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [timeRange]);

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

export function usePipelineMetrics(timeRange: TimeRange = "30d") {
  const [data, setData] = useState<StageMetrics[]>([]);
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
      const result = await governanceApi.getPipelineMetrics(timeRange);
      setData(result);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch pipeline metrics:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [timeRange]);

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

export function useTeamMetrics(timeRange: TimeRange = "30d") {
  const [data, setData] = useState<TeamMemberMetrics[]>([]);
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
      const result = await governanceApi.getTeamMetrics(timeRange);
      setData(result);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch team metrics:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [timeRange]);

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

export function useBottleneckAnalysis(timeRange: TimeRange = "30d") {
  const [data, setData] = useState<BottleneckAnalysis[]>([]);
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
      const result = await governanceApi.getBottleneckAnalysis(timeRange);
      setData(result);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch bottleneck analysis:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [timeRange]);

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

export function useRevenueMetrics(timeRange: TimeRange = "30d") {
  const [data, setData] = useState<RevenueMetrics | null>(null);
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
      const result = await governanceApi.getRevenueMetrics(timeRange);
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch revenue metrics:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [timeRange]);

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

// ============================================================================
// TEAM MANAGEMENT HOOKS
// ============================================================================

export function useTeamMembers() {
  const [data, setData] = useState<TeamMember[]>([]);
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
      const result = await governanceApi.getTeamMembers();
      setData(result);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch team members:", err);
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

  const inviteMember = useCallback(async (data: {
    email: string;
    name: string;
    role: string;
    capacity?: number;
  }) => {
    return governanceApi.inviteTeamMember(data);
  }, []);

  const updateMember = useCallback(async (id: string, data: Partial<TeamMember>) => {
    return governanceApi.updateTeamMember(id, data);
  }, []);

  const deactivateMember = useCallback(async (id: string) => {
    return governanceApi.deactivateTeamMember(id);
  }, []);

  return {
    data,
    isLoading,
    error,
    refetch: fetch,
    inviteMember,
    updateMember,
    deactivateMember,
  };
}

export function useWorkloadDistribution() {
  const [data, setData] = useState<WorkloadDistribution[]>([]);
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
      const result = await governanceApi.getWorkloadDistribution();
      setData(result);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch workload distribution:", err);
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

// ============================================================================
// INBOX HOOKS
// ============================================================================

export function useInboxTrips(
  filters?: InboxFilters,
  page: number = 1,
  limit: number = 20
) {
  const [data, setData] = useState<InboxTrip[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
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
      const result = await governanceApi.getInboxTrips(filters, page, limit);
      setData(result.items);
      setTotal(result.total);
      setHasMore(result.hasMore);
    } catch (err) {
      setError(err as Error);
      setData([]);
      console.error("Failed to fetch inbox trips:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, [filters, page, limit]);

  useEffect(() => {
    fetch();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [fetch]);

  const assignTrips = useCallback(async (request: AssignmentRequest) => {
    return governanceApi.assignTrips(request);
  }, []);

  const bulkAction = useCallback(async (request: BulkActionRequest) => {
    return governanceApi.bulkInboxAction(request);
  }, []);

  const snoozeTrip = useCallback(async (tripId: string, snoozeUntil: string) => {
    return governanceApi.snoozeTrip(tripId, snoozeUntil);
  }, []);

  return {
    data,
    total,
    hasMore,
    isLoading,
    error,
    refetch: fetch,
    assignTrips,
    bulkAction,
    snoozeTrip,
  };
}

export function useInboxStats() {
  const [data, setData] = useState<{
    total: number;
    unassigned: number;
    critical: number;
    atRisk: number;
  } | null>(null);
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
      const result = await governanceApi.getInboxStats();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch inbox stats:", err);
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
