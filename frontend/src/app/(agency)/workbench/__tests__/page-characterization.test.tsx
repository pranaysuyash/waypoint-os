/**
 * Characterization baseline for the workbench modularization (T1–T5).
 *
 * These tests pin OBSERVABLE behavior of PageClient.tsx before any
 * structure moves (council decision 2026-09-12, seat PER-0052):
 *   T1  tab -> panel mount contract (which lazy panel each tab mounts)
 *   T2  invalid ?tab= falls back to intake
 *   T3  autosave happy path (5s debounce -> patchDraft with
 *       expected_version + is_auto_save, save_state saving -> saved)
 *   T4  autosave failure branches (409 -> conflict, other -> error,
 *       no automatic retry loop)
 *   T5  unmount cancels a pending autosave timer
 *
 * Behavior notes pinned deliberately:
 * - The arm key uses URL-derived stage/mode/scenario while the hydration
 *   init key uses store values; tests below arm the autosave via
 *   save_state='dirty' so they stay independent of that divergence.
 *   Unifying the two key builders is a BEHAVIOR commit, not a move commit.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import WorkbenchPage from '../page';

const mockReplace = vi.fn();
const mockPatchDraft = vi.hoisted(() => vi.fn());
const mockCreateDraft = vi.hoisted(() => vi.fn());
const mockGetDraft = vi.hoisted(() => vi.fn());
const mockSetSaveState = vi.fn();
const mockSetDraftMeta = vi.fn();

let mockTabsProps: {
  tabs: readonly { readonly id: string }[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
} | null = null;
let mockWorkbenchStore: Record<string, unknown>;
let mockTripData: { id: string; stage: string } | null = null;

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// Tag each lazy stub by the module it lazy-loads so a tab's panel-mount
// contract is observable without loading the real panel modules. Vitest
// resolves the loader's import to an absolute module id
// ("/src/.../PacketTab.tsx"), so match by basename.
vi.mock('next/dynamic', () => ({
  default: (loader: () => Promise<unknown>) => {
    const quoted = String(loader).match(/["']([^"'\n]+)["']/g) ?? [];
    let source = 'unknown';
    for (const candidate of quoted) {
      const inner = candidate.slice(1, -1);
      if (inner.startsWith('/') && !inner.includes(' ')) {
        source = inner.replace(/\.tsx?$/, '').split('/').pop() ?? 'unknown';
        break;
      }
    }
    return function DynamicStub() {
      return <div data-testid={`dynamic-${source}`} />;
    };
  },
}));

vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(),
  useRouter: () => ({ push: vi.fn(), replace: mockReplace, refresh: vi.fn() }),
  usePathname: () => '/workbench',
}));

vi.mock('@/components/error-boundary', () => ({
  ErrorBoundary: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('./PipelineFlow', () => ({
  PipelineFlow: () => <div data-testid='pipeline-flow' />,
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: (props: {
    tabs: readonly { readonly id: string }[];
    activeTab: string;
    onTabChange: (tabId: string) => void;
  }) => {
    mockTabsProps = props;
    return <div data-testid='tabs' />;
  },
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrip: (id: string | null) => ({
    data: id && mockTripData && mockTripData.id === id ? mockTripData : null,
    isLoading: false,
    error: null,
  }),
  useUpdateTrip: () => ({ mutate: vi.fn(), isSaving: false }),
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
  useWorkbenchStore: () => mockWorkbenchStore,
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: (selector: (state: { isLoading: boolean; isAuthenticated: boolean }) => unknown) =>
    selector({ isLoading: false, isAuthenticated: true }),
}));

vi.mock('@/lib/api-client', () => ({
  submitTripReviewAction: vi.fn(),
  createDraft: mockCreateDraft,
  getDraft: mockGetDraft,
  patchDraft: mockPatchDraft,
  discardDraft: vi.fn(),
  promoteDraft: vi.fn(),
}));

import { useSearchParams } from 'next/navigation';

function makeStore(overrides: Record<string, unknown> = {}) {
  return {
    result_safety: null,
    result_strategy: null,
    result_decision: null,
    result_packet: null,
    result_frontier: null,
    result_run_ts: null,
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
    setSaveState: mockSetSaveState,
    setDraftMeta: mockSetDraftMeta,
    setInputRawNote: vi.fn(),
    setInputOwnerNote: vi.fn(),
    resetAll: vi.fn(),
    ...overrides,
  };
}

describe('WorkbenchPage characterization (pre-modularization baseline)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTabsProps = null;
    mockTripData = null;
    mockGetDraft.mockResolvedValue(null);
    mockWorkbenchStore = makeStore();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // T1 — tab -> panel mount contract
  it('mounts the PacketTab lazy panel for tab=packet when a trip makes packet visible', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=packet&trip=trip_t1') as never);
    mockTripData = { id: 'trip_t1', stage: 'proposal' };

    render(<WorkbenchPage />);

    expect(screen.getByTestId('dynamic-PacketTab')).toBeInTheDocument();
  });

  it('mounts the SafetyTab lazy panel for tab=safety', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=safety') as never);

    render(<WorkbenchPage />);

    expect(screen.getByTestId('dynamic-SafetyTab')).toBeInTheDocument();
  });

  it('mounts the PersonaCouncilPanel lazy panel for tab=council', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=council') as never);

    render(<WorkbenchPage />);

    expect(screen.getByTestId('dynamic-PersonaCouncilPanel')).toBeInTheDocument();
  });

  // T2 — invalid tab param falls back to intake
  it('falls back to the intake tab when the tab param is not a known tab id', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=nonsense&trip=trip_t2') as never);
    mockTripData = { id: 'trip_t2', stage: 'proposal' };

    render(<WorkbenchPage />);

    expect(mockTabsProps).not.toBeNull();
    expect(mockTabsProps?.activeTab).toBe('intake');
    expect(screen.getByTestId('dynamic-IntakeTab')).toBeInTheDocument();
  });

  // T3 — autosave happy path
  it('auto-saves dirty draft content after the 5s debounce with expected_version and is_auto_save', async () => {
    vi.useFakeTimers();
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = makeStore({
      draft_id: 'draft_auto_1',
      draft_name: 'Auto One',
      draft_version: 3,
      save_state: 'dirty',
      input_raw_note: 'Hello Bali',
    });
    mockPatchDraft.mockResolvedValue({ name: 'Auto One', status: 'open', version: 4, updated_at: '2026-09-12T00:00:00Z' });

    render(<WorkbenchPage />);

    await vi.advanceTimersByTimeAsync(5000);

    expect(mockPatchDraft).toHaveBeenCalledTimes(1);
    expect(mockPatchDraft).toHaveBeenCalledWith('draft_auto_1', expect.objectContaining({
      customer_message: 'Hello Bali',
      agent_notes: null,
      structured_json: null,
      itinerary_text: null,
      stage: 'discovery',
      operating_mode: 'normal_intake',
      scenario_id: null,
      expected_version: 3,
      is_auto_save: true,
    }));
    expect(mockSetSaveState).toHaveBeenCalledWith('saving');
    expect(mockSetSaveState).toHaveBeenCalledWith('saved');
    expect(mockSetDraftMeta).toHaveBeenCalledWith(expect.objectContaining({
      draft_id: 'draft_auto_1',
      version: 4,
    }));
  });

  // T4a — version conflict maps to save_state 'conflict'
  it('marks save_state conflict when autosave hits a 409', async () => {
    vi.useFakeTimers();
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = makeStore({
      draft_id: 'draft_auto_2',
      draft_version: 7,
      save_state: 'dirty',
      input_raw_note: 'Conflict case',
    });
    mockPatchDraft.mockRejectedValue({ status: 409 });

    render(<WorkbenchPage />);

    await vi.advanceTimersByTimeAsync(5000);

    expect(mockPatchDraft).toHaveBeenCalledTimes(1);
    expect(mockSetSaveState).toHaveBeenCalledWith('saving');
    expect(mockSetSaveState).toHaveBeenCalledWith('conflict');
    expect(mockSetSaveState).not.toHaveBeenCalledWith('saved');
  });

  // T4b — generic failure maps to save_state 'error'
  it('marks save_state error when autosave fails for a non-conflict reason', async () => {
    vi.useFakeTimers();
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = makeStore({
      draft_id: 'draft_auto_3',
      draft_version: 2,
      save_state: 'dirty',
      input_raw_note: 'Error case',
    });
    mockPatchDraft.mockRejectedValue(new Error('network down'));

    render(<WorkbenchPage />);

    await vi.advanceTimersByTimeAsync(5000);

    expect(mockSetSaveState).toHaveBeenCalledWith('error');
    expect(mockSetSaveState).not.toHaveBeenCalledWith('conflict');
    expect(mockSetSaveState).not.toHaveBeenCalledWith('saved');
  });

  // T4c — failure does not update the dedupe key and does not loop retries
  it('does not automatically retry a failed autosave on subsequent ticks', async () => {
    vi.useFakeTimers();
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = makeStore({
      draft_id: 'draft_auto_4',
      draft_version: 2,
      save_state: 'dirty',
      input_raw_note: 'Retry case',
    });
    mockPatchDraft.mockRejectedValue(new Error('network down'));

    render(<WorkbenchPage />);

    await vi.advanceTimersByTimeAsync(5000);
    expect(mockPatchDraft).toHaveBeenCalledTimes(1);

    // Same content stays retryable only on the next content change / arm,
    // not via an automatic timer loop.
    await vi.advanceTimersByTimeAsync(15000);
    expect(mockPatchDraft).toHaveBeenCalledTimes(1);
  });

  // T5 — unmount cancels the pending autosave timer
  it('cancels the pending autosave when the workbench unmounts before the debounce fires', async () => {
    vi.useFakeTimers();
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);
    mockWorkbenchStore = makeStore({
      draft_id: 'draft_auto_5',
      draft_version: 1,
      save_state: 'dirty',
      input_raw_note: 'Unmount case',
    });

    const { unmount } = render(<WorkbenchPage />);

    await vi.advanceTimersByTimeAsync(4500);
    expect(mockPatchDraft).not.toHaveBeenCalled();

    unmount();
    await vi.advanceTimersByTimeAsync(5000);

    expect(mockPatchDraft).not.toHaveBeenCalled();
    expect(mockSetSaveState).not.toHaveBeenCalledWith('saving');
  });
});
