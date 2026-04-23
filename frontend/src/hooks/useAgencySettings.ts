/**
 * Agency Settings Hook
 *
 * Fetches and manages agency configuration (profile + operational + autonomy).
 * Follows the same delayed-loading pattern as other data hooks.
 */

import { useState, useEffect, useCallback, useRef } from "react";

const LOADING_DELAY_MS = 300;

// =============================================================================
// TYPES
// =============================================================================

export interface AgencyProfile {
  agency_name: string;
  contact_email: string;
  contact_phone: string;
  logo_url: string;
  website: string;
}

export interface AgencyOperational {
  target_margin_pct: number;
  default_currency: string;
  operating_hours: { start: string; end: string };
  operating_days: string[];
  preferred_channels: string[];
  brand_tone: string;
}

export interface AgencyAutonomy {
  approval_gates: Record<string, "auto" | "review" | "block">;
  mode_overrides: Record<string, Record<string, string>>;
  auto_proceed_with_warnings: boolean;
  learn_from_overrides: boolean;
  min_proceed_confidence?: number;
  min_draft_confidence?: number;
}

export interface AgencySettings {
  agency_id: string;
  profile: AgencyProfile;
  operational: AgencyOperational;
  autonomy: AgencyAutonomy;
}

export interface UpdateOperationalPayload {
  agency_name?: string;
  contact_email?: string;
  contact_phone?: string;
  logo_url?: string;
  website?: string;
  target_margin_pct?: number;
  default_currency?: string;
  operating_hours_start?: string;
  operating_hours_end?: string;
  operating_days?: string[];
  preferred_channels?: string[];
  brand_tone?: string;
}

export interface UpdateAutonomyPayload {
  approval_gates?: Record<string, "auto" | "review" | "block">;
  mode_overrides?: Record<string, Record<string, string>>;
  auto_proceed_with_warnings?: boolean;
  learn_from_overrides?: boolean;
}

// =============================================================================
// HOOK: useAgencySettings
// =============================================================================

export function useAgencySettings() {
  const [data, setData] = useState<AgencySettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadSettings = useCallback(async () => {
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(true);
    }, LOADING_DELAY_MS);

    setError(null);

    try {
      const response = await fetch("/api/settings", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err as Error);
      console.error("Failed to fetch agency settings:", err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, [loadSettings]);

  return { data, isLoading, error, refetch: loadSettings };
}

// =============================================================================
// HOOK: useUpdateOperationalSettings
// =============================================================================

export function useUpdateOperationalSettings() {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (payload: UpdateOperationalPayload): Promise<AgencySettings | null> => {
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch("/api/settings/operational", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      setError(err as Error);
      console.error("Failed to update operational settings:", err);
      return null;
    } finally {
      setIsSaving(false);
    }
  }, []);

  return { mutate, isSaving, error };
}

// =============================================================================
// HOOK: useUpdateAutonomyPolicy
// =============================================================================

export function useUpdateAutonomyPolicy() {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (payload: UpdateAutonomyPayload): Promise<AgencyAutonomy | null> => {
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch("/api/settings/autonomy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      setError(err as Error);
      console.error("Failed to update autonomy policy:", err);
      return null;
    } finally {
      setIsSaving(false);
    }
  }, []);

  return { mutate, isSaving, error };
}
