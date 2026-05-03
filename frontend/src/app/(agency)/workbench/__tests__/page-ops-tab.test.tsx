import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';

// Mock next/dynamic to return a real component with the module name
const dynamicModules: Record<string, ReactNode> = {};
vi.mock('next/dynamic', () => ({
  default: (loader: { loading: () => ReactNode }) => {
    // Return a stub that renders nothing — we just test the page shell
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

  it('shows ops tab at proposal stage', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'proposal' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).toContain('ops');
  });

  it('shows ops tab at booking stage', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockTripData = { id: 't1', stage: 'booking' };

    render(<WorkbenchPage />);

    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).toContain('ops');
  });

  it('does not render OpsPanel when URL requests ?tab=ops at discovery stage', () => {
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams('tab=ops') as never,
    );
    mockTripData = { id: 't1', stage: 'discovery' };

    render(<WorkbenchPage />);

    // Ops tab should not be in visible tabs
    const tabIds = renderedTabs.map((t) => t.id);
    expect(tabIds).not.toContain('ops');
    // OpsPanel should not render (no ops-panel or ops-panel-empty testid)
    expect(screen.queryByTestId('ops-panel')).not.toBeInTheDocument();
    expect(screen.queryByTestId('ops-panel-empty')).not.toBeInTheDocument();
  });
});
