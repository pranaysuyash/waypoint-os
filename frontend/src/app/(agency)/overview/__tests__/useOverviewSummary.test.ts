import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useOverviewSummary } from '../useOverviewSummary';

vi.mock('@/hooks/useTrips', () => ({
  useTrips: vi.fn(),
}));

vi.mock('@/hooks/useGovernance', () => ({
  useInboxTrips: vi.fn(),
  useReviews: vi.fn(),
}));

vi.mock('@/hooks/useUnifiedState', () => ({
  useUnifiedState: vi.fn(),
}));

vi.mock('@/hooks/useIntegrityIssues', () => ({
  useIntegrityIssues: vi.fn(),
}));

import { useTrips } from '@/hooks/useTrips';
import { useInboxTrips, useReviews } from '@/hooks/useGovernance';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { useIntegrityIssues } from '@/hooks/useIntegrityIssues';

describe('useOverviewSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTrips).mockReturnValue({
      data: [],
      total: 2,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    vi.mocked(useInboxTrips).mockReturnValue({
      data: [],
      total: 5,
      hasMore: true,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      assignTrips: vi.fn(),
      bulkAction: vi.fn(),
      snoozeTrip: vi.fn(),
    });

    vi.mocked(useUnifiedState).mockReturnValue({
      state: {
        canonical_total: 7,
        stages: {
          new: 2,
          assigned: 3,
          in_progress: 2,
          completed: 0,
          cancelled: 0,
        },
        sla_breached: 0,
        orphans: [{ id: 'orphan-1' }],
        integrity_meta: {
          sum_stages: 7,
          orphan_count: 1,
          consistent: true,
        },
      },
      loading: false,
      error: null,
      refresh: vi.fn(),
      isConsistent: true,
    });

    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('uses pending review total instead of loaded review items', () => {
    vi.mocked(useReviews).mockReturnValue({
      data: [
        { id: 'r-1', status: 'pending' },
        { id: 'r-2', status: 'pending' },
      ] as any,
      total: 7,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());

    const approvalMetric = result.current.metrics.find(
      (metric) => metric.title === 'Quote Review'
    );

    expect(vi.mocked(useReviews)).toHaveBeenCalledWith({ status: 'pending' });
    expect(approvalMetric?.value).toBe(7);
    expect(result.current.headerSubtitle).toContain('7 quotes to review');
  });

  it('uses user-facing system-check labels while still routing integrity to the typed endpoint', () => {
    vi.mocked(useReviews).mockReturnValue({
      data: [] as any,
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });

    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [
        {
          id: 'integrity_orphaned_record_trip_123',
          entity_id: 'trip_123',
          entity_type: 'unknown',
          issue_type: 'orphaned_record',
          severity: 'medium',
          reason: 'Record is detached from normal inbox/workspace routing.',
          current_status: 'mystery',
          created_at: '2026-04-30T00:00:00Z',
          detected_at: '2026-04-30T00:00:00Z',
          allowed_actions: [],
        },
      ],
      total: 3,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());

    const integrityMetric = result.current.metrics.find(
      (metric) => metric.title === 'System Check'
    );
    const integrityNav = result.current.navItems.find(
      (item) => item.label === 'System Check'
    );

    expect(integrityMetric?.value).toBe(3);
    expect(integrityMetric?.sub).toBe('3 items to check');
    expect(integrityMetric?.href).toBe('/workbench?panel=integrity');
    expect(integrityNav?.sub).toBe('3 items to check');
    expect(integrityNav?.href).toBe('/workbench?panel=integrity');
    expect(result.current.metrics.map((metric) => metric.title)).toEqual([
      'Trips in Planning',
      'Lead Inbox',
      'Quote Review',
      'System Check',
    ]);
  });

  it('shows check unavailable instead of a false zero when ops health fails', () => {
    vi.mocked(useReviews).mockReturnValue({
      data: [] as any,
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });

    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: new Error('backend unavailable'),
      refetch: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());

    const integrityMetric = result.current.metrics.find(
      (metric) => metric.title === 'System Check'
    );
    const integrityNav = result.current.navItems.find(
      (item) => item.label === 'System Check'
    );

    expect(integrityMetric?.value).toBe('—');
    expect(integrityMetric?.sub).toBe('System check unavailable');
    expect(integrityMetric?.error).toBeNull();
    expect(integrityNav?.sub).toBe('System check unavailable');
  });

  it('uses singular system-check copy for a single issue', () => {
    vi.mocked(useReviews).mockReturnValue({
      data: [] as any,
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });

    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [
        {
          id: 'integrity_orphaned_record_trip_123',
          entity_id: 'trip_123',
          entity_type: 'unknown',
          issue_type: 'orphaned_record',
          severity: 'medium',
          reason: 'Record is detached from normal inbox/workspace routing.',
          current_status: 'mystery',
          created_at: '2026-04-30T00:00:00Z',
          detected_at: '2026-04-30T00:00:00Z',
          allowed_actions: [],
        },
      ],
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());

    const integrityMetric = result.current.metrics.find(
      (metric) => metric.title === 'System Check'
    );

    expect(integrityMetric?.sub).toBe('1 item to check');
  });

  it('exposes planning and inbox totals for lifecycle-aware overview states', () => {
    vi.mocked(useTrips).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    vi.mocked(useInboxTrips).mockReturnValue({
      data: [],
      total: 4,
      hasMore: true,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      assignTrips: vi.fn(),
      bulkAction: vi.fn(),
      snoozeTrip: vi.fn(),
    });

    vi.mocked(useReviews).mockReturnValue({
      data: [] as any,
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());

    expect(result.current.planningTripsTotal).toBe(0);
    expect(result.current.leadInboxTotal).toBe(4);
  });
});
