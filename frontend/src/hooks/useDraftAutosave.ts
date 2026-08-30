'use client';

import { useEffect, useState, useCallback, useRef } from 'react';

export interface UseDraftAutosaveOptions<T> {
  key: string;
  data: T;
  debounceMs?: number;
  enabled?: boolean;
}

export function useDraftAutosave<T extends Record<string, unknown>>({
  key,
  data,
  debounceMs = 1000,
  enabled = true,
}: UseDraftAutosaveOptions<T>) {
  const [hasSavedDraft, setHasSavedDraft] = useState(false);
  const [savedDraft, setSavedDraft] = useState<T | null>(null);
  const storageKey = `waypoint_draft_${key}`;
  const isFirstRender = useRef(true);

  // Check for existing saved draft on initial mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as { data: T; timestamp: number };
        if (parsed && parsed.data) {
          // Verify that draft actually contains non-empty values
          const hasContent = Object.values(parsed.data).some((val) => {
            if (typeof val === 'string') return val.trim().length > 0;
            if (Array.isArray(val)) return val.length > 0;
            if (typeof val === 'object' && val !== null) return Object.keys(val).length > 0;
            return val !== undefined && val !== null;
          });

          if (hasContent) {
            setHasSavedDraft(true);
            setSavedDraft(parsed.data);
          }
        }
      }
    } catch {
      // Ignore localStorage parse errors
    }
  }, [storageKey]);

  // Debounced autosave
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (!enabled || typeof window === 'undefined') return;

    const timer = setTimeout(() => {
      try {
        const hasContent = Object.values(data).some((val) => {
          if (typeof val === 'string') return val.trim().length > 0;
          if (Array.isArray(val)) return val.length > 0;
          if (typeof val === 'object' && val !== null) return Object.keys(val).length > 0;
          return val !== undefined && val !== null;
        });

        if (hasContent) {
          const payload = {
            data,
            timestamp: Date.now(),
          };
          localStorage.setItem(storageKey, JSON.stringify(payload));
        }
      } catch {
        // Handle quota exceeded or private mode errors silently
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [data, debounceMs, enabled, storageKey]);

  const clearDraft = useCallback(() => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.removeItem(storageKey);
      setHasSavedDraft(false);
      setSavedDraft(null);
    } catch {
      // Ignore errors
    }
  }, [storageKey]);

  const dismissDraft = useCallback(() => {
    setHasSavedDraft(false);
  }, []);

  return {
    hasSavedDraft,
    savedDraft,
    clearDraft,
    dismissDraft,
  };
}
