import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import WorkbenchPage from '../page';

const mockReplace = vi.fn();

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
    // PARKED (Frontier Phase 0): result_frontier kept in store but removed from UI
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

describe('WorkbenchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render the overview return link in the default workbench view', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams() as never);

    render(<WorkbenchPage />);

    expect(screen.queryByRole('link', { name: /back to overview/i })).not.toBeInTheDocument();
  });

  it('does not render Frontier OS tab (removed in Phase 0)', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=frontier') as never);

    render(<WorkbenchPage />);

    // Frontier OS text should never appear in the workbench
    expect(screen.queryByText('Frontier OS')).not.toBeInTheDocument();
  });

  it('falls back safely when an invalid tab is requested', () => {
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams('tab=frontier') as never);

    render(<WorkbenchPage />);

    // The page should still render without crashing
    expect(screen.getByText(/process inquiry/i)).toBeInTheDocument();
  });
});
