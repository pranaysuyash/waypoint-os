'use client';

/**
 * useTransientTimers - fire-and-forget UI-feedback timers (toasts, banner
 * resets) that are cancelled on unmount so they never call setState on an
 * unmounted component (FND-0282).
 *
 * Not for load-bearing timers with cleanup semantics of their own (the draft
 * auto-save debounce manages its own timer; the ensureDraftSaved
 * window.setTimeout(…, 0) deferral is intentionally uncleaned).
 */
import { useCallback, useEffect, useRef } from 'react';

export function useTransientTimers() {
  const timersRef = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((id) => clearTimeout(id));
      timers.clear();
    };
  }, []);

  const later = useCallback((fn: () => void, ms: number) => {
    const id = setTimeout(() => {
      timersRef.current.delete(id);
      fn();
    }, ms);
    timersRef.current.add(id);
  }, []);

  return { later };
}
