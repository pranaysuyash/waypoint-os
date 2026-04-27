import { useState, useEffect, useCallback } from "react";

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
export function useUnifiedState() {
  const [state, setState] = useState<UnifiedState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/system/unified-state", {
        // Explicit cookie-auth for cross-subdomain safety.
        credentials: "include",
        cache: "no-store",
      });
      if (!response.ok) {
        // 401 = unauthenticated, don't throw noisy errors during redirect-to-login
        if (response.status === 401) {
          setError("Unauthorized");
          return;
        }
        throw new Error(`Integrity fetch failed: ${response.statusText}`);
      }
      const data = (await response.json()) as UnifiedState;
      setState(data);
      setError(null);
    } catch (err: any) {
      // Skip console noise for 401 — AuthProvider handles redirect
      if (err.message !== "Unauthorized") {
        console.error("Unified State Hook Error:", err);
      }
      setError(err.message || "Unknown integrity error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    state,
    loading,
    error,
    refresh,
    isConsistent: state?.integrity_meta.consistent ?? true,
  };
}
