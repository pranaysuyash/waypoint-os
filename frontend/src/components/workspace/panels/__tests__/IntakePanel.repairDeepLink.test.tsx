// @vitest-environment jsdom

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { IntakePanel } from '../IntakePanel';
import { useWorkbenchStore } from '@/stores/workbench';
import { useAuthStore } from '@/stores/auth';

/**
 * D-09: `?repair=<field>` deep-link into the intake repair surface. The panel
 * must auto-open the named field's editor, anchor it for scroll-into-view,
 * and move focus into its input (keyboard-reachable, visible focus ring).
 * `?field=` stays supported as a legacy alias.
 */

const mockExecuteSpineRun = vi.fn();
const mockSaveTrip = vi.fn();
const mockStartPlanning = vi.fn();

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('@/hooks/useSpineRun', () => ({
  useSpineRun: vi.fn(() => ({
    execute: mockExecuteSpineRun,
    isLoading: false,
    error: null,
    reset: vi.fn(),
  })),
}));

vi.mock('@/hooks/useTrips', () => ({
  useUpdateTrip: vi.fn(() => ({ mutate: mockSaveTrip, isSaving: false })),
  useStartPlanning: vi.fn(() => ({ mutate: mockStartPlanning, isStarting: false })),
}));

vi.mock('@/contexts/TripContext', () => ({
  useTripContext: vi.fn(() => ({ replaceTrip: vi.fn(), refetchTrip: vi.fn() })),
}));

const mockPush = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: mockPush, replace: vi.fn() })),
  useSearchParams: vi.fn(() => mockSearchParams),
}));

vi.mock('@/lib/routes', () => ({
  getTripRoute: vi.fn((id: string, stage: string) => `/trips/${id}/${stage}`),
}));

vi.mock('@/lib/api-client', async () => {
  const actual = await vi.importActual<any>('@/lib/api-client');
  return { ...actual, updateTrip: vi.fn() };
});

const tripMissingBudget = {
  id: 'trip_deep_link',
  destination: 'Paris',
  type: 'Vacation',
  party: 2,
  dateWindow: 'October 2026',
  budget: null,
  state: 'blue',
  age: '1d',
  createdAt: '2026-09-01T08:00:00.000Z',
  updatedAt: '2026-09-01T08:15:00.000Z',
} as any;

const tripComplete = {
  id: 'trip_complete',
  origin: 'Mumbai',
  destination: 'Paris',
  type: 'Vacation',
  tripPurpose: 'holiday',
  party: 2,
  dateWindow: 'October 2026',
  budget: '₹500000',
  tripPriorities: 'walkable neighborhood',
  dateFlexibility: 'firm',
  state: 'blue',
  age: '1d',
  status: 'assigned',
} as any;

describe('IntakePanel repair deep-link (?repair=)', () => {
  const mockStore = {
    input_raw_note: '',
    input_owner_note: '',
    setInputRawNote: vi.fn(),
    setInputOwnerNote: vi.fn(),
    stage: 'discovery',
    setStage: vi.fn(),
    operating_mode: 'normal_intake',
    setOperatingMode: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    Element.prototype.scrollIntoView = vi.fn();
    (useWorkbenchStore as any).mockReturnValue(mockStore);
    (useAuthStore as any).mockImplementation((selector: any) =>
      selector({ user: { id: 'agent-1', email: 'a@b.c', name: 'Agent' } }),
    );
  });

  it('auto-opens and focuses the budget editor for ?repair=budget', async () => {
    mockSearchParams = new URLSearchParams('repair=budget');

    render(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    await waitFor(() => {
      const anchor = document.querySelector<HTMLElement>('[data-intake-editor="budget"]');
      expect(anchor).not.toBeNull();
      expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
      expect(anchor!.contains(document.activeElement)).toBe(true);
    });

    // The budget editor inputs are rendered and reachable.
    expect(screen.getByPlaceholderText('Approximate budget')).toBeInTheDocument();
  });

  it('still honors the legacy ?field= alias', async () => {
    mockSearchParams = new URLSearchParams('field=priorities');

    render(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    await waitFor(() => {
      const anchor = document.querySelector<HTMLElement>('[data-intake-editor="priorities"]');
      expect(anchor).not.toBeNull();
      expect(anchor!.contains(document.activeElement)).toBe(true);
    });
  });

  it('opens the inline dates editor for a mapped machine field (?repair=date_window)', async () => {
    mockSearchParams = new URLSearchParams('repair=date_window');

    render(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    await waitFor(() => {
      const anchor = document.querySelector<HTMLElement>('[data-intake-editor="dateWindow"]');
      expect(anchor).not.toBeNull();
      expect(anchor!.contains(document.activeElement)).toBe(true);
    });
  });

  it('ignores unmapped repair fields without opening any deep-link editor', () => {
    mockSearchParams = new URLSearchParams('repair=not_a_field');

    render(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    expect(document.querySelector('[data-intake-editor="budget"]')).toBeNull();
    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
    // The panel still renders its normal review-mode action.
    expect(screen.getByRole('button', { name: /start planning/i })).toBeInTheDocument();
  });

  it('retries the focus handoff when the trip hydrates after the route mounts', async () => {
    mockSearchParams = new URLSearchParams('repair=budget');
    const { rerender } = render(<IntakePanel tripId='trip_deep_link' />);

    expect(document.querySelector('[data-intake-editor="budget"]')).toBeNull();

    rerender(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    await waitFor(() => {
      const anchor = document.querySelector<HTMLElement>('[data-intake-editor="budget"]');
      expect(anchor).not.toBeNull();
      expect(anchor!.contains(document.activeElement)).toBe(true);
    });
  });

  it('handles a second repair query without remounting the intake route', async () => {
    mockSearchParams = new URLSearchParams('repair=budget');
    const { rerender } = render(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    await waitFor(() => expect(
      document.querySelector('[data-intake-editor="budget"]')?.contains(document.activeElement),
    ).toBe(true));

    mockSearchParams = new URLSearchParams('repair=date_window');
    rerender(<IntakePanel tripId='trip_deep_link' trip={tripMissingBudget} />);

    await waitFor(() => {
      const anchor = document.querySelector<HTMLElement>('[data-intake-editor="dateWindow"]');
      expect(anchor).not.toBeNull();
      expect(anchor!.contains(document.activeElement)).toBe(true);
    });
  });

  it('keeps a valid budget repair editable even when no missing-details panel is needed', async () => {
    mockSearchParams = new URLSearchParams('repair=budget');

    render(<IntakePanel tripId='trip_complete' trip={tripComplete} />);

    await waitFor(() => {
      const anchor = document.querySelector<HTMLElement>('[data-intake-editor="budget"]');
      expect(anchor).not.toBeNull();
      expect(anchor!.contains(document.activeElement)).toBe(true);
    });
    expect(screen.getByPlaceholderText('Approximate budget')).toBeInTheDocument();
  });
});
