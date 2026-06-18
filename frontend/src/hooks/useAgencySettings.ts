/**
 * Agency Settings Hook
 *
 * Fetches and manages agency configuration (profile + operational + autonomy).
 * Uses the centralized JSON API client (api-client.ts) for consistent
 * credential handling, retries, and error shaping.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getAgencySettings,
  updateAgencyOperational,
  updateAgencyAutonomy,
  updateAgencySeasonal,
  type AgencySettings as AgencySettingsType,
  type AgencyAutonomy as AgencyAutonomyType,
  type AgencySeasonal as AgencySeasonalType,
  type UpdateOperationalPayload,
  type UpdateAutonomyPayload,
  type UpdateSeasonalPayload,
} from "@/lib/api-client";

const SETTINGS_QUERY_KEY = ["agency", "settings"] as const;
const SETTINGS_STALE_TIME_MS = 60_000;

export type AgencySettings = AgencySettingsType;
export type AgencyAutonomy = AgencyAutonomyType;
export type AgencySeasonal = AgencySeasonalType;
export type { UpdateOperationalPayload, UpdateAutonomyPayload, UpdateSeasonalPayload };

const VALID_AUTONOMY_ACTIONS = new Set(["auto", "review", "block"]);

function isRecordLike(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringRecord(value: unknown): value is Record<string, string> {
  if (!isRecordLike(value)) return false;
  return Object.values(value).every((item) => typeof item === "string");
}

function isStringToStringRecord(value: unknown): value is Record<string, Record<string, string>> {
  if (!isRecordLike(value)) return false;
  return Object.values(value).every(isStringRecord);
}

function isStringToBooleanRecord(value: unknown): value is Record<string, boolean> {
  if (!isRecordLike(value)) return false;
  return Object.values(value).every((item) => typeof item === "boolean");
}

function isStringToNumberRecord(value: unknown): value is Record<string, number> {
  if (!isRecordLike(value)) return false;
  return Object.values(value).every((item) => typeof item === "number");
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function asAgencySettings(value: unknown): AgencySettings | null {
  if (!isRecordLike(value)) return null;

  const seasonal = value.seasonal;
  const profile = value.profile;
  const operational = value.operational;
  const autonomy = value.autonomy;

  const approvalGates = isRecordLike(autonomy)
    ? isRecordLike((autonomy as Record<string, unknown>).approval_gates)
      ? isRecordLike(autonomy.approval_gates)
        ? Object.values(autonomy.approval_gates).every((item) => typeof item === "string" && VALID_AUTONOMY_ACTIONS.has(item))
        : false
      : false
    : false;

  const VALID_TIERS = new Set(["starter", "pro", "enterprise"]);

  if (
    typeof value.agency_id !== "string" ||
    (value.tier !== undefined && !VALID_TIERS.has(value.tier as string)) ||
    !isRecordLike(profile) ||
    !isRecordLike(operational) ||
    !isRecordLike(autonomy) ||
    !isRecordLike(seasonal) ||
    typeof profile.agency_name !== "string" ||
    typeof profile.sub_brand !== "string" ||
    typeof profile.plan_label !== "string" ||
    typeof profile.contact_email !== "string" ||
    typeof profile.contact_phone !== "string" ||
    typeof profile.logo_url !== "string" ||
    typeof profile.website !== "string" ||
    typeof operational.target_margin_pct !== "number" ||
    typeof operational.default_currency !== "string" ||
    !isRecordLike(operational.operating_hours) ||
    typeof operational.operating_hours.start !== "string" ||
    typeof operational.operating_hours.end !== "string" ||
    !isStringArray(operational.operating_days) ||
    !isStringArray(operational.preferred_channels) ||
    typeof operational.brand_tone !== "string" ||
    !isRecordLike(autonomy.mode_overrides) ||
    !isStringToStringRecord(autonomy.mode_overrides) ||
    !approvalGates ||
    typeof autonomy.auto_proceed_with_warnings !== "boolean" ||
    typeof autonomy.learn_from_overrides !== "boolean" ||
    typeof autonomy.auto_reprocess_on_edit !== "boolean" ||
    typeof autonomy.allow_explicit_reassess !== "boolean" ||
    !isStringToBooleanRecord(autonomy.auto_reprocess_stages) ||
    typeof autonomy.min_proceed_confidence !== "number" ||
    typeof autonomy.min_draft_confidence !== "number" ||
    typeof seasonal.active_seasons_enabled !== "boolean" ||
    typeof seasonal.default_quarter_window_months !== "number" ||
    !isStringToNumberRecord(seasonal.channel_mix) ||
    typeof seasonal.weather_risk_threshold !== "number" ||
    typeof seasonal.budget_guardrail_multiplier !== "number" ||
    typeof seasonal.micro_seasonality_window_days !== "number" ||
    typeof seasonal.quarterly_recalibration_enabled !== "boolean" ||
    !isStringArray(seasonal.prelaunch_blocklist)
  ) {
    return null;
  }

  return value as AgencySettingsType;
}

function asAgencyAutonomy(value: unknown): AgencyAutonomyType | null {
  if (!isRecordLike(value)) return null;

  if (
    !isRecordLike(value.approval_gates) ||
    !isRecordLike(value.mode_overrides) ||
    typeof value.auto_proceed_with_warnings !== "boolean" ||
    typeof value.learn_from_overrides !== "boolean" ||
    typeof value.auto_reprocess_on_edit !== "boolean" ||
    typeof value.allow_explicit_reassess !== "boolean" ||
    !isStringToBooleanRecord(value.auto_reprocess_stages) ||
    typeof value.min_proceed_confidence !== "number" ||
    typeof value.min_draft_confidence !== "number" ||
    !Object.values(value.approval_gates).every((item) => typeof item === "string" && VALID_AUTONOMY_ACTIONS.has(item))
  ) {
    return null;
  }

  return {
    approval_gates: value.approval_gates as Record<string, string>,
    mode_overrides: value.mode_overrides as Record<string, Record<string, string>>,
    auto_proceed_with_warnings: value.auto_proceed_with_warnings,
    learn_from_overrides: value.learn_from_overrides,
    auto_reprocess_on_edit: value.auto_reprocess_on_edit,
    allow_explicit_reassess: value.allow_explicit_reassess,
    auto_reprocess_stages: value.auto_reprocess_stages,
    min_proceed_confidence: value.min_proceed_confidence,
    min_draft_confidence: value.min_draft_confidence,
  };
}

function asAgencyOperational(value: unknown): {
  profile: {
    agency_name: string;
    sub_brand: string;
    plan_label: string;
    contact_email: string;
    contact_phone: string;
    logo_url: string;
    website: string;
  };
  operational: {
    target_margin_pct: number;
    default_currency: string;
    operating_hours: {
      start: string;
      end: string;
    };
    operating_days: string[];
    preferred_channels: string[];
    brand_tone: string;
  };
} | null {
  if (!isRecordLike(value)) return null;
  const profile = value.profile;
  const operational = value.operational;

  if (
    !isRecordLike(profile) ||
    !isRecordLike(operational) ||
    typeof profile.agency_name !== "string" ||
    typeof profile.sub_brand !== "string" ||
    typeof profile.plan_label !== "string" ||
    typeof profile.contact_email !== "string" ||
    typeof profile.contact_phone !== "string" ||
    typeof profile.logo_url !== "string" ||
    typeof profile.website !== "string" ||
    typeof operational.target_margin_pct !== "number" ||
    typeof operational.default_currency !== "string" ||
    !isRecordLike(operational.operating_hours) ||
    typeof operational.operating_hours.start !== "string" ||
    typeof operational.operating_hours.end !== "string" ||
    !isStringArray(operational.operating_days) ||
    !isStringArray(operational.preferred_channels) ||
    typeof operational.brand_tone !== "string"
  ) {
    return null;
  }

  return {
    profile: profile as {
      agency_name: string;
      sub_brand: string;
      plan_label: string;
      contact_email: string;
      contact_phone: string;
      logo_url: string;
      website: string;
    },
    operational: operational as {
      target_margin_pct: number;
      default_currency: string;
      operating_hours: {
        start: string;
        end: string;
      };
      operating_days: string[];
      preferred_channels: string[];
      brand_tone: string;
    },
  };
}

function asAgencySeasonal(value: unknown): AgencySeasonalType | null {
  if (!isRecordLike(value)) return null;

  if (
    typeof value.active_seasons_enabled !== "boolean" ||
    typeof value.default_quarter_window_months !== "number" ||
    !isStringToNumberRecord(value.channel_mix) ||
    typeof value.weather_risk_threshold !== "number" ||
    typeof value.budget_guardrail_multiplier !== "number" ||
    typeof value.micro_seasonality_window_days !== "number" ||
    typeof value.quarterly_recalibration_enabled !== "boolean" ||
    !isStringArray(value.prelaunch_blocklist)
  ) {
    return null;
  }

  return value as AgencySeasonalType;
}

function upsertAgencySettings(
  queryClient: ReturnType<typeof useQueryClient>,
  value: unknown
): AgencySettings | null {
  const normalized = asAgencySettings(value);
  if (queryClient && normalized) {
    queryClient.setQueryData<AgencySettings | null>(SETTINGS_QUERY_KEY, normalized);
  }
  return normalized;
}

async function refreshAgencySettingsFromServer(
  queryClient: ReturnType<typeof useQueryClient>
): Promise<AgencySettings | null> {
  if (queryClient.getQueryData<AgencySettings>(SETTINGS_QUERY_KEY)) {
    queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    return null;
  }

  try {
    const fresh = await queryClient.fetchQuery({
      queryKey: [...SETTINGS_QUERY_KEY, "refresh"],
      queryFn: getAgencySettings,
    });
    return upsertAgencySettings(queryClient, fresh);
  } catch (error) {
    console.warn("Failed to refresh agency settings after partial update", {
      source: "settings-update-refresh",
      error,
    });
    queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    return null;
  }
}

function upsertAgencyAutonomyPatch(
  queryClient: ReturnType<typeof useQueryClient>,
  value: unknown
): AgencySettings | null {
  const autonomy = asAgencyAutonomy(value);
  if (!autonomy) return null;
  const current = queryClient.getQueryData<AgencySettings>(SETTINGS_QUERY_KEY);
  if (!current) return null;

  return upsertAgencySettings(queryClient, {
    ...current,
    autonomy,
  });
}

function upsertAgencyOperationalPatch(
  queryClient: ReturnType<typeof useQueryClient>,
  value: unknown
): AgencySettings | null {
  const operational = asAgencyOperational(value);
  if (!operational) return null;
  const current = queryClient.getQueryData<AgencySettings>(SETTINGS_QUERY_KEY);
  if (!current) return null;

  return upsertAgencySettings(queryClient, {
    ...current,
    profile: operational.profile,
    operational: operational.operational,
  });
}

function upsertAgencySeasonalPatch(
  queryClient: ReturnType<typeof useQueryClient>,
  value: unknown
): AgencySettings | null {
  const seasonal = asAgencySeasonal(value);
  if (!seasonal) return null;
  const current = queryClient.getQueryData<AgencySettings>(SETTINGS_QUERY_KEY);
  if (!current) return null;

  return upsertAgencySettings(queryClient, {
    ...current,
    seasonal,
  });
}

export function useAgencySettings() {
  const query = useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: getAgencySettings,
    staleTime: SETTINGS_STALE_TIME_MS,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  return {
    data: asAgencySettings(query.data),
    isLoading: query.isLoading,
    error: (query.error as Error) ?? null,
    refetch: async () => {
      await query.refetch();
    },
  };
}

export function useUpdateOperationalSettings() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: UpdateOperationalPayload) => updateAgencyOperational(payload),
    onSuccess: (result) => {
      if (!upsertAgencySettings(queryClient, result) && !upsertAgencyOperationalPatch(queryClient, result)) {
        console.warn("Ignoring malformed operational settings response", {
          source: "settings-update-operational",
        });
        queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
      }
    },
  });

  const mutate = async (payload: UpdateOperationalPayload): Promise<AgencySettings | null> => {
    try {
      const raw = await mutation.mutateAsync(payload);
      const upserted = upsertAgencySettings(queryClient, raw);
      if (upserted) {
        return upserted;
      }
      const patched = upsertAgencyOperationalPatch(queryClient, raw);
      return patched ?? (await refreshAgencySettingsFromServer(queryClient));
    } catch (err) {
      console.error("Failed to update operational settings:", err);
      return null;
    }
  };

  return { mutate, isSaving: mutation.isPending, error: (mutation.error as Error) ?? null };
}

export function useUpdateAutonomyPolicy() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: UpdateAutonomyPayload) => updateAgencyAutonomy(payload),
    onSuccess: (result) => {
      if (!upsertAgencySettings(queryClient, result) && !upsertAgencyAutonomyPatch(queryClient, result)) {
        console.warn("Ignoring malformed autonomy update response, falling back to refetch", {
          source: "settings-update-autonomy",
        });
        queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
      }
    },
  });

  const mutate = async (payload: UpdateAutonomyPayload): Promise<AgencySettings | null> => {
    try {
      const raw = await mutation.mutateAsync(payload);
      const upserted = upsertAgencySettings(queryClient, raw);
      if (upserted) {
        return upserted;
      }
      const patched = upsertAgencyAutonomyPatch(queryClient, raw);
      return patched ?? (await refreshAgencySettingsFromServer(queryClient));
    } catch (err) {
      console.error("Failed to update autonomy policy:", err);
      return null;
    }
  };

  return { mutate, isSaving: mutation.isPending, error: (mutation.error as Error) ?? null };
}

export function useUpdateSeasonalPolicy() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: UpdateSeasonalPayload) => updateAgencySeasonal(payload),
    onSuccess: (result) => {
      if (!upsertAgencySettings(queryClient, result) && !upsertAgencySeasonalPatch(queryClient, result)) {
        console.warn("Ignoring malformed seasonal update response, falling back to refetch", {
          source: "settings-update-seasonal",
        });
        queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
      }
    },
  });

  const mutate = async (payload: UpdateSeasonalPayload): Promise<AgencySettings | null> => {
    try {
      const raw = await mutation.mutateAsync(payload);
      const upserted = upsertAgencySettings(queryClient, raw);
      if (upserted) {
        return upserted;
      }
      const patched = upsertAgencySeasonalPatch(queryClient, raw);
      return patched ?? (await refreshAgencySettingsFromServer(queryClient));
    } catch (err) {
      console.error("Failed to update seasonal policy:", err);
      return null;
    }
  };

  return { mutate, isSaving: mutation.isPending, error: (mutation.error as Error) ?? null };
}
