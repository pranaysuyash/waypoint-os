import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  useAgencySettings,
  useUpdateOperationalSettings,
  useUpdateAutonomyPolicy,
  useUpdateSeasonalPolicy,
} from '../useAgencySettings';
import * as apiClient from '@/lib/api-client';

vi.mock('@/lib/api-client');

const validAgencySettings = {
  agency_id: 'agency-123',
  seasonal: {
    active_seasons_enabled: true,
    default_quarter_window_months: 4,
    channel_mix: { whatsapp: 0.65, email: 0.25 },
    weather_risk_threshold: 0.75,
    budget_guardrail_multiplier: 1.2,
    micro_seasonality_window_days: 15,
    quarterly_recalibration_enabled: false,
    prelaunch_blocklist: ['monsoon', 'flood'],
  },
  profile: {
    agency_name: 'Blue Sky Travel',
    sub_brand: 'Aqua',
    plan_label: 'Growth',
    contact_email: 'ops@bluesky.travel',
    contact_phone: '+91 98765 43210',
    logo_url: 'https://example.com/logo.png',
    website: 'https://bluesky.example.com',
  },
  operational: {
    target_margin_pct: 22,
    default_currency: 'USD',
    operating_hours: { start: '09:00', end: '18:00' },
    operating_days: ['mon', 'tue', 'wed', 'thu', 'fri'],
    preferred_channels: ['whatsapp', 'email'],
    brand_tone: 'professional',
  },
  autonomy: {
    approval_gates: {
      proposal: 'review',
      booking: 'auto',
    },
    mode_overrides: { default: { budget: 'warn' } },
    auto_proceed_with_warnings: true,
    learn_from_overrides: true,
    auto_reprocess_on_edit: false,
    allow_explicit_reassess: true,
    auto_reprocess_stages: { proposal: true, booking: false },
    min_proceed_confidence: 0.72,
    min_draft_confidence: 0.58,
  },
};

const baselineSettings = validAgencySettings;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

function createHarness() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  const Wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  return { Wrapper, queryClient };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useAgencySettings contract-shape safety', () => {
  it('normalizes malformed settings payloads to null', async () => {
    vi.mocked(apiClient.getAgencySettings).mockResolvedValue({} as never);

    const { result } = renderHook(() => useAgencySettings(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('preserves valid settings payloads', async () => {
    vi.mocked(apiClient.getAgencySettings).mockResolvedValue(validAgencySettings as never);

    const { result } = renderHook(() => useAgencySettings(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).not.toBeNull());

    expect(result.current.data).toEqual(validAgencySettings);
  });

  it('does not overwrite existing cached settings on malformed operational update response', async () => {
    vi.mocked(apiClient.updateAgencyOperational).mockResolvedValue({} as never);
    const { Wrapper, queryClient } = createHarness();
    queryClient.setQueryData(['agency', 'settings'], baselineSettings);

    const { result } = renderHook(() => useUpdateOperationalSettings(), { wrapper: Wrapper });

    await act(async () => {
      const updateResult = await result.current.mutate({ brand_tone: 'professional' });
      expect(updateResult).toBeNull();
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(baselineSettings);
    });
  });

  it('updates cache when operational settings mutation returns a valid payload', async () => {
    const operationResponse = {
      agency_id: 'agency-123',
      profile: {
        agency_name: 'Blue Sky Travel',
        sub_brand: 'Aqua',
        plan_label: 'Growth',
        contact_email: 'ops@bluesky.travel',
        contact_phone: '+91 98765 43210',
        logo_url: 'https://example.com/logo.png',
        website: 'https://bluesky.example.com',
      },
      operational: {
        target_margin_pct: 30,
        default_currency: 'USD',
        operating_hours: { start: '09:00', end: '18:00' },
        operating_days: ['mon', 'tue', 'wed', 'thu', 'fri'],
        preferred_channels: ['whatsapp', 'email'],
        brand_tone: 'professional',
      },
      changes: ['target_margin_pct'],
    };

    const expectedSettings = {
      ...baselineSettings,
      operational: {
        ...baselineSettings.operational,
        target_margin_pct: 30,
      },
    };

    vi.mocked(apiClient.updateAgencyOperational).mockResolvedValue(operationResponse as never);
    const { Wrapper, queryClient } = createHarness();
    queryClient.setQueryData(['agency', 'settings'], baselineSettings);

    const { result } = renderHook(() => useUpdateOperationalSettings(), { wrapper: Wrapper });

    await act(async () => {
      const updated = await result.current.mutate({ target_margin_pct: 30 });
      expect(updated).toEqual(expectedSettings);
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(expectedSettings);
    });
  });

  it('merges valid autonomy payloads into cached settings', async () => {
    const nextAutonomy = {
      agency_id: 'agency-123',
      approval_gates: { proposal: 'review', booking: 'auto' },
      mode_overrides: { default: { budget: 'approve' } },
      auto_proceed_with_warnings: false,
      learn_from_overrides: false,
      auto_reprocess_on_edit: true,
      allow_explicit_reassess: true,
      auto_reprocess_stages: { proposal: false, booking: false },
      min_proceed_confidence: 0.61,
      min_draft_confidence: 0.52,
    };

    const expectedAutonomy = {
      ...baselineSettings,
      autonomy: {
        approval_gates: nextAutonomy.approval_gates,
        mode_overrides: nextAutonomy.mode_overrides,
        auto_proceed_with_warnings: nextAutonomy.auto_proceed_with_warnings,
        learn_from_overrides: nextAutonomy.learn_from_overrides,
        auto_reprocess_on_edit: nextAutonomy.auto_reprocess_on_edit,
        allow_explicit_reassess: nextAutonomy.allow_explicit_reassess,
        auto_reprocess_stages: nextAutonomy.auto_reprocess_stages,
        min_proceed_confidence: nextAutonomy.min_proceed_confidence,
        min_draft_confidence: nextAutonomy.min_draft_confidence,
      },
    };

    vi.mocked(apiClient.updateAgencyAutonomy).mockResolvedValue(nextAutonomy as never);
    const { Wrapper, queryClient } = createHarness();
    queryClient.setQueryData(['agency', 'settings'], baselineSettings);

    const { result } = renderHook(() => useUpdateAutonomyPolicy(), { wrapper: Wrapper });

    await act(async () => {
      const updated = await result.current.mutate({ allow_explicit_reassess: true });
      expect(updated).toEqual(expectedAutonomy);
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(expectedAutonomy);
    });
  });

  it('merges valid seasonal payloads into cached settings', async () => {
    const nextSeasonal = {
      active_seasons_enabled: false,
      default_quarter_window_months: 8,
      channel_mix: { whatsapp: 0.55, email: 0.45 },
      weather_risk_threshold: 0.88,
      budget_guardrail_multiplier: 1.15,
      micro_seasonality_window_days: 20,
      quarterly_recalibration_enabled: true,
      prelaunch_blocklist: ['heatwave'],
    };

    const expectedSeasonal = {
      ...baselineSettings,
      seasonal: {
        active_seasons_enabled: nextSeasonal.active_seasons_enabled,
        default_quarter_window_months: nextSeasonal.default_quarter_window_months,
        channel_mix: nextSeasonal.channel_mix,
        weather_risk_threshold: nextSeasonal.weather_risk_threshold,
        budget_guardrail_multiplier: nextSeasonal.budget_guardrail_multiplier,
        micro_seasonality_window_days: nextSeasonal.micro_seasonality_window_days,
        quarterly_recalibration_enabled: nextSeasonal.quarterly_recalibration_enabled,
        prelaunch_blocklist: nextSeasonal.prelaunch_blocklist,
      },
    };

    vi.mocked(apiClient.updateAgencySeasonal).mockResolvedValue(nextSeasonal as never);
    const { Wrapper, queryClient } = createHarness();
    queryClient.setQueryData(['agency', 'settings'], baselineSettings);

    const { result } = renderHook(() => useUpdateSeasonalPolicy(), { wrapper: Wrapper });

    await act(async () => {
      const updated = await result.current.mutate({ weather_risk_threshold: nextSeasonal.weather_risk_threshold });
      expect(updated).toEqual(expectedSeasonal);
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(expectedSeasonal);
    });
  });

  it('invalid autonomy payload does not crash and keeps cached settings intact', async () => {
    vi.mocked(apiClient.updateAgencyAutonomy).mockResolvedValue({} as never);
    const { Wrapper, queryClient } = createHarness();
    queryClient.setQueryData(['agency', 'settings'], baselineSettings);

    const { result } = renderHook(() => useUpdateAutonomyPolicy(), { wrapper: Wrapper });

    await act(async () => {
      const updateResult = await result.current.mutate({ allow_explicit_reassess: true });
      expect(updateResult).toBeNull();
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(baselineSettings);
    });
  });

  it('rejected autonomy mutation keeps cached settings intact and returns null', async () => {
    vi.mocked(apiClient.updateAgencyAutonomy).mockRejectedValue(new Error('400: invalid autonomy action'));
    const { Wrapper, queryClient } = createHarness();
    queryClient.setQueryData(['agency', 'settings'], baselineSettings);

    const { result } = renderHook(() => useUpdateAutonomyPolicy(), { wrapper: Wrapper });

    await act(async () => {
      const updateResult = await result.current.mutate({ allow_explicit_reassess: true });
      expect(updateResult).toBeNull();
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(baselineSettings);
    });
  });

  it('falls back to refetch when autonomy update returns malformed payload and cache is empty', async () => {
    vi.mocked(apiClient.updateAgencyAutonomy).mockResolvedValue({} as never);
    vi.mocked(apiClient.getAgencySettings).mockResolvedValue(validAgencySettings as never);
    const { Wrapper, queryClient } = createHarness();

    const { result } = renderHook(() => useUpdateAutonomyPolicy(), { wrapper: Wrapper });

    await act(async () => {
      const updateResult = await result.current.mutate({ allow_explicit_reassess: true });
      expect(updateResult).toEqual(validAgencySettings);
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(validAgencySettings);
    });
    expect(vi.mocked(apiClient.getAgencySettings)).toHaveBeenCalledTimes(1);
  });

  it('falls back to refetch when operational update returns malformed payload and cache is empty', async () => {
    vi.mocked(apiClient.updateAgencyOperational).mockResolvedValue({} as never);
    vi.mocked(apiClient.getAgencySettings).mockResolvedValue(validAgencySettings as never);
    const { Wrapper, queryClient } = createHarness();

    const { result } = renderHook(() => useUpdateOperationalSettings(), { wrapper: Wrapper });

    await act(async () => {
      const updateResult = await result.current.mutate({ brand_tone: 'professional' });
      expect(updateResult).toEqual(validAgencySettings);
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(validAgencySettings);
    });
    expect(vi.mocked(apiClient.getAgencySettings)).toHaveBeenCalledTimes(1);
  });

  it('falls back to refetch when seasonal update returns malformed payload and cache is empty', async () => {
    vi.mocked(apiClient.updateAgencySeasonal).mockResolvedValue({} as never);
    vi.mocked(apiClient.getAgencySettings).mockResolvedValue(validAgencySettings as never);
    const { Wrapper, queryClient } = createHarness();

    const { result } = renderHook(() => useUpdateSeasonalPolicy(), { wrapper: Wrapper });

    await act(async () => {
      const updateResult = await result.current.mutate({ weather_risk_threshold: 0.8 });
      expect(updateResult).toEqual(validAgencySettings);
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(['agency', 'settings'])).toEqual(validAgencySettings);
    });
    expect(vi.mocked(apiClient.getAgencySettings)).toHaveBeenCalledTimes(1);
  });
});
