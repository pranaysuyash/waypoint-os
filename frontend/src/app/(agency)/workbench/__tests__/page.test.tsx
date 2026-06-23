import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import WorkbenchPage, { extractCompletedTripIdFromDraft } from '../page';

const mockReplace = vi.fn();
const mockExecuteSpineRun = vi.fn();
const mockCreateDraft = vi.hoisted(() => vi.fn());
let mockWorkbenchStore: Record<string, unknown>;
let mockAuthState = {
  isLoading: false,
  isAuthenticated: true,
};

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('next/dynamic', () => ({
  default: () => {
    return function DynamicStub() {
      return <div data-testid='dynamic-stub' />;
    };
  },
}));

vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(),
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
  usePathname: () => '/workbench',
}));

vi.mock('@/components/error-boundary', () => ({
  ErrorBoundary: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('./PipelineFlow', () => ({
  PipelineFlow: () => <div data-testid='pipeline-flow' />,
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: () => <div data-testid='tabs' />,
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrip: () => ({
    data: null,
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
    execute: mockExecuteSpineRun,
    isLoading: false,
    error: null,
    reset: vi.fn(),
    runId: null,
    state: null,
  }),
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockWorkbenchStore,
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: typeof mockAuthState) => unknown) => selector(mockAuthState),
}));

mockWorkbenchStore = {
    result_safety: null,
    result_strategy: null,
    result_decision: null,
    result_packet: null,
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
};

vi.mock('@/lib/api-client', () => ({
  submitTripReviewAction: vi.fn(),
  createDraft: mockCreateDraft,
  getDraft: vi.fn().mockResolvedValue({
    draft_id: 'draft_test_123',
    draft_name: 'Draft Test',
    draft_status: 'open',
    draft_version: 1,
    draft_last_saved_at: null,
    customer_message: '',
    agent_notes: '',
    structured_json: null,
    itinerary_text: null,
    stage: 'discovery',
    operating_mode: 'normal_intake',
    scenario_id: null,
    strict_leakage: false,
  }),
  patchDraft: vi.fn(),
  discardDraft: vi.fn(),
  promoteDraft: vi.fn(),
}));

import { useSearchParams } from 'next/navigation';

describe('WorkbenchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateDraft.mockReset();
    mockAuthState = {
      isLoading: false,
      isAuthenticated: true,
    };
    mockWorkbenchStore = {
      ...mockWorkbenchStore,
      input_raw_note: '',
      input_owner_note: '',
      draft_id: null,
      save_state: 'saved',
    };
  });

  it('does not render the overview return link in the default workbench view', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);

    render(<WorkbenchPage />);

    expect(screen.queryByRole('link', { name: /back to overview/i })).not.toBeInTheDocument();
  });

  it('falls back to intake when Frontier tab is requested without frontier visibility', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=frontier') as never);

    render(<WorkbenchPage />);

    expect(screen.getByText(/process inquiry/i)).toBeInTheDocument();
  });

  it('submits the workbench intake when process inquiry is used', async () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = {
      ...mockWorkbenchStore,
      input_raw_note: 'Traveler wants Bali in July',
      input_owner_note: 'Keep margin >=18%',
      draft_id: 'draft-test-001',
    };

    render(<WorkbenchPage />);

    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /process inquiry/i }));

    expect(mockExecuteSpineRun).toHaveBeenCalledTimes(1);
    expect(mockExecuteSpineRun).toHaveBeenCalledWith(expect.objectContaining({
      raw_note: 'Traveler wants Bali in July',
      owner_note: 'Keep margin >=18%',
      draft_id: 'draft-test-001',
    }));
  });

  it('creates a draft and still submits the run on the first process click', async () => {
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams('draft=new&tab=intake&capture_mode=call&entry=new') as never,
    );
    mockCreateDraft.mockResolvedValue({
      draft_id: 'draft_test_first_submit',
      name: 'Draft Test First Submit',
      status: 'open',
      created_at: '2026-06-22T00:00:00.000Z',
    });
    mockWorkbenchStore = {
      ...mockWorkbenchStore,
      input_raw_note: 'Traveler wants Bali in July',
      input_owner_note: 'Keep margin >=18%',
      draft_id: null,
    };

    render(<WorkbenchPage />);

    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /process inquiry/i }));

    expect(mockCreateDraft).toHaveBeenCalledTimes(1);
    expect(mockExecuteSpineRun).toHaveBeenCalledTimes(1);
    expect(mockExecuteSpineRun).toHaveBeenCalledWith(expect.objectContaining({
      raw_note: 'Traveler wants Bali in July',
      owner_note: 'Keep margin >=18%',
      draft_id: 'draft_test_first_submit',
    }));
  });

  it('preserves an existing draft id for fast-capture entry instead of resetting to draft=new', () => {
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams('draft=draft_test_123&entry=new&capture_mode=call') as never,
    );
    mockWorkbenchStore = {
      ...mockWorkbenchStore,
      draft_id: 'draft_test_123',
    };

    render(<WorkbenchPage />);

    expect(mockReplace).not.toHaveBeenCalledWith(expect.stringContaining('draft=new'), expect.anything());
  });

  it('shows a sign-in notice when the browser session is unauthenticated', () => {
    mockAuthState = {
      isLoading: false,
      isAuthenticated: false,
    };
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams('draft=new&tab=intake&capture_mode=call&entry=new') as never,
    );

    render(<WorkbenchPage />);

    expect(screen.getByRole('heading', { name: /workbench/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in to continue/i })).toHaveAttribute(
      'href',
      '/login?redirect=%2Fworkbench%3Fdraft%3Dnew%26tab%3Dintake%26capture_mode%3Dcall%26entry%3Dnew'
    );
  });

  it('extracts the last completed trip id from a hydrated draft payload', () => {
    expect(
      extractCompletedTripIdFromDraft({
        run_snapshots: [
          { snapshot: { trip_id: 'trip_old' } },
          { snapshot: { trip_id: 'trip_latest' } },
        ],
      }),
    ).toBe('trip_latest');
  });

  it('prefers promoted trip ids over run snapshot fallbacks', () => {
    expect(
      extractCompletedTripIdFromDraft({
        promoted_trip_id: 'trip_promoted',
        run_snapshots: [{ snapshot: { trip_id: 'trip_snapshot' } }],
      }),
    ).toBe('trip_promoted');
  });
});
