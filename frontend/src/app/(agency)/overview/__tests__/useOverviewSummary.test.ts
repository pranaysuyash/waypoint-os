import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useOverviewSummary } from '../useOverviewSummary';

vi.mock('@/hooks/useTrips', () => ({
  useTrips: vi.fn(),
  usePipeline: vi.fn(),
}));

vi.mock('@/hooks/useGovernance', () => ({
  useInboxTrips: vi.fn(),
  useInboxStats: vi.fn(),
  useReviews: vi.fn(),
}));

vi.mock('@/hooks/useIntegrityIssues', () => ({
  useIntegrityIssues: vi.fn(),
}));

import { useTrips, usePipeline } from '@/hooks/useTrips';
import { useInboxStats, useInboxTrips, useReviews } from '@/hooks/useGovernance';
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

    vi.mocked(usePipeline).mockReturnValue({
      data: [
        { label: 'assigned', count: 1 },
        { label: 'in_progress', count: 1 },
      ],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    vi.mocked(useInboxTrips).mockReturnValue({
      data: [],
      total: 5,
      hasMore: true,
      filterCounts: {},
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      assignTrips: vi.fn(),
      bulkAction: vi.fn(),
      snoozeTrip: vi.fn(),
    });

    vi.mocked(useInboxStats).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
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
    expect(vi.mocked(useInboxTrips)).toHaveBeenCalledWith(undefined, 1, 5);
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
    expect(integrityMetric?.href).toBe('/overview?panel=system-check');
    expect(integrityNav?.sub).toBe('3 items to check');
    expect(integrityNav?.href).toBe('/overview?panel=system-check');
    expect(result.current.metrics.map((metric) => metric.title)).toEqual([
      'Trips in Planning',
      'New enquiries',
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

    expect(integrityMetric?.value).toBe('-');
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
      filterCounts: {},
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

  it('derives action required items from existing overview data sources', () => {
    vi.mocked(useTrips).mockReturnValue({
      data: [
        {
          id: 'trip_1',
          destination: 'Maldives',
          type: 'honeymoon',
          state: 'red',
          age: 'Today',
          createdAt: '2026-05-18T00:00:00Z',
          updatedAt: '2026-05-18T00:00:00Z',
        },
      ] as any,
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    vi.mocked(useInboxTrips).mockReturnValue({
      data: [
        {
          id: 'lead_1',
          reference: 'REF-1',
          destination: 'Singapore',
          tripType: 'family',
          partySize: 4,
          dateWindow: 'July 2026',
          value: 0,
          priority: 'medium',
          priorityScore: 60,
          urgency: 55,
          importance: 60,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-17T00:00:00Z',
          lastUpdated: '2026-05-17T00:00:00Z',
          daysInCurrentStage: 2,
          slaStatus: 'on_track',
          customerName: 'Amit Shah',
          flags: [],
        },
      ] as any,
      total: 2,
      hasMore: true,
      filterCounts: {},
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      assignTrips: vi.fn(),
      bulkAction: vi.fn(),
      snoozeTrip: vi.fn(),
    });

    vi.mocked(useReviews).mockReturnValue({
      data: [
        {
          id: 'review_1',
          tripId: 'trip_1',
          tripReference: 'TRIP-1',
          destination: 'Italy',
          tripType: 'honeymoon',
          partySize: 2,
          dateWindow: 'June',
          value: 3000,
          currency: 'USD',
          agentId: 'agent_1',
          agentName: 'Agent',
          submittedAt: '2026-05-18T00:00:00Z',
          status: 'pending',
          reason: 'Needs owner approval',
          riskFlags: [],
        },
      ] as any,
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });

    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [],
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());
    expect(result.current.actionRequiredItems.map((item) => item.source)).toEqual([
      'trip',
      'quote',
      'lead',
    ]);
  });

  it('derives action required loading/error state from the four source queries', () => {
    vi.mocked(useTrips).mockReturnValue({
      data: [],
      total: 0,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });
    vi.mocked(useInboxTrips).mockReturnValue({
      data: [],
      total: 0,
      hasMore: false,
      filterCounts: {},
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
      error: new Error('reviews down'),
      refetch: vi.fn(),
      submitAction: vi.fn(),
      bulkAction: vi.fn(),
    });
    vi.mocked(useIntegrityIssues).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { result } = renderHook(() => useOverviewSummary());
    expect(result.current.actionRequiredLoading).toBe(true);
    expect(result.current.actionRequiredError).toBeInstanceOf(Error);
  });
});
