import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import IntakeTab from '../IntakeTab';
import type { Trip } from '@/lib/api-client';

const mockReplace = vi.fn();
let currentSearchParams = new URLSearchParams();

// Mutable holder so tests can drive the workbench draft state the component reads.
const mockStore = vi.hoisted(() => ({
  input_raw_note: '',
  input_owner_note: '',
  draft_status: 'open',
  pending_intake_prefill: null as string | null,
  setInputRawNote: vi.fn(),
  setInputOwnerNote: vi.fn(),
  setPendingIntakePrefill: vi.fn(),
  consumePendingIntakePrefill: vi.fn((): string | null => null),
}));

vi.mock('next/navigation', () => ({
  useSearchParams: () => currentSearchParams,
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => '/workbench',
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

const baseTrip = {
  id: 'trip-intake-tab',
  destination: 'Bali',
  type: 'family leisure',
  state: 'green',
  age: '1h',
  createdAt: '2026-08-31T00:00:00Z',
  updatedAt: '2026-08-31T00:00:00Z',
  party: 4,
  budget: '₹4L',
  dateWindow: 'Jul 2026',
} as Trip;

describe('IntakeTab', () => {
  beforeEach(() => {
    mockReplace.mockReset();
    currentSearchParams = new URLSearchParams();
    mockStore.input_raw_note = '';
    mockStore.input_owner_note = '';
    mockStore.draft_status = 'open';
    mockStore.pending_intake_prefill = null;
    mockStore.setInputRawNote.mockReset();
    mockStore.setInputRawNote.mockImplementation(() => {});
    mockStore.setInputOwnerNote.mockReset();
    mockStore.setInputOwnerNote.mockImplementation(() => {});
    mockStore.setPendingIntakePrefill.mockReset();
    mockStore.setPendingIntakePrefill.mockImplementation(() => {});
    mockStore.consumePendingIntakePrefill.mockReset();
    mockStore.consumePendingIntakePrefill.mockImplementation(() => null);
  });

  it('shows the canonical trip purpose prompt in the intake helper copy', () => {
    render(<IntakeTab trip={null} />);

    expect(screen.getByText(/What is the purpose of this trip/i)).toBeInTheDocument();
    expect(screen.getByText(/Need the purpose fast\?/i)).toBeInTheDocument();
  });

  it('updates the full workbench pathname when the stage changes', async () => {
    render(<IntakeTab trip={null} />);

    await userEvent.selectOptions(screen.getByLabelText('Stage'), 'booking');

    expect(mockReplace).toHaveBeenCalledWith('/workbench?stage=booking', { scroll: false });
  });

  // IMP-03 (DEMO-08): the captured-details empty state must reflect run state honestly.
  it('shows the captured-details empty state before any run', () => {
    render(<IntakeTab trip={null} />);

    expect(
      screen.getByText('Captured details will appear here after processing the inquiry.'),
    ).toBeInTheDocument();
  });

  it('shows an in-flight line while processing instead of the pre-run copy', () => {
    mockStore.draft_status = 'processing';
    render(<IntakeTab trip={null} />);

    expect(
      screen.getByText(/Processing the inquiry — captured details will appear here\./),
    ).toBeInTheDocument();
    expect(
      screen.queryByText('Captured details will appear here after processing the inquiry.'),
    ).not.toBeInTheDocument();
  });

  it('does not duplicate the empty-state copy after a blocked run', () => {
    mockStore.draft_status = 'blocked';
    render(<IntakeTab trip={null} />);

    expect(
      screen.queryByText('Captured details will appear here after processing the inquiry.'),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/Processing stopped before any details were captured/i),
    ).toBeInTheDocument();
  });

  it('renders the sample recall card only when no trip is captured', () => {
    const { rerender } = render(<IntakeTab trip={null} />);

    expect(screen.getByTestId('sample-data-badge')).toBeInTheDocument();

    rerender(<IntakeTab trip={baseTrip} />);

    expect(screen.queryByTestId('sample-data-badge')).not.toBeInTheDocument();
    expect(screen.getByText('Bali')).toBeInTheDocument();
  });

  // Message→intake hand-off (operator-surface tranche 2026-11-03): a channel
  // message handed over from the inbox fills the empty note exactly once.
  it('applies a pending intake prefill to the empty note on mount', () => {
    mockStore.consumePendingIntakePrefill.mockImplementationOnce(
      () => 'Family of 4 from Delhi to Bali in December, villa preferred.',
    );

    render(<IntakeTab trip={null} />);

    expect(mockStore.setInputRawNote).toHaveBeenCalledWith(
      'Family of 4 from Delhi to Bali in December, villa preferred.',
    );
  });

  it('appends a prefill beneath a labeled separator when a note already exists (no data loss)', () => {
    mockStore.input_raw_note = 'Operator draft already in progress.';
    mockStore.consumePendingIntakePrefill.mockImplementationOnce(() => 'Different message.');

    render(<IntakeTab trip={null} />);

    // Sim-pass fix (2026-11-07): consume-and-drop was silent data loss — the
    // operator's draft AND the forwarded message must both survive.
    const call = mockStore.setInputRawNote.mock.calls[0][0];
    expect(call).toContain('Operator draft already in progress.');
    expect(call).toContain('forwarded from inbox channel message');
    expect(call).toContain('Different message.');
  });

  it('renders departure board handoff banner when source=departure-board', () => {
    currentSearchParams = new URLSearchParams('source=departure-board&case=portugal&iata=PRT');

    render(<IntakeTab trip={null} />);

    expect(screen.getByTestId('intake-departure-board-handoff-banner')).toBeInTheDocument();
    expect(screen.getByText('Departure Board Handoff Applied')).toBeInTheDocument();
    expect(screen.getByText(/PORTUGAL client inquiry note ingested into Raw Notes/)).toBeInTheDocument();
    expect(screen.getByText('✈ PRT')).toBeInTheDocument();
  });

  it('extracts and projects live travel signal when raw note contains travel brief details', () => {
    mockStore.input_raw_note = 'Couple from Mumbai planning 10 days in Japan for our 20th anniversary in October, luxury ryokans, budget around $18,000, vegetarian meals.';

    render(<IntakeTab trip={null} />);

    expect(screen.getByText('Live Ingestion Signal')).toBeInTheDocument();
    expect(screen.getByText(/Real-Time Signal Extracted · Ready to Process/i)).toBeInTheDocument();
    expect(screen.getByText('Japan')).toBeInTheDocument();
    expect(screen.getByText('Mumbai')).toBeInTheDocument();
    expect(screen.getAllByText('$18,000').length).toBeGreaterThan(0);
  });
});
