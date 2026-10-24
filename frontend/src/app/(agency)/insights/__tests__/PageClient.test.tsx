import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import InsightsPageClient from '../PageClient';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock('@/components/visual/RevenueChart', () => ({
  RevenueChart: () => <div data-testid='revenue-chart' />,
}));

vi.mock('@/components/visual/PipelineFunnel', () => ({
  PipelineFunnel: () => <div data-testid='pipeline-funnel' />,
}));

vi.mock('@/components/visual/TeamPerformanceChart', () => ({
  TeamPerformanceChart: () => <div data-testid='team-performance-chart' />,
}));

vi.mock('@/components/workspace/panels/MetricDrillDownDrawer', () => ({
  MetricDrillDownDrawer: () => <div data-testid='metric-drilldown-drawer' />,
}));

vi.mock('@/components/visual/AnalyticsEmptyState', () => ({
  AnalyticsEmptyState: () => <div data-testid='analytics-empty-state' />,
}));

const mockUseInsightsSummary = vi.fn(() => ({
  totalInquiries: 1,
  conversionRate: 5,
  pipelineVelocity: {
    averageTotal: 3.1,
    stage1To2: 1,
    stage2To3: 1,
    stage3To4: 1,
    stage4To5: 0.8,
    stage5ToBooked: 0.3,
  },
}));

const mockUsePipelineMetrics = vi.fn(() => []);
const mockUseTeamMetrics = vi.fn(() => []);
const mockUseBottlenecks = vi.fn(() => []);
const mockUseRevenueMetrics = vi.fn(() => ({
  bookedRevenue: 0,
  totalPipelineValue: 0,
  projectedRevenue: 0,
  nearCloseRevenue: 0,
  revenueByMonth: [],
}));
const mockUseUnifiedState = vi.fn(() => ({ canonical_total: 0 }));
const mockDismissAlert = vi.fn();
const mockRefetchProductBKpis = vi.fn();

vi.mock('@/hooks/useGovernance', () => ({
  useInsightsSummary: () => ({
    data: mockUseInsightsSummary(),
    isLoading: false,
    error: null,
  }),
  usePipelineMetrics: () => ({
    data: mockUsePipelineMetrics(),
    isLoading: false,
    error: null,
  }),
  useTeamMetrics: () => ({
    data: mockUseTeamMetrics(),
    isLoading: false,
    error: null,
  }),
  useBottleneckAnalysis: () => ({
    data: mockUseBottlenecks(),
    isLoading: false,
    error: null,
  }),
  useRevenueMetrics: () => ({
    data: mockUseRevenueMetrics(),
    isLoading: false,
    error: null,
  }),
  useProductBKpis: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: mockRefetchProductBKpis,
  }),
  useOperationalAlerts: () => ({
    data: [
      {
        id: 'alert-1',
        tripId: 'trip_123',
        type: 'sla_breach',
        message: 'Trip missing critical documents',
        timestamp: '2026-06-17T09:00:00.000Z',
        metadata: {
          sla_status: 'breached',
          is_escalated: true,
          deadline: '2026-06-17T10:00:00.000Z',
        },
      },
    ],
    dismiss: mockDismissAlert,
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/hooks/useUnifiedState', () => ({
  useUnifiedState: () => ({
    state: mockUseUnifiedState(),
  }),
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: { user: { platform_role: 'none' } }) => unknown) =>
    selector({ user: { platform_role: 'none' } }),
}));

describe('Insights PageClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUnifiedState.mockClear();
  });

  it('uses canonical intake trip query for alert recovery action', () => {
    render(<InsightsPageClient />);

    const recoverLink = screen.getByRole('link', { name: /recover now/i });
    expect(recoverLink).toHaveAttribute('href', '/inquiries/new?trip=trip_123');
    expect(recoverLink).not.toHaveAttribute('href', '/inquiries/new?tripId=trip_123');
  });

  it('renders safely when list-shaped governance payloads are initially undefined', () => {
    mockUsePipelineMetrics.mockReturnValueOnce(undefined as never);
    mockUseTeamMetrics.mockReturnValueOnce(undefined as never);
    mockUseBottlenecks.mockReturnValueOnce(undefined as never);
    mockUseRevenueMetrics.mockReturnValueOnce({
      bookedRevenue: 0,
      totalPipelineValue: 0,
      projectedRevenue: 0,
      nearCloseRevenue: 0,
      revenueByMonth: [],
    });

    render(<InsightsPageClient />);

    expect(screen.getByRole('heading', { name: /Insights & Analytics/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /recover now/i })).toHaveAttribute('href', '/inquiries/new?trip=trip_123');
  });

  it('does not relabel missing commercial evidence as confirmed dollars', () => {
    render(<InsightsPageClient />);
    expect(screen.queryByText('Confirmed revenue')).not.toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Agency earned revenue' })).toHaveTextContent('Unavailable');
    expect(screen.getByRole('group', { name: 'Recorded booking value' })).toHaveTextContent('Not recorded');
    expect(screen.queryByText('$0')).not.toBeInTheDocument();
  });

  it('renders each recorded pipeline currency and qualifies partial evidence', () => {
    const unavailable = {
      availability: 'unavailable', totals: [], evidenceTripCount: 0,
      missingAmountTripCount: 0, missingCurrencyTripCount: 0, excludedPreviewTripCount: 0,
      reason: 'No supporting records',
    };
    mockUseRevenueMetrics.mockReturnValueOnce({
      bookedRevenue: null, totalPipelineValue: null, projectedRevenue: null,
      nearCloseRevenue: null, currency: null, revenueByMonth: [],
      commercial: {
        budgetPipeline: { ...unavailable, availability: 'partial', missingCurrencyTripCount: 1,
          evidenceTripCount: 2, totals: [
            {currency: 'INR', amount: 300000, amountDecimal: '300000', minorUnitDigits: 2, tripCount: 1},
            {currency: 'EUR', amount: 1500, amountDecimal: '1500', minorUnitDigits: 2, tripCount: 1},
          ]},
        weightedPipelineBudget: unavailable, nearCloseBudget: unavailable,
        bookedCustomerValue: unavailable, recordedCustomerCollections: unavailable,
        agencyEarnedRevenue: unavailable, agencyRealizedRevenue: unavailable,
      },
    } as never);
    render(<InsightsPageClient />);
    const pipeline = screen.getByRole('group', { name: 'Pipeline budgets' });
    expect(pipeline).toHaveTextContent('INR');
    expect(pipeline).toHaveTextContent('EUR');
    expect(pipeline).toHaveTextContent(/partial/i);
    expect(pipeline).not.toHaveTextContent('$');
  });
});
