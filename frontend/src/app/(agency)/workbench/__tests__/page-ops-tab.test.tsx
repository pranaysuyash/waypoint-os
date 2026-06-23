import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';

// Mock next/dynamic to return a real component with the module name
const dynamicModules: Record<string, ReactNode> = {};
vi.mock('next/dynamic', () => ({
  default: (loader: { loading: () => ReactNode }) => {
    // Return a stub that renders nothing - we just test the page shell
    return function DynamicStub() {
      return <div data-testid='dynamic-stub' />;
    };
  },
}));

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

const mockRouterReplace = vi.fn();
const mockRouterPush = vi.fn();
vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(),
  useRouter: () => ({ push: mockRouterPush, replace: mockRouterReplace }),
  usePathname: () => '/workbench',
}));

vi.mock('@/components/error-boundary', () => ({
  ErrorBoundary: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('./PipelineFlow', () => ({
  PipelineFlow: () => <div data-testid='pipeline-flow' />,
}));

// Capture the tabs prop to test visibility
let renderedTabs: { id: string; label: string }[] = [];
let mockSpineRunState: {
  state: string | null;
  frontier_result?: Record<string, unknown> | null;
  decision_state?: string | null;
  hard_blockers?: string[];
  soft_blockers?: string[];
} = {
  state: null,
  frontier_result: null,
  decision_state: null,
  hard_blockers: [],
  soft_blockers: [],
};
vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ tabs }: { tabs: { id: string; label: string }[] }) => {
    renderedTabs = tabs;
    return <div data-testid='tabs' />;
  },
}));

let mockTripData: Record<string, unknown> | null = null;
let mockFrontierData: Record<string, unknown> | null = null;
vi.mock('@/hooks/useTrips', () => ({
  useTrip: () => ({
    data: mockTripData,
    isLoading: false,
    error: null,
  }),
  useUpdateTrip: () => ({
    mutate: vi.fn(),
    isSaving: false,
  }),
}));

vi.mock('@/hooks/useSpineRun', () => ({
  useSpineRun: () => ({
    execute: vi.fn(),
    isLoading: false,
    error: null,
    reset: vi.fn(),
    runId: null,
    state: mockSpineRunState,
  }),
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => ({
    result_safety: null,
    result_strategy: null,
    result_decision: null,
    result_packet: null,
    result_validation: null,
    result_frontier: mockFrontierData,
    input_raw_note: '',
    input_owner_note: '',
    input_structured_json: '',
    input_itinerary_text: '',
    strict_leakage: false,
    draft_id: null,
    draft_name: '',
    draft_status: 'open',
    draft_version: 1,
    draft_last_saved_at: null,
    save_state: 'saved',
    result_run_ts: null,
    setResultPacket: vi.fn(),
    setResultValidation: vi.fn(),
    setResultDecision: vi.fn(),
    setResultStrategy: vi.fn(),
    setResultInternalBundle: vi.fn(),
    setResultTravelerBundle: vi.fn(),
    setResultSafety: vi.fn(),
    setResultFees: vi.fn(),
    setResultFrontier: vi.fn(),
    clearTransientRunResults: vi.fn(),
    clearDraft: vi.fn(),
    hydrateFromDraft: vi.fn(),
    setDraftStatus: vi.fn(),
    setSaveState: vi.fn(),
    setDraftMeta: vi.fn(),
    setInputRawNote: vi.fn(),
    setInputOwnerNote: vi.fn(),
    resetAll: vi.fn(),
  }),
}));

vi.mock('@/lib/api-client', () => ({
  submitTripReviewAction: vi.fn(),
  createDraft: vi.fn(),
  getDraft: vi.fn(),
  patchDraft: vi.fn(),
  discardDraft: vi.fn(),
  promoteDraft: vi.fn(),
}));

import { useSearchParams } from 'next/navigation';
import WorkbenchPage from '../page';

describe('Workbench ops tab visibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    renderedTabs = [];
    mockTripData = null;
    mockFrontierData = null;
    mockSpineRunState = { state: null, frontier_result: null, decision_state: null, hard_blockers: [], soft_blockers: [] };
  });

  it('does not show ops tab at discovery stage', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'discovery' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).not.toContain('ops');
  });

  it('does not show ops tab at shortlist stage', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'shortlist' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).not.toContain('ops');
  });

  it('does not show ops tab at proposal stage (ops moved to Trip Workspace)', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'proposal' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).not.toContain('ops');
  });

  it('does not show ops tab at booking stage (ops moved to Trip Workspace)', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'booking' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).not.toContain('ops');
  });

  it('does not render OpsPanel when URL requests ?tab=ops at discovery stage', () => {
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams('tab=ops') as never,
    );
    mockTripData = { id: 't1', stage: 'discovery' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).not.toContain('ops');
    expect(screen.queryByTestId('ops-panel')).not.toBeInTheDocument();
    expect(screen.queryByTestId('ops-panel-empty')).not.toBeInTheDocument();
  });

  it('does not show ops tab at any stage — ops lives in Trip Workspace', () => {
    for (const stage of ['discovery', 'shortlist', 'proposal', 'booking']) {
      vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
      mockTripData = { id: 't1', stage };
      renderedTabs = [];
      render(<WorkbenchPage />);
      expect(renderedTabs.map((t) => t.id)).not.toContain('ops');
    }
  });

  it('shows frontier tab when frontier result exists', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'discovery' };
    mockFrontierData = { sentiment_score: 0.82 };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).toContain('frontier');
  });

  it('auto-switches to frontier tab when run completes with frontier result', () => {
    mockSpineRunState = {
      state: 'completed',
      frontier_result: { sentiment_score: 0.82 },
      decision_state: null,
      hard_blockers: [],
      soft_blockers: [],
    };
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'discovery' };

    render(<WorkbenchPage />);

    expect(mockRouterReplace).toHaveBeenCalledWith('?tab=frontier', { scroll: false });
  });

  it('keeps Trip Details open when a completed run already includes follow-up blockers', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=safety') as never);
    mockTripData = { id: 't1', stage: 'discovery' };
    mockSpineRunState = {
      state: 'completed',
      frontier_result: null,
      decision_state: 'ASK_FOLLOWUP',
      hard_blockers: [],
      soft_blockers: ['soft_preferences'],
    };

    const { rerender } = render(<WorkbenchPage />);
    mockRouterReplace.mockClear();

    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=packet') as never);
    rerender(<WorkbenchPage />);

    expect(mockRouterReplace).not.toHaveBeenCalledWith('?tab=safety', { scroll: false });
  });

  it('keeps Trip Details open after a frontier result once the run has already completed', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=frontier') as never);
    mockTripData = { id: 't1', stage: 'discovery' };
    mockSpineRunState = {
      state: 'completed',
      frontier_result: { sentiment_score: 0.82 },
      decision_state: null,
      hard_blockers: [],
      soft_blockers: [],
    };

    const { rerender } = render(<WorkbenchPage />);
    mockRouterReplace.mockClear();

    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=packet') as never);
    rerender(<WorkbenchPage />);

    expect(mockRouterReplace).not.toHaveBeenCalledWith('?tab=frontier', { scroll: false });
  });

  it('switches to frontier when the run completes and frontier is present', () => {
    mockSpineRunState = {
      state: null,
      frontier_result: null,
      decision_state: null,
      hard_blockers: [],
      soft_blockers: [],
    };
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'discovery' };

    const { rerender } = render(<WorkbenchPage />);
    expect(mockRouterReplace).toHaveBeenCalledTimes(0);

    mockRouterReplace.mockClear();
    mockSpineRunState = {
      state: 'completed',
      frontier_result: { sentiment_score: 0.82 },
      decision_state: null,
      hard_blockers: [],
      soft_blockers: [],
    };
    rerender(<WorkbenchPage />);

    expect(mockRouterReplace).toHaveBeenCalledWith('?tab=frontier', { scroll: false });
  });
});

// ---------------------------------------------------------------------------
// getPostRunTripRoute priority — tested directly via the exported helper in routes.ts
// ---------------------------------------------------------------------------
// Priority: BLOCKED/ESCALATED → packet; proposal/booking (clean) → ops; else → intake.

import { getPostRunTripRoute } from '@/lib/routes';

describe('getPostRunTripRoute routing priority', () => {
  it('proposal + BLOCKED → /packet (blocked wins over stage)', () => {
    expect(getPostRunTripRoute({ tripId: 'trip_123', tripStage: 'proposal', validationStatus: 'BLOCKED' }))
      .toBe('/trips/trip_123/packet');
  });

  it('booking + ESCALATED → /packet', () => {
    expect(getPostRunTripRoute({ tripId: 'trip_123', tripStage: 'booking', validationStatus: 'ESCALATED' }))
      .toBe('/trips/trip_123/packet');
  });

  it('proposal + clean → /ops', () => {
    expect(getPostRunTripRoute({ tripId: 'trip_123', tripStage: 'proposal', validationStatus: null }))
      .toBe('/trips/trip_123/ops');
  });

  it('booking + clean → /ops', () => {
    expect(getPostRunTripRoute({ tripId: 'trip_123', tripStage: 'booking' }))
      .toBe('/trips/trip_123/ops');
  });

  it('intake stage → /intake', () => {
    expect(getPostRunTripRoute({ tripId: 'trip_123', tripStage: 'intake' }))
      .toBe('/trips/trip_123/intake');
  });
});

// ---------------------------------------------------------------------------
// Workbench tab=ops compatibility alias
// ---------------------------------------------------------------------------

describe('Workbench ?tab=ops compatibility redirect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    renderedTabs = [];
    mockTripData = null;
    mockSpineRunState = { state: null, frontier_result: null };
  });

  it('replaces history (not pushes) when redirecting ?tab=ops with a trip ID', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=ops&trip=trip_123') as never);
    mockTripData = { id: 'trip_123', stage: 'proposal' };

    render(<WorkbenchPage />);

    const opsRedirectCalls = mockRouterReplace.mock.calls
      .map(([to]) => to)
      .filter((to) => to === '/trips/trip_123/ops');
    expect(opsRedirectCalls).toHaveLength(1);
    expect(mockRouterReplace).toHaveBeenCalledWith('/trips/trip_123/ops');
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('supports legacy ?tab=ops&tripId alias for the same redirect behavior', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=ops&tripId=trip_456') as never);
    mockTripData = { id: 'trip_456', stage: 'proposal' };

    render(<WorkbenchPage />);

    expect(mockRouterReplace).toHaveBeenCalledWith('/trips/trip_456/ops');
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('uses canonical trip over legacy tripId when both are present', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=ops&trip=trip_123&tripId=trip_456') as never);
    mockTripData = { id: 'trip_123', stage: 'proposal' };

    render(<WorkbenchPage />);

    expect(mockRouterReplace).toHaveBeenCalledWith('/trips/trip_123/ops');
    expect(mockRouterReplace).not.toHaveBeenCalledWith('/trips/trip_456/ops');
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('falls back to intake tab when ?tab=ops is opened without a trip', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=ops&foo=bar') as never);
    mockTripData = null;

    render(<WorkbenchPage />);

    const redirectArg = mockRouterReplace.mock.calls.at(-1)?.[0];
    expect(typeof redirectArg).toBe('string');
    if (typeof redirectArg === 'string') {
      const redirectedParams = new URLSearchParams(redirectArg.replace('/workbench?', ''));
      expect(redirectedParams.get('tab')).toBe('intake');
      expect(redirectedParams.get('foo')).toBe('bar');
      expect(redirectedParams.get('notice')).toBeNull();
      expect(redirectedParams.get('trip')).toBeNull();
      expect(redirectedParams.get('tripId')).toBeNull();
    }
    expect(mockRouterPush).not.toHaveBeenCalled();
  });
});
