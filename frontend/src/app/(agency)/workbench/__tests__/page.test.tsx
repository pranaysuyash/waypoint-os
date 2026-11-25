import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
// T2 route unification: ../page redirects to /inquiries/new; these tests
// characterize PageClient behavior and mount it directly.
import WorkbenchPage from '../PageClient';
import { extractCompletedTripIdFromDraft } from '../PageClient';
import { transformSpineTripToTrip, normalizeSafetyResult } from '@/lib/bff-trip-adapters';
import { useWorkbenchStore } from '@/stores/workbench';

const mockReplace = vi.fn();
const mockExecuteSpineRun = vi.fn();
const mockCreateDraft = vi.hoisted(() => vi.fn());
const mockGetDraft = vi.hoisted(() => vi.fn().mockResolvedValue({
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
}));
const mockRefetchTrip = vi.fn();
const mockApiGet = vi.hoisted(() => vi.fn());
const mockRenderedPacket = vi.fn();
let mockInteractiveRun: { run_id: string; state: string; packet: unknown } | null = null;
const mockUseTrip = vi.fn((id: string | null) => ({
  data: id && mockTripData && mockTripData.id === id ? mockTripData : null,
  isLoading: false,
  error: null,
  refetch: mockRefetchTrip,
}));
let mockTabsProps: {
  tabs: readonly { readonly id: string; readonly label: string; count?: number }[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
} | null = null;
let mockWorkbenchStore: Record<string, unknown>;
let mockTripData: { id: string; stage: string; frontier_result?: Record<string, unknown> | null; safety?: Record<string, unknown> | null } | null = null;
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
    return function DynamicStub(props: { reviewPacket?: unknown }) {
      if ('reviewPacket' in props) mockRenderedPacket(props.reviewPacket);
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

vi.mock('@/components/ui/tabs', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/components/ui/tabs')>(),
  Tabs: (props: {
    tabs: readonly { readonly id: string; readonly label: string; count?: number }[];
    activeTab: string;
    onTabChange: (tabId: string) => void;
  }) => {
    mockTabsProps = props;
    return <div data-testid='tabs' />;
  },
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrip: (id: string | null) => mockUseTrip(id),
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
    runId: mockInteractiveRun?.run_id ?? null,
    state: mockInteractiveRun,
  }),
}));

vi.mock('@/stores/workbench', () => ({
  // FND-0283: PageClient now subscribes via per-field selectors — the mock
  // must apply the selector to the mock state.
  useWorkbenchStore: Object.assign(
    (sel?: (s: typeof mockWorkbenchStore) => unknown) =>
      (sel ? sel(mockWorkbenchStore) : mockWorkbenchStore),
    { setState: vi.fn() },
  ),
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
  api: { get: mockApiGet },
  submitTripReviewAction: vi.fn(),
  createDraft: mockCreateDraft,
  getDraft: mockGetDraft,
  patchDraft: vi.fn(),
  discardDraft: vi.fn(),
  promoteDraft: vi.fn(),
}));

import { useSearchParams } from 'next/navigation';

describe('WorkbenchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTabsProps = null;
    mockCreateDraft.mockReset();
    mockGetDraft.mockReset();
    mockGetDraft.mockResolvedValue({
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
    });
    mockUseTrip.mockClear();
    mockInteractiveRun = null;
    mockTripData = null;
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

  it('keeps a labelled panel for each visible workspace tab and mounts only the selected content', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    render(<WorkbenchPage />);

    for (const tab of mockTabsProps!.tabs) {
      const panel = document.getElementById(`wt-panel-${tab.id}`);
      expect(panel).toHaveAttribute('aria-labelledby', `wt-tab-${tab.id}`);
      if (tab.id !== mockTabsProps!.activeTab) {
        expect(panel).toHaveAttribute('hidden');
        expect(panel).toBeEmptyDOMElement();
      }
    }
    expect(screen.getAllByRole('tabpanel')).toHaveLength(1);
  });

  it('counts the displayed details and preserves the name of a compound inquiry', () => {
    const originalStore = mockWorkbenchStore;
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = {
      ...originalStore,
      draft_name: 'Rail group enquiry',
      result_validation: { is_valid: false },
      result_packet: {
        itinerary_feasibility_context: 'Hotel package · Cutoff unknown',
        itinerary_feasibility_question: 'When does the rate become nonrefundable?',
        itinerary_feasibility_findings: ['Rail pickup', 'Step-free access'].map(title => ({
          flag: title, message: title, details: { title, authority: 'advisory' },
        })),
      },
    };
    try {
      render(<WorkbenchPage />);
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Rail group enquiry');
      expect(screen.getByRole('button', { name: 'Review 3 itinerary details' })).toBeVisible();
    } finally {
      mockWorkbenchStore = originalStore;
    }
  });

  it.each(['safety', 'decision', 'packet'])('shows the new saved details in the header and %s after an older explicit run', (tab) => {
    const id = 'trip-reassessed-rail';
    const findings = ['Rail pickup', 'Hotel cutoff', 'Step-free boarding'].map(title => ({
      flag: title, message: title, details: { title, authority: 'advisory' },
    }));
    const oldPacket = { itinerary_feasibility_findings: findings };
    const editedPacket = { itinerary_feasibility_findings: findings.slice(1) };
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams(`trip=${id}&tab=${tab}`) as never);
    mockTripData = transformSpineTripToTrip({ id, stage: 'discovery', run_id: 'interactive', extracted: oldPacket }) as typeof mockTripData;
    mockInteractiveRun = { run_id: 'interactive', state: 'completed', packet: oldPacket };
    mockWorkbenchStore.result_packet = oldPacket;
    const page = render(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Review 3 itinerary details' })).toBeVisible();
    mockTripData = transformSpineTripToTrip({ id, stage: 'discovery', run_id: 'automatic', extracted: editedPacket }) as typeof mockTripData;
    page.rerender(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Review 2 itinerary details' })).toBeVisible();
    expect(mockRenderedPacket).toHaveBeenLastCalledWith(editedPacket);
    expect(screen.queryByRole('button', { name: 'Review 3 itinerary details' })).toBeNull();
    mockWorkbenchStore.result_packet = null;
  });

  it('falls back to intake when Frontier tab is requested without frontier visibility', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=frontier') as never);

    render(<WorkbenchPage />);

    expect(screen.getByText(/process inquiry/i)).toBeInTheDocument();
  });

  it('keeps the Frontier tab visible when the trip payload includes frontier_result', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('trip=trip_frontier_123&tab=frontier') as never);
    mockTripData = {
      id: 'trip_frontier_123',
      stage: 'booking',
      frontier_result: {
        ghost_triggered: true,
        sentiment_score: 0.83,
      },
    };

    render(<WorkbenchPage />);

    expect(mockTabsProps?.tabs.map((tab) => tab.id)).toContain('frontier');
    expect(mockTabsProps?.activeTab).toBe('frontier');
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

  it('updates the full workbench pathname when a tab changes', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);

    render(<WorkbenchPage />);

    expect(mockTabsProps).not.toBeNull();
    mockTabsProps?.onTabChange('safety');

    expect(mockReplace).toHaveBeenCalledWith('/workbench?tab=safety', { scroll: false });
  });

  it('routes blocked trips from the workbench banner to the trip repair surface', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('trip=trip_bali_blocked&tab=packet') as never);
    mockTripData = { id: 'trip_bali_blocked', stage: 'discovery' };
    mockWorkbenchStore = {
      ...mockWorkbenchStore,
      result_validation: {
        is_valid: false,
        status: 'BLOCKED',
        gate: 'NB01',
        stage: 'intake_completion',
        reasons: ['MVB_MISSING'],
      },
    };

    render(<WorkbenchPage />);

    // IMP-05 (DEMO-06): the single banner CTA opens the persisted trip editor.
    expect(screen.queryByRole('link', { name: /open trip details/i })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /review missing fields/i })).toHaveAttribute(
      'href',
      '/trips/trip_bali_blocked/intake',
    );
  });

  it('falls back to the packet-tab switch when the blocked state has no persisted trip yet', async () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=packet') as never);
    mockWorkbenchStore = {
      ...mockWorkbenchStore,
      result_validation: {
        is_valid: false,
        status: 'BLOCKED',
        gate: 'NB01',
        stage: 'intake_completion',
        reasons: ['MVB_MISSING'],
      },
    };

    render(<WorkbenchPage />);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /review missing fields/i }));

    expect(mockReplace).toHaveBeenCalledWith('/workbench?tab=packet', { scroll: false });
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

  it('rehydrates a completed draft back to the trip-backed workbench route', async () => {
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams('draft=draft_test_456&tab=intake&capture_mode=call&entry=new') as never,
    );
    mockTripData = { id: 'trip_completed_456', stage: 'discovery' };
    vi.mocked(mockCreateDraft).mockResolvedValue({
      draft_id: 'draft_test_456',
      name: 'Draft Test',
      status: 'open',
      created_at: '2026-06-22T00:00:00.000Z',
    });
    mockGetDraft.mockResolvedValue({
      draft_id: 'draft_test_456',
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
      run_snapshots: [{ snapshot: { trip_id: 'trip_completed_456' } }],
    });

    render(<WorkbenchPage />);

    await waitFor(() => {
      expect(mockUseTrip).toHaveBeenCalledWith('trip_completed_456');
      expect(mockReplace).toHaveBeenCalledWith(
        '/workbench?draft=draft_test_456&tab=packet&capture_mode=call&entry=new&trip=trip_completed_456',
        { scroll: false },
      );
    });
  });

  it('hydrates every persisted trip output through the Workbench store actions', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('trip=trip_hydrate_123') as never);
    const packet = { destination: 'Bali' };
    const validation = { is_valid: true, status: 'VALID' };
    const decision = { decision_state: 'PROCEED' };
    const strategy = { selected_option: 'direct' };
    const internalBundle = { margin: 0.2 };
    const travelerBundle = { summary: 'Ready to review' };
    const fees = { total: 125 };
    const frontier = { sentiment_score: 0.83 };
    const safety = { leaks: [] };
    mockTripData = {
      id: 'trip_hydrate_123',
      stage: 'proposal',
      packet,
      validation,
      decision,
      strategy,
      internal_bundle: internalBundle,
      traveler_bundle: travelerBundle,
      fees,
      frontier_result: frontier,
      safety,
      customerMessage: 'Traveler wants Bali',
      agentNotes: 'Keep margin >=18%',
    } as never;

    render(<WorkbenchPage />);

    expect(mockWorkbenchStore.setResultPacket).toHaveBeenCalledWith(packet);
    expect(mockWorkbenchStore.setResultValidation).toHaveBeenCalledWith(validation);
    expect(mockWorkbenchStore.setResultDecision).toHaveBeenCalledWith(decision);
    expect(mockWorkbenchStore.setResultStrategy).toHaveBeenCalledWith(strategy);
    expect(mockWorkbenchStore.setResultInternalBundle).toHaveBeenCalledWith(internalBundle);
    expect(mockWorkbenchStore.setResultTravelerBundle).toHaveBeenCalledWith(travelerBundle);
    expect(mockWorkbenchStore.setResultSafety).toHaveBeenCalledWith(normalizeSafetyResult(safety));
    expect(mockWorkbenchStore.setResultFees).toHaveBeenCalledWith(fees);
    expect(mockWorkbenchStore.setResultFrontier).toHaveBeenCalledWith(frontier);
    expect(useWorkbenchStore.setState).toHaveBeenCalledWith({
      input_raw_note: 'Traveler wants Bali',
      input_owner_note: 'Keep margin >=18%',
      save_state: 'clean',
    });
  });

  it.each(['completed', 'failed', 'interrupted'])('refreshes a reopened trip after its queued reassessment is %s', async (state) => {
    const id = 'trip-reopened';
    const runId = 'run-edit';
    const backendTrip = {
      id, stage: 'discovery', run_id: 'run-original', customerMessage: 'Our travel dates have changed.',
      safety: { leakage_passed: true }, decision: { decision_state: 'ASK_FOLLOWUP' },
      traveler_bundle: { user_message: 'When would you like to depart?' },
    };
    mockTripData = transformSpineTripToTrip({
      ...backendTrip, reassess: { queued: true, run_id: runId },
    }) as typeof mockTripData;
    mockWorkbenchStore.input_raw_note = backendTrip.customerMessage;
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams(`trip=${id}`) as never);
    mockApiGet.mockResolvedValue({ run_id: runId, state });
    const page = render(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Reassessing inquiry' })).toBeVisible();
    await waitFor(() => expect(mockRefetchTrip).toHaveBeenCalledTimes(1));
    expect(mockApiGet).toHaveBeenCalledWith(`/api/runs/${runId}`);
    mockTripData = transformSpineTripToTrip(state === 'completed' ? {
      ...backendTrip, run_id: runId, safety: {
        leakage_passed: true, draft_check: { version: 2, status: 'passed', digest_sha256: 'a'.repeat(64) },
      },
    } : backendTrip) as typeof mockTripData;
    page.rerender(<WorkbenchPage />);
    const label = state === 'completed' ? 'Draft language checked' : 'Draft check unavailable';
    expect(screen.getByRole('button', { name: label })).toBeVisible();
  });

  it('recognizes a rechecked note while preserving unrelated unsaved draft edits', () => {
    const id = 'trip-racing-autosave';
    const pass = { leakage_passed: true, draft_check: { version: 2, status: 'passed', digest_sha256: 'a'.repeat(64) } };
    const original = { id, stage: 'discovery', run_id: 'old', customerMessage: 'Original inquiry',
      safety: pass, traveler_bundle: { user_message: 'Please confirm the arrival date.' } };
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams(`trip=${id}`) as never);
    mockTripData = transformSpineTripToTrip(original) as typeof mockTripData;
    mockWorkbenchStore.input_raw_note = original.customerMessage;
    const page = render(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Draft language checked' })).toBeVisible();
    const edited = { ...original, customerMessage: 'Changed travel dates.' };
    mockWorkbenchStore.input_raw_note = edited.customerMessage;
    mockWorkbenchStore.save_state = 'dirty';
    mockTripData = transformSpineTripToTrip({
      ...edited, safety: { leakage_passed: true }, reassess: { queued: true, run_id: 'new' },
    }) as typeof mockTripData;
    page.rerender(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Reassessing inquiry' })).toBeVisible();
    mockTripData = transformSpineTripToTrip({ ...edited, run_id: 'new' }) as typeof mockTripData;
    page.rerender(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Draft language checked' })).toBeVisible();
    mockWorkbenchStore.input_itinerary_text = 'A new overnight transfer was just added.';
    page.rerender(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Draft check unavailable' })).toBeVisible();
    mockWorkbenchStore.input_itinerary_text = '';
    mockWorkbenchStore.input_raw_note = 'An even newer departure.';
    page.rerender(<WorkbenchPage />);
    expect(screen.getByRole('button', { name: 'Draft check unavailable' })).toBeVisible();
  });

  it('normalizes raw safety leaks from the hydrated trip into the workbench store', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('trip=trip_safety_123&tab=safety') as never);
    mockTripData = {
      id: 'trip_safety_123',
      stage: 'proposal',
      safety: {
        leaks: ['internal_budget'],
        traveler_bundle_leaks: ['MVB'],
        sanitized_view_leaks: ['ops-only'],
      } as never,
    };

    render(<WorkbenchPage />);

    expect((mockWorkbenchStore as { setResultSafety: ReturnType<typeof vi.fn> }).setResultSafety).toHaveBeenCalledWith(
      normalizeSafetyResult(mockTripData.safety),
    );
  });
});
