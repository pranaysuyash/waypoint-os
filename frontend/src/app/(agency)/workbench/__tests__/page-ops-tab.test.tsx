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
vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(),
  useRouter: () => ({ push: vi.fn(), replace: mockRouterReplace }),
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
vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ tabs }: { tabs: { id: string; label: string }[] }) => {
    renderedTabs = tabs;
    return <div data-testid='tabs' />;
  },
}));

let mockTripData: Record<string, unknown> | null = null;
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
    state: null,
  }),
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => ({
    result_safety: null,
    result_strategy: null,
    result_decision: null,
    result_packet: null,
    result_validation: null,
    result_frontier: null,
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
  });

  it('replaces history (not pushes) when redirecting ?tab=ops with a trip ID', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=ops&trip=trip_123') as never);
    mockTripData = { id: 'trip_123', stage: 'proposal' };

    render(<WorkbenchPage />);

    expect(mockRouterReplace).toHaveBeenCalledWith('/trips/trip_123/ops');
    // push should NOT be called for this alias redirect
    expect(mockRouterReplace).toHaveBeenCalledTimes(1);
  });

  it('adds notice=ops-requires-trip when ?tab=ops is opened without a trip', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=ops') as never);
    mockTripData = null;

    render(<WorkbenchPage />);

    expect(mockRouterReplace).toHaveBeenCalledWith(
      expect.stringContaining('notice=ops-requires-trip'),
    );
  });
});
