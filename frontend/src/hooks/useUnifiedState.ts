import { useState, useEffect, useCallback } from 'react';

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
 * Mandate: Single Source of Truth for all dashboard metrics.
 * Fetches the unified system state and provides it to the UI.
 * Prevents local screen-specific calculations.
 */
export function useUnifiedState() {
  const [state, setState] = useState<UnifiedState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      // Use the local API route which handles proxying to Python backend
      const response = await fetch('/api/system/unified-state');
      if (!response.ok) {
        throw new Error(`Integrity fetch failed: ${response.statusText}`);
      }
      const data = await response.json();
      setState(data);
      setError(null);
    } catch (err: any) {
      console.error('Unified State Hook Error:', err);
      setError(err.message || 'Unknown integrity error');
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
    isConsistent: state?.integrity_meta.consistent ?? true
  };
}
